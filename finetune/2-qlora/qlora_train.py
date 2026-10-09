"""Qwen'ni QLoRA bilan o'qitish: topshiriq gapidan JSON (ijrochi, muddat, muddat turi) ajratish.

Qadamlar:
  1. Model 4 bitga siqib yuklanadi (QLoRA ning "Q" qismi): 4 mlrd parametr ~3 GB xotiraga sig'adi.
  2. O'qitishdan OLDIN ikkala testda o'lchanadi (model bu vazifani hech ko'rmagan).
  3. Modelga kichik LoRA adapterlari qo'shiladi, faqat ular o'qitiladi (asosiy model muzlatilgan).
  4. Javob qismidagi xato hisoblanadi: savolni yodlash emas, javob yozishni o'rganadi.
  5. O'qitishdan KEYIN aynan shu testlarda qayta o'lchanadi.
"""
import json
import os
import random
import re
import time
import unicodedata
from pathlib import Path

import torch
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

MODEL = os.getenv("BASE_MODEL", "Qwen/Qwen3-4B-Instruct-2507")
DATA = Path(os.getenv("DATA_DIR", "data"))
OUT = Path(os.getenv("OUT_DIR", "out"))
OUT.mkdir(parents=True, exist_ok=True)
EPOCHS, BS, ACC, LR = int(os.getenv("EPOCHS", "1")), 4, 4, 2e-4
random.seed(0); torch.manual_seed(0)
LOG = open(OUT / "log.txt", "w", encoding="utf-8")
SYSTEM = "Sen rasmiy hujjatlardagi topshiriq gapidan ijrochi va muddatni ajratuvchi yordamchisan. Faqat JSON qaytar."
INSTR = ('Quyidagi topshiriq gapidan ijrochi(lar)ni va muddatni ajrat. JSON shakli: {"ijrochi": [ro\'yxat], '
         '"muddat": "gapdagi muddat iborasi yoki null", "muddat_turi": "sana | nisbiy | davriy | boshlanish | doimiy | yo\'q"}'
         "\nGap: ")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.write(s + "\n"); LOG.flush()


def load(name):
    return [json.loads(line) for line in open(DATA / name, encoding="utf-8")]


train, test_synth, test_real = load("train.jsonl"), load("test_synth.jsonl"), load("test_real.jsonl")
tok = AutoTokenizer.from_pretrained(MODEL)
tok.pad_token = tok.pad_token or tok.eos_token


def msgs(text, answer=None):
    m = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": INSTR + text}]
    return m + ([{"role": "assistant", "content": answer}] if answer is not None else [])


def target(r):
    return json.dumps({"ijrochi": r["ijrochi"], "muddat": r["muddat"], "muddat_turi": r["muddat_turi"]}, ensure_ascii=False)


APO = dict.fromkeys(map(ord, "‘’ʻʼ`´"), "'")


def norm(s):
    s = unicodedata.normalize("NFC", str(s or "")).translate(APO).lower()
    return re.sub(r"\s+", " ", s).strip(" .,;:")


@torch.inference_mode()
def evaluate(model, rows, name):
    model.eval()
    tok.padding_side = "left"
    stats = {"json": 0, "ijrochi": 0, "muddat": 0, "turi": 0, "hammasi": 0}
    examples = []
    for i in range(0, len(rows), 16):
        part = rows[i:i + 16]
        prompts = [tok.apply_chat_template(msgs(r["text"]), add_generation_prompt=True, tokenize=False) for r in part]
        enc = tok(prompts, return_tensors="pt", padding=True, add_special_tokens=False).to(model.device)
        out = model.generate(**enc, max_new_tokens=120, do_sample=False, pad_token_id=tok.pad_token_id)
        for r, o in zip(part, out):
            txt = tok.decode(o[enc["input_ids"].shape[1]:], skip_special_tokens=True).strip()
            m = re.search(r"\{.*\}", txt, re.S)
            try:
                p = json.loads(m.group(0)) if m else None
            except json.JSONDecodeError:
                p = None
            ok_json = isinstance(p, dict)
            p = p if ok_json else {}
            ex_ok = sorted(map(norm, p.get("ijrochi") or [])) == sorted(map(norm, r["ijrochi"]))
            md = p.get("muddat")
            md_ok = norm(md if md not in (None, "null", "") else "") == norm(r["muddat"] or "")
            t_ok = norm(p.get("muddat_turi")) == norm(r["muddat_turi"])
            for k, v in (("json", ok_json), ("ijrochi", ex_ok), ("muddat", md_ok), ("turi", t_ok), ("hammasi", ex_ok and md_ok and t_ok)):
                stats[k] += int(v)
            examples.append({"gap": r["text"], "kutilgan": target(r), "model": txt[:300]})
    res = {k: round(v / len(rows), 3) for k, v in stats.items()}
    log(f"  {name} ({len(rows)} ta): " + ", ".join(f"{k} {v:.0%}" for k, v in res.items()))
    return res, examples


# 1. 4 bitli yuklash
t0 = time.time()
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.bfloat16,
                         bnb_4bit_use_double_quant=True)
model = AutoModelForCausalLM.from_pretrained(MODEL, quantization_config=bnb, device_map={"": 0}, torch_dtype=torch.bfloat16)
log(f"Model: {MODEL}, 4 bitda yuklandi: {time.time() - t0:.0f} s, GPU xotira {torch.cuda.memory_allocated() / 2**30:.1f} GB")

# 2. O'qitishdan oldin
if os.getenv("SKIP_BEFORE"):                     # oldingi urinishda o'lchangan (bir xil model, bir xil so'rov)
    before_real = before_synth = None; ex_before = [{"gap": r["text"], "kutilgan": target(r), "model": ""} for r in test_real]
else:
    log("O'QITISHDAN OLDIN:")
    before_real, ex_before = evaluate(model, test_real, "haqiqiy hujjatlar")
    before_synth, _ = evaluate(model, test_synth, "sun'iy, yangi nomlar")

# 3. LoRA adapterlari
model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True,      # xotirani tejaydi
                                        gradient_checkpointing_kwargs={"use_reentrant": False})
model.config.use_cache = False
cfg = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, task_type="CAUSAL_LM",
                 target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])
model = get_peft_model(model, cfg)
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
total = sum(p.numel() for p in model.parameters())
log(f"LoRA: o'qitiladigan parametrlar {trainable:,} ({trainable / total:.2%} — 4 bitli asosiy model hisobida)")


# 4. Ma'lumotni tayyorlash: faqat javob qismi hisobga olinadi
def encode(r):
    p = tok.apply_chat_template(msgs(r["text"]), add_generation_prompt=True, tokenize=False)
    f = tok.apply_chat_template(msgs(r["text"], target(r)), tokenize=False)
    assert f.startswith(p), "chat shabloni kutilganidek emas"
    ids = tok(f, add_special_tokens=False)["input_ids"]
    n = len(tok(p, add_special_tokens=False)["input_ids"])
    return ids, [-100] * n + ids[n:]


data = [encode(r) for r in train]
log(f"O'qitish misollari: {len(data)}, o'rtacha uzunlik {sum(len(d[0]) for d in data) / len(data):.0f} token")
params = [p for p in model.parameters() if p.requires_grad]
opt = torch.optim.AdamW(params, lr=LR, weight_decay=0.0)
steps = EPOCHS * len(data) // (BS * ACC)
sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / 10) * max(0.05, 1 - s / steps))
tok.padding_side = "right"
model.train()
step, t0, losses = 0, time.time(), []
for ep in range(1, EPOCHS + 1):
    random.shuffle(data)
    for i in range(0, len(data), BS):
        batch = data[i:i + BS]
        L = max(len(x) for x, _ in batch)
        ids = torch.tensor([x + [tok.pad_token_id] * (L - len(x)) for x, _ in batch], device=model.device)
        lab = torch.tensor([y + [-100] * (L - len(y)) for _, y in batch], device=model.device)
        att = torch.tensor([[1] * len(x) + [0] * (L - len(x)) for x, _ in batch], device=model.device)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            loss = model(input_ids=ids, attention_mask=att, labels=lab).loss / ACC
        loss.backward()
        losses.append(loss.item() * ACC)
        if (i // BS + 1) % ACC == 0:
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            opt.step(); sched.step(); opt.zero_grad(); step += 1
            if step % 20 == 0:
                log(f"  epoch {ep}, qadam {step}/{steps}, loss {sum(losses[-40:]) / len(losses[-40:]):.3f}, {time.time() - t0:.0f} s")
train_min = (time.time() - t0) / 60
log(f"O'qitish tugadi: {train_min:.1f} daqiqa")

# 5. O'qitishdan keyin
model.config.use_cache = True
log("O'QITISHDAN KEYIN:")
after_real, ex_after = evaluate(model, test_real, "haqiqiy hujjatlar")
after_synth, _ = evaluate(model, test_synth, "sun'iy, yangi nomlar")
model.save_pretrained(OUT / "adapter")
size = sum(f.stat().st_size for f in (OUT / "adapter").glob("*")) / 2**20
res = {"model": MODEL, "train": len(train), "epochs": EPOCHS, "trainable": trainable, "adapter_mb": round(size, 1),
       "train_minutes": round(train_min, 1), "before": {"real": before_real, "synth": before_synth},
       "after": {"real": after_real, "synth": after_synth}}
json.dump(res, open(OUT / "natija.json", "w"), ensure_ascii=False, indent=1)
json.dump([dict(b, keyin=a["model"]) for b, a in zip(ex_before, ex_after)], open(OUT / "misollar.json", "w"),
          ensure_ascii=False, indent=1)
log("TAYYOR:", json.dumps(res, ensure_ascii=False))
