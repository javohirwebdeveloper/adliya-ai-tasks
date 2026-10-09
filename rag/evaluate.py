"""RAG natijasi: bir xil savollarda RAG bilan va RAG'siz Gemma solishtiriladi.

    python rag/evaluate.py            # natija/gemma_rag.json -> natija/results.md

O'lchovlar:
  qidirish        shaxsiy ma'lumot qo'shilib yashirilgan savolda to'g'ri javob 1-o'rinda / 3 talikda (toza savoldagi
                  natija 1-topshiriqda o'lchangan: 87,5% / 91,7%)
  hakam bahosi    javob rasmiy javobga mosmi (hakam ham Gemma: to'g'ri / qisman / noto'g'ri)
  tasdiqsiz raqam javobdagi summa, muddat kabi raqam model ko'rgan manbalarda (RAG) yoki rasmiy javob va o'sha
                  manbalarda (RAG'siz) yo'q
  rad etish       bazada yo'q savolga "javob yo'q" deyildimi
  manba           RAG javobi to'g'ri manbaga havola qildimi
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pii-shield"))
from llm.prompts import reply_lang  # noqa: E402

NAT = ROOT / "rag" / "natija"
TAG = re.compile(r"\[[A-Z_]+_\d+\]")


def nums(s: str) -> set[str]:
    """Ikki va undan ko'p xonali raqamlar, ichidagi bo'sh joysiz: "366 680" -> "366680"."""
    s = TAG.sub(" ", s or "")
    return {d for d in (re.sub(r"\D", "", m) for m in re.findall(r"\d(?:[\d  ]*\d)?", s)) if len(d) >= 2}


def cited_nums(d) -> list[int]:
    """Gemma manba raqamini son yoki matn ("1", "[2]") qilib qaytarishi mumkin."""
    out = []
    for k in d.get("manbalar") or []:
        m = re.search(r"\d+", str(k))
        if m:
            out.append(int(m.group(0)))
    return out


def pct(a, b):
    return f"{a / b:.1%}" if b else "-"


def main():
    items = json.load(open(NAT / "gemma_rag.json", encoding="utf-8"))
    real = [it for it in items if it["tur"] == "bazada"]
    neg = [it for it in items if it["tur"] == "bazada_yoq"]
    st = Counter()
    for it in real:
        for key in ("qidiruv", "qidiruv_tozalangan", "qidiruv_qayta"):
            if key not in it:
                continue
            ids = [x["answer_id"] for x in it[key]["items"]]
            st[key, 1] += bool(ids) and ids[0] in it["gold"]
            st[key, 3] += any(i in it["gold"] for i in ids[:3])
    rows = {}
    for mode in ("yopiq", "rag"):
        c = Counter()
        for it in real:
            d = it.get(mode) or {}
            ans = str(d.get("javob") or "")
            if not (d.get("javob_bor") and ans):
                c["rad"] += 1
                continue
            c["javob"] += 1
            c[(it.get(mode + "_baho") or {}).get("baho", "?")] += 1
            # RAG: faqat o'zi ko'rgan manbalar. RAG'siz: rasmiy javob va o'sha 3 manba (unga nisbatan yumshoqroq)
            srcs = " ".join(x["answer"] for x in it["qidiruv"]["items"])
            src = it["masked"] + " " + srcs + ("" if mode == "rag" else " " + it["gold_javob"])
            c["tasdiqsiz"] += bool(nums(ans) - nums(src))
            c["til"] += reply_lang(ans) == it["yozuv"]
            c["toqilgan_belgi"] += bool(set(TAG.findall(ans)) - set(it["key"]))
            if mode == "rag":
                ids = [x["answer_id"] for x in it["qidiruv"]["items"]]
                cited = [ids[k - 1] for k in cited_nums(d) if 0 < k <= len(ids)]
                c["manba_togri"] += any(i in it["gold"] for i in cited)
                c["kontekstda_bor"] += any(i in it["gold"] for i in ids)
            elif mode == "rag":
                pass
        if mode == "rag":
            for it in real:
                d = it.get("rag") or {}
                if not (d.get("javob_bor") and d.get("javob")):
                    c["rad_kontekstda_bor"] += any(x["answer_id"] in it["gold"] for x in it["qidiruv"]["items"])
        for it in neg:
            d = it.get(mode) or {}
            c["neg_rad"] += not (d.get("javob_bor") and d.get("javob"))
        rows[mode] = c
    n, m = len(real), len(neg)
    L = ["# RAG: 1-topshiriq bazasi + qalqon + Gemma 4", "",
         f"Savollar: 1-topshiriqning ko'r to'plami, bazada bor {n} ta va bazada yo'q {m} ta. Har savolga to'qima ism, "
         "pasport, telefon qo'shilgan; Gemma faqat qalqondan o'tgan matnni ko'rgan.", "",
         "**Qidirish** (to'g'ri javob 1-o'rinda / 3 talikda):", "",
         "| So'rov | 1-o'rin | 3 talik |", "|---|---|---|",
         "| Toza savol (1-topshiriqdagi o'lchov) | 87.5% | 91.7% |",
         f"| Shaxsiy ma'lumotli savol, yashirilgan matnning o'zi (Gemma'ga shu manbalar berildi) | "
         f"{pct(st['qidiruv', 1], n)} | {pct(st['qidiruv', 3], n)} |",
         f"| Shaxsiy ma'lumot berilgan gaplar oddiy qoida bilan olib tashlangan (rad etildi) | "
         f"{pct(st['qidiruv_tozalangan', 1], n)} | {pct(st['qidiruv_tozalangan', 3], n)} |"]
    if st["qidiruv_qayta", 1] or st["qidiruv_qayta", 3]:
        L.append(f"| Gemma qayta yozgan qidiruv savoli | {pct(st['qidiruv_qayta', 1], n)} | {pct(st['qidiruv_qayta', 3], n)} |")
    L += ["",
         "| | RAG'siz Gemma | RAG bilan |", "|---|---|---|"]
    y, r = rows["yopiq"], rows["rag"]
    for name, key, base in [("Bazada bor savolga javob berdi", "javob", n),
                            ("Hakam: to'g'ri", "to'g'ri", n), ("Hakam: qisman", "qisman", n),
                            ("Hakam: noto'g'ri", "noto'g'ri", n)]:
        L.append(f"| {name} | {pct(y[key], base)} | {pct(r[key], base)} |")
    L.append(f"| Bazada yo'q savolga \"javob yo'q\" dedi | {pct(y['neg_rad'], m)} | {pct(r['neg_rad'], m)} |")
    L.append(f"| Javob fuqaro tilida | {pct(y['til'], y['javob'])} | {pct(r['til'], r['javob'])} |")
    L.append(f"| O'zidan belgi ([ISM_2] kabi) to'qidi | {y['toqilgan_belgi']} | {r['toqilgan_belgi']} |")
    L += ["", f"RAG javoblarining {pct(r['manba_togri'], r['javob'])} i to'g'ri manbaga havola qilgan "
          f"(to'g'ri javob manbalar orasida bo'lgan holatlarning {pct(r['manba_togri'], r['kontekstda_bor'])} i).",
          f"RAG bazada bor {r['rad']} ta savolga \"javob yo'q\" dedi: ulardan {r['rad_kontekstda_bor']} tasida to'g'ri "
          "javob topilgan 3 manba orasida bor edi (ortiqcha ehtiyotkorlik), qolganlarida qidiruv uni topmagan.",
          f"Javobdagi summa, muddat kabi raqam manbada yo'q holatlar: RAG'siz {y['tasdiqsiz']}, RAG bilan {r['tasdiqsiz']}. "
          "RAG'siz Gemma raqam aytishdan qochgan, lekin idora va tartibni to'qigan (hakam bahosi shuni ushlaydi).",
          "Hakam bahosi va \"to'g'ri\" ulushlari bazada bor hamma savolga nisbatan (rad etilganlar ham maxrajda)."]
    text = "\n".join(L) + "\n"
    (NAT / "results.md").write_text(text)
    print(text)
    return rows, st


if __name__ == "__main__":
    main()
