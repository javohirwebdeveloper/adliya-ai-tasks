"""1-qadam (shu serverda, yengil ish): savolga shaxsiy ma'lumot qo'shiladi, qalqon uni yashiradi, 1-topshiriq API'si
(/retrieve) bazadan 3 ta eng yaqin javobni topadi. Savollar: 1-topshiriqning ko'r to'plami (bazada bor 120 ta, bazada
yo'q 60 ta).

Server boshqa ishlar bilan band bo'lmasligi uchun so'rovlar ketma-ket, orasida pauza; server yuki LOAD_MAX dan
oshsa (12 yadrodan 8 tasi band), pasayguncha kutadi. Qidiruvning o'zi yukni ~5 ga chiqaradi. Har natija darhol
saqlanadi: to'xtab qolsa, qayta ishga tushirilganda topilganlari qayta so'ralmaydi.

    python rag/prepare.py            # -> rag/natija/inputs.json
"""
import csv
import json
import os
import random
import re
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pii-shield"))
sys.path.insert(0, str(ROOT / "rag"))
from llm.prompts import reply_lang  # noqa: E402
from pii import add_pii  # noqa: E402
from shield import Shield  # noqa: E402

API = os.getenv("FAQ_API", "http://127.0.0.1:8091")
PAUSE, LOAD_MAX = 1.0, 8.0
EVAL = ROOT / "task1-faq" / "eval"


TAG = re.compile(r"\[[A-Z_]+_\d+\]")


def retrieval_query(masked: str) -> str:
    """Sinab ko'rilgan va rad etilgan g'oya: shaxsiy ma'lumot berilgan gaplarni ("Telefonim [TELEFON_1].") qidirishdan
    oldin olib tashlash. O'lchovda yordam bermadi (natija/results.md), chunki tinish belgisiz savolda gaplar ajralmaydi.
    Shuning uchun Gemma'ga yashirilgan matnning o'zi bo'yicha topilgan manbalar beriladi."""
    parts = re.split(r"(?<=[.!?])\s+", masked.strip())
    keep = [TAG.sub("", p) for p in parts if not TAG.search(p) or p.rstrip().endswith("?")]
    q = re.sub(r"\s+([,.!?])", r"\1", re.sub(r"\s+", " ", " ".join(keep))).strip()
    return q or re.sub(r"\s+", " ", TAG.sub("", masked)).strip()


def wait_for_quiet_server():
    for _ in range(60):
        if os.getloadavg()[0] < LOAD_MAX:
            return
        time.sleep(10)
    sys.exit("server band, to'xtatildi")


def main():
    answers = {int(r["id"]): r["answer"] for r in csv.DictReader(open(ROOT / "task1-faq/data/answers.csv", encoding="utf-8"))}
    items = []
    for r in csv.DictReader(open(EVAL / "final_test_queries.csv", encoding="utf-8")):
        gold = [int(r["answer_id"])] + [int(x) for x in r["alt_answer_ids"].split(";") if x.strip()]
        items.append({"tur": "bazada", "id": int(r["id"]), "savol": r["query"], "uslub": r["style"], "gold": gold,
                      "gold_javob": answers[gold[0]]})
    for r in csv.DictReader(open(EVAL / "final_negatives.csv", encoding="utf-8")):
        items.append({"tur": "bazada_yoq", "id": int(r["id"]), "savol": r["query"], "uslub": r["kind"], "gold": [],
                      "gold_javob": ""})
    rnd, sh, client = random.Random(5), Shield(), httpx.Client(base_url=API, timeout=60)
    out = ROOT / "rag" / "natija"
    out.mkdir(exist_ok=True)
    cache_file = out / "qidiruv_kesh.jsonl"                 # yashirilgan savol -> qidiruv natijasi
    cache = {}
    if cache_file.exists():
        for line in open(cache_file, encoding="utf-8"):
            d = json.loads(line)
            cache[d["q"]] = d["r"]
    t0 = time.time()
    for n, it in enumerate(items, 1):
        it["yozuv"] = reply_lang(it["savol"])
        it["fuqaro"] = add_pii(it["savol"], it["yozuv"], rnd)
        it["masked"], it["key"] = sh.mask(it["fuqaro"])
        it["qidiruv_sorov"] = retrieval_query(it["masked"])
        for q in (it["masked"], it["qidiruv_sorov"]):
            if q not in cache:
                wait_for_quiet_server()
                r = client.post("/retrieve", json={"question": q, "k": 3})
                r.raise_for_status()
                cache[q] = r.json()
                with open(cache_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"q": q, "r": cache[q]}, ensure_ascii=False) + "\n")
                time.sleep(PAUSE)
        it["qidiruv"] = cache[it["masked"]]               # Gemma'ga shu manbalar beriladi
        it["qidiruv_tozalangan"] = cache[it["qidiruv_sorov"]]   # rad etilgan variant, solishtirish uchun
        if n % 30 == 0:
            print(f"{n}/{len(items)}  {time.time() - t0:.0f} s  server yuki {os.getloadavg()[0]:.1f}", flush=True)
    (out / "inputs.json").write_text(json.dumps(items, ensure_ascii=False, indent=1))
    print("tayyor:", len(items))


if __name__ == "__main__":
    main()
