"""LoRA bilan fine-tuning namunasi: fuqaro savolini 9 ta mavzudan biriga ajratish.

Nima qilinadi (har qadam suhbatda tushuntirish uchun):
  1. Dataset: bazadagi 3048 ta savol, har birining mavzusi uning javobidan olinadi.
  2. Ko'r test: biz alohida yozgan 325 ta real uslubdagi savol (dev 205 + final 120). O'qitishda ishlatilmaydi.
  3. Fine-tuningsiz: model muzlatilgan, faqat ustiga oddiy klassifikator o'qitiladi.
  4. LoRA: model muzlatilgan, unga kichik adapter qo'shilib, faqat adapter va klassifikator o'qitiladi.
  5. Natija: ikkalasi bir xil ko'r testda solishtiriladi.
"""
import csv
import json
import os
import random
import time
from pathlib import Path

import numpy as np
import torch
from peft import LoraConfig, get_peft_model
from sklearn.linear_model import LogisticRegression
from transformers import AutoModel, AutoModelForSequenceClassification, AutoTokenizer

MODEL = os.getenv("BASE_MODEL", "FacebookAI/xlm-roberta-base")      # BERT oilasidan, 100 tilni biladi
DATA = Path(os.getenv("DATA_DIR", Path(__file__).resolve().parents[2] / "task1-faq"))
OUT = Path(os.getenv("OUT_DIR", Path(__file__).resolve().parent / "natija"))
DEV = "cuda" if torch.cuda.is_available() else "cpu"                  # GPU bo'lsa, o'sha
OUT.mkdir(parents=True, exist_ok=True)
torch.set_num_threads(int(os.getenv("THREADS", "6")))
random.seed(0); np.random.seed(0); torch.manual_seed(0)
LOG = open(OUT / "log.txt", "a", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.write(time.strftime("%H:%M:%S ") + s + "\n"); LOG.flush()


# 1. Dataset
cat_of = {int(r["id"]): int(r["category_id"]) - 1 for r in csv.DictReader(open(DATA / "data/answers.csv", encoding="utf-8"))}
names = [r["name"] for r in csv.DictReader(open(DATA / "data/categories.csv", encoding="utf-8"))]
kb = [(r["question"], cat_of[int(r["answer_id"])]) for r in csv.DictReader(open(DATA / "data/questions.csv", encoding="utf-8"))]
random.shuffle(kb)
n_val = len(kb) // 10
val, train = kb[:n_val], kb[n_val:]
test = []
for f in ["eval/test_queries.csv", "eval/final_test_queries.csv"]:
    for r in csv.DictReader(open(DATA / f, encoding="utf-8")):
        if r.get("answer_id"):
            test.append((r["query"], cat_of[int(r["answer_id"])]))
if os.getenv("LIMIT"):                                                # tez tekshirish uchun
    k = int(os.getenv("LIMIT")); train, val, test = train[:k], val[:k // 4], test[:k // 4]
log(f"Qurilma: {DEV} {torch.cuda.get_device_name(0) if DEV == 'cuda' else ''}")
log(f"Model: {MODEL} | o'qitish: {len(train)} | tekshirish: {len(val)} | ko'r test: {len(test)} | mavzular: {len(names)}")
majority = max(range(len(names)), key=lambda c: sum(1 for _, y in train if y == c))
log(f"Eng oddiy taxmin (hammasiga eng ko'p mavzu): {np.mean([y == majority for _, y in test]):.1%}")

tok = AutoTokenizer.from_pretrained(MODEL)


def batches(rows, size):
    for i in range(0, len(rows), size):
        part = rows[i:i + size]
        enc = tok([t for t, _ in part], padding=True, truncation=True, max_length=64, return_tensors="pt").to(DEV)
        yield enc, torch.tensor([y for _, y in part]).to(DEV)


# 3. Fine-tuningsiz: muzlatilgan model + oddiy klassifikator (linear probe)
t0 = time.time()
base = AutoModel.from_pretrained(MODEL).to(DEV).eval()


@torch.inference_mode()
def embed(rows):
    out = []
    for enc, _ in batches(rows, 64):
        h = base(**enc).last_hidden_state
        m = enc["attention_mask"].unsqueeze(-1)
        out.append(((h * m).sum(1) / m.sum(1)).cpu().numpy())
    return np.concatenate(out)


clf = LogisticRegression(max_iter=2000).fit(embed(train), [y for _, y in train])
probe_acc = float(np.mean(clf.predict(embed(test)) == np.array([y for _, y in test])))
log(f"Fine-tuningsiz (muzlatilgan model + klassifikator): ko'r test {probe_acc:.1%} ({time.time() - t0:.0f} s)")
del base

# 4. LoRA
model = AutoModelForSequenceClassification.from_pretrained(MODEL, num_labels=len(names))
cfg = LoraConfig(task_type="SEQ_CLS", r=8, lora_alpha=16, lora_dropout=0.1, target_modules=["query", "key", "value"])
model = get_peft_model(model, cfg).to(DEV)
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
total = sum(p.numel() for p in model.parameters())
log(f"LoRA: o'qitiladigan parametrlar {trainable:,} / {total:,} ({trainable / total:.2%})")


@torch.inference_mode()
def accuracy(rows):
    model.eval()
    ok = 0
    for enc, y in batches(rows, 64):
        ok += (model(**enc).logits.argmax(-1) == y).sum().item()
    return ok / len(rows)


opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=3e-4, weight_decay=0.01)
EPOCHS, BS = (1 if os.getenv("LIMIT") else int(os.getenv("EPOCHS", "3"))), 32
steps_total = EPOCHS * ((len(train) + BS - 1) // BS)
sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / 20) * max(0.0, 1 - s / steps_total))
history, step, t0 = [], 0, time.time()
for ep in range(1, EPOCHS + 1):
    model.train()
    random.shuffle(train)
    losses = []
    for enc, y in batches(train, BS):
        loss = model(**enc, labels=y).loss
        loss.backward()
        opt.step(); sched.step(); opt.zero_grad()
        losses.append(loss.item()); step += 1
        if step % 20 == 0:
            log(f"  qadam {step}/{steps_total}, loss {np.mean(losses[-20:]):.3f}, {time.time() - t0:.0f} s")
    va, te = accuracy(val), accuracy(test)
    history.append({"epoch": ep, "loss": round(float(np.mean(losses)), 4), "val": round(va, 4), "test": round(te, 4)})
    log(f"Epoch {ep}: o'rtacha loss {np.mean(losses):.3f} | tekshirish {va:.1%} | ko'r test {te:.1%}")

model.save_pretrained(OUT / "adapter")
size_mb = sum(f.stat().st_size for f in (OUT / "adapter").glob("*")) / 1024 / 1024
res = {"model": MODEL, "train": len(train), "val": len(val), "test": len(test),
       "majority_test": round(float(np.mean([y == majority for _, y in test])), 4),
       "frozen_probe_test": round(probe_acc, 4), "lora_test": history[-1]["test"],
       "trainable_params": trainable, "total_params": total, "adapter_mb": round(size_mb, 1),
       "train_minutes": round((time.time() - t0) / 60, 1), "history": history}
json.dump(res, open(OUT / "natija.json", "w"), ensure_ascii=False, indent=1)
log("TAYYOR:", json.dumps(res, ensure_ascii=False))
