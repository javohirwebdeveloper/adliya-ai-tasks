"""Demo sahifasi uchun Gemma 4 ning haqiqiy javoblaridan namunalar: har yozuvdan bittadan (lotin, kirill, rus).

    python llm/namunalar.py llm/natija/gemma_items_v3.json                # avtomatik tanlov
    python llm/namunalar.py llm/natija/gemma_items_v3.json 48,78,33       # sahifadagi namunalar (qo'lda tanlangan)

Tanlov: mavzu to'g'ri topilgan, matnda kamida 3 ta yashirilgan ma'lumot bor, javob loyihasida belgi ishlatilgan va
javob fuqaro yozgan tilda.
Qo'lda tanlov: til xatosi va o'zidan to'qilgan talab yoki idora nomi bo'lmagan javoblar. Natijalar (README) esa
hamma murojaat bo'yicha hisoblangan, faqat tanlanganlari bo'yicha emas.
Matnlardagi shaxsiy ma'lumotlar Gemma to'qib chiqargan, haqiqiy odamga tegishli emas.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from llm.prompts import reply_lang  # noqa: E402
from shield import Shield  # noqa: E402

TAG = re.compile(r"\[[A-Z_]+_\d+\]")


def card(it):
    j = it.get("javob_yashirin") or {}
    reply = str(j.get("javob_loyihasi") or "")
    return {"yozuv": it["yozuv"], "asl": it["matn"], "yashirin": it["masked"], "mavzu": j.get("mavzu", ""),
            "shoshilinch": bool(j.get("shoshilinch")), "xulosa": j.get("xulosa", ""),
            "javob": reply, "fuqaroga": Shield.unmask(reply, it["key"]), "key": it["key"]}


def pick(items):
    sh, out = Shield(), []
    for script in ("o'zbek lotin", "o'zbek kirill", "rus tili"):
        cands = []
        for it in items:
            j = it.get("javob_yashirin") or {}
            reply = str(j.get("javob_loyihasi") or "")
            if (it["yozuv"] != script or j.get("mavzu") != it["mavzu"] or not TAG.search(reply)
                    or reply_lang(reply) != script                  # javob fuqaro tilida
                    or sh.mask(it["matn"])[0] != it["masked"]       # hozirgi qalqon ham aynan shunday yashiradi
                    or re.search(r"(?i)bekbek|бекбек", it["matn"])):  # Gemma to'qigan buzuq ismlar emas
                continue
            n = len(it["key"])
            if n >= 3 and len(it["matn"]) < 700:
                cands.append((-n, len(it["matn"]), it, j, reply))
        if cands:
            out.append(card(sorted(cands, key=lambda c: c[:2])[0][2]))
    return out


if __name__ == "__main__":
    items = json.load(open(sys.argv[1], encoding="utf-8"))
    res = [card(items[int(i)]) for i in sys.argv[2].split(",")] if len(sys.argv) > 2 else pick(items)
    dest = Path(__file__).resolve().parent.parent / "namunalar.json"
    dest.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(len(res), "ta namuna ->", dest)
