"""Qalqon demo sahifasining 5-qismi uchun RAG namunalari (pii-shield/rag_namunalar.json).

    python rag/namunalar.py ID1,ID2,ID3          # natija/gemma_rag.json dagi tartib raqamlari, qo'lda tanlanadi

Natijalar (results.md) hamma savol bo'yicha hisoblangan, namunalar faqat ko'rsatish uchun.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pii-shield"))
sys.path.insert(0, str(ROOT / "rag"))
from evaluate import cited_nums, nums  # noqa: E402
from shield import Shield  # noqa: E402

NOT_FOUND = "Bu savol bo'yicha bazada ma'lumot topmadim. Savolni boshqacharoq yozib ko'ring yoki mavzular ro'yxatidan qidiring."
NAMES = {"o'zbek lotin": "Lotin", "o'zbek kirill": "Кирилл", "rus tili": "Русский"}


def card(it):
    d, y = it.get("rag") or {}, it.get("yopiq") or {}
    ok = bool(d.get("javob_bor") and d.get("javob"))
    used = cited_nums(d) if ok else []
    srcs = " ".join(x["answer"] for x in it["qidiruv"]["items"])
    extra = sorted(nums(y.get("javob") or "") - nums(it["masked"] + " " + srcs + " " + it["gold_javob"]))
    if not (y.get("javob_bor") and y.get("javob")):
        y_note = ""
    elif it["tur"] == "bazada_yoq":
        y_note = "Bazada bunday javob yo'q, model o'zi bilganidan yozdi."
    else:
        b = it.get("yopiq_baho") or {}
        y_note = ("Rasmiy javobda va manbalarda yo'q raqam: " + ", ".join(extra) + ". " if extra else "") + \
                 (f"Hakam: {b.get('baho')}. {b.get('sabab', '')}" if b.get("baho") else "")
    nom = ("Bazada yo'q savol" if it["tur"] == "bazada_yoq" else NAMES.get(it["yozuv"], it["yozuv"]))
    return {"nom": nom, "fuqaro": it["fuqaro"], "yashirin": it["masked"], "javob_bor": ok, "ishlatilgan": used,
            "manbalar": [{"n": i, "savol": x["question"], "ishlatildi": i in used}
                         for i, x in enumerate(it["qidiruv"]["items"], 1)],
            "javob": d.get("javob", "") if ok else "", "fuqaroga": Shield.unmask(d["javob"], it["key"]) if ok else NOT_FOUND,
            "yopiq": y.get("javob") if y.get("javob_bor") else "Javob yo'q dedi.", "yopiq_izoh": y_note.strip()}


if __name__ == "__main__":
    items = json.load(open(ROOT / "rag/natija/gemma_rag.json", encoding="utf-8"))
    res = [card(items[int(i)]) for i in sys.argv[1].split(",")]
    dest = ROOT / "pii-shield" / "rag_namunalar.json"
    dest.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(len(res), "ta namuna ->", dest)
