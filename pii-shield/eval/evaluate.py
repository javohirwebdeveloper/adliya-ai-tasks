"""Qalqon sifatini o'lchash.

    python -m eval.evaluate                 # qo'lda yozilgan sinov matnlari (data/real_test.txt)
    python -m eval.evaluate --show          # sizib chiqqan va ortiqcha yashirilganlarni ham ko'rsatadi

Uchta o'lchov:
  yashirildi   har bir haqiqiy shaxsiy ma'lumotning 90% dan ko'p belgisi biror yorliq bilan yopildimi (turi muhim emas).
               Maxfiylik uchun asosiysi shu: ism "manzil" deb yashirilsa ham, sizib chiqmagan.
  aniq topildi chegarasi va turi to'g'ri topilganlari (qat'iy o'lchov).
  ortiqcha     shaxsiy bo'lmagan narsa yashirilgan holatlar (AI uchun foydali ma'lumot yo'qolishi).
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shield import Shield  # noqa: E402

TAG = re.compile(r"\{([A-Z_]+)\|([^}]+)\}")


def load(path):
    rows = []
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip() or line.startswith("#"):
            continue
        text, gold, pos = "", [], 0
        for m in TAG.finditer(line):
            text += line[pos:m.start()]
            gold.append((m.group(1), len(text), len(text) + len(m.group(2))))
            text += m.group(2)
            pos = m.end()
        text += line[pos:]
        rows.append((text, gold))
    return rows


def evaluate(shield, rows, show=False):
    st = Counter()
    per = Counter()
    misses, extras = [], []
    for text, gold in rows:
        pred = shield.detect(text)
        covered = [False] * len(text)
        for _, s, e in pred:
            for i in range(s, e):
                covered[i] = True
        for kind, s, e in gold:
            per[kind, "jami"] += 1
            hidden = sum(covered[s:e]) / max(1, e - s) >= 0.9
            exact = (kind, s, e) in pred
            per[kind, "yashirildi"] += hidden
            per[kind, "aniq"] += exact
            st["jami"] += 1; st["yashirildi"] += hidden; st["aniq"] += exact
            if not hidden:
                misses.append((kind, text[s:e], text[:80]))
        for kind, s, e in pred:
            st["topilgan"] += 1
            if not any(s < ge and gs < e for _, gs, ge in gold):
                st["ortiqcha"] += 1
                extras.append((kind, text[s:e]))
    res = {"matnlar": len(rows), "shaxsiy_ma'lumot": st["jami"],
           "yashirildi": round(st["yashirildi"] / st["jami"], 3), "aniq_topildi": round(st["aniq"] / st["jami"], 3),
           "ortiqcha": st["ortiqcha"], "turlar": {k: f"{per[k, 'yashirildi']}/{per[k, 'jami']}"
                                                 for k in sorted({k for k, _ in per})}}
    if show:
        for m in misses:
            print("  SIZIB CHIQDI:", m)
        for x in extras:
            print("  ORTIQCHA:", x)
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(Path(__file__).resolve().parent.parent / "data" / "real_test.txt"))
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()
    print(json.dumps(evaluate(Shield(), load(a.data), a.show), ensure_ascii=False, indent=1))
