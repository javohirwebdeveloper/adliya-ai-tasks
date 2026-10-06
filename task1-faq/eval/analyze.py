"""eval/dump_scores.py saqlagan ballar bo'yicha sozlamalarni solishtirish (modelni qayta ishlatmasdan).

Savol: reranker kerakmi va qachon? Solishtiriladi:
  - faqat 1-bosqich (bge-m3 dense + sparse + lug'at);
  - har doim reranker (savol + javob matni yoki faqat savol bilan), 5 yoki 3 nomzod;
  - "kulrang zona": 1-bosqich ishonchli bo'lsa (bali yuqori va ikkinchisidan ancha oldinda) reranker
    chaqirilmaydi, aks holda chaqiriladi. Bu o'rtacha javob vaqtini kamaytiradi.
Har bir variant uchun: Hit@1, Hit@3, reranker chaqirilgan so'rovlar ulushi, o'rtacha vaqt, bazada yo'q
savollarning "ishonchli" deb o'tib ketgan ulushi.

  python -m eval.analyze
"""
import json
from pathlib import Path

HERE = Path(__file__).parent


def stage1(row):
    return sorted([c for c in row["cands"] if "raw_rank" in c], key=lambda c: c["raw_rank"])


def confident(c, conf_t, conf_m):
    return bool(c) and c[0]["raw_s1"] >= conf_t and (len(c) < 2 or c[0]["raw_s1"] - c[1]["raw_s1"] >= conf_m)


def evaluate(rows, passage, top, conf_t, conf_m, per_cand):
    pos = [r for r in rows if not r["is_neg"]]
    neg = [r for r in rows if r["is_neg"]]
    h1 = h3 = reranked = 0
    for r in pos:
        c = stage1(r)
        if passage is None or confident(c, conf_t, conf_m):
            ids = [x["answer_id"] for x in c]
        else:
            reranked += 1
            head = sorted(c[:top], key=lambda x: -x[passage])
            ids = [x["answer_id"] for x in head + c[top:]]
        h1 += bool(ids) and ids[0] in r["gold"]
        h3 += any(a in r["gold"] for a in ids[:3])
    share = reranked / len(pos)
    return {"passage": passage or "-", "top": top, "conf_t": conf_t, "conf_m": conf_m, "hit@1": round(h1 / len(pos), 4),
            "hit@3": round(h3 / len(pos), 4), "reranked": round(share, 3),
            "avg_rerank_s": round(share * per_cand.get(passage, 0) * top, 2),
            "neg_confident": round(sum(confident(stage1(r), conf_t, conf_m) for r in neg) / max(len(neg), 1), 3)}


def main():
    data = json.loads((HERE / "dev_scores.json").read_text())
    rows = data["rows"]
    ncand = sum(len(r["cands"]) for r in rows) / len(rows)
    per_cand = {p: t / data["n"] / ncand for p, t in data["timing_total_s"].items()}
    print("reranker vaqti, 1 nomzod (s):", {p: round(v, 3) for p, v in per_cand.items()})
    base = evaluate(rows, None, 0, 99, 0, per_cand)
    print("faqat 1-bosqich:", base)
    always, gray = [], []
    for passage in ("qa300", "q"):
        for top in (5, 3):
            always.append(evaluate(rows, passage, top, 99, 0, per_cand))
            for conf_t in (1.0, 0.95, 0.9, 0.85, 0.8):
                for conf_m in (0.0, 0.03, 0.05, 0.1):
                    o = evaluate(rows, passage, top, conf_t, conf_m, per_cand)
                    if o["neg_confident"] <= 0.01:
                        gray.append(o)
    for o in always:
        print("har doim reranker:", o)
    gray.sort(key=lambda o: (-o["hit@1"], o["avg_rerank_s"]))
    for o in gray[:12]:
        print("kulrang zona:", o)
    (HERE / "analyze_dev.json").write_text(json.dumps({"stage1": base, "always": always, "gray": gray[:30]}, indent=1))


if __name__ == "__main__":
    main()
