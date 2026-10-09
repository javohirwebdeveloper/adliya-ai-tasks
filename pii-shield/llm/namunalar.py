"""Demo sahifasi uchun Gemma 4 ning haqiqiy javoblaridan namunalar: har yozuvdan bittadan (lotin, kirill, rus).

    python llm/namunalar.py llm/natija/gemma_items_v2.json      # -> namunalar.json (app.py yonida)

Tanlov: mavzu to'g'ri topilgan, matnda kamida 3 ta yashirilgan ma'lumot bor va javob loyihasida belgi ishlatilgan.
Matnlardagi shaxsiy ma'lumotlar Gemma to'qib chiqargan, haqiqiy odamga tegishli emas.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shield import Shield  # noqa: E402

TAG = re.compile(r"\[[A-Z_]+_\d+\]")


def pick(items):
    out = []
    for script in ("o'zbek lotin", "o'zbek kirill", "rus tili"):
        cands = []
        for it in items:
            j = it.get("javob_yashirin") or {}
            reply = str(j.get("javob_loyihasi") or "")
            if it["yozuv"] != script or j.get("mavzu") != it["mavzu"] or not TAG.search(reply):
                continue
            n = len(it["key"])
            if n >= 3 and len(it["matn"]) < 700:
                cands.append((-n, len(it["matn"]), it, j, reply))
        if cands:
            _, _, it, j, reply = sorted(cands, key=lambda c: c[:2])[0]
            out.append({"yozuv": script, "asl": it["matn"], "yashirin": it["masked"], "mavzu": j["mavzu"],
                        "shoshilinch": bool(j.get("shoshilinch")), "xulosa": j.get("xulosa", ""),
                        "javob": reply, "fuqaroga": Shield.unmask(reply, it["key"])})
    return out


if __name__ == "__main__":
    items = json.load(open(sys.argv[1], encoding="utf-8"))
    res = pick(items)
    dest = Path(__file__).resolve().parent.parent / "namunalar.json"
    dest.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(len(res), "ta namuna ->", dest)
