"""Dev to'plamida har bir so'rov uchun nomzodlar va ularning ballarini saqlaydi: 1-bosqich (xom va tozalangan
indeks) va reranker (turli matn uzunligida). Keyin eval/analyze.py ularni modelni qayta ishlatmasdan solishtiradi.

  python -m eval.dump_scores
"""
import json
import time

from qdrant_client import QdrantClient

from app.config import settings
from app.embedder import Embedder
from app.normalize import clean_kb_question, load_synonyms
from app.rerank import Reranker
from app.search import UZ_CYRILLIC, Searcher, score_hits
from eval.evaluate import AW, HERE, PROD as RAW, SW, read_csv, retrieve_all  # noqa: E402

PASSAGES = {"qa300": 300, "q": 0}


def main():
    client = QdrantClient(url=settings.qdrant_url)
    emb, rr = Embedder(), Reranker()
    syn = load_synonyms(settings.synonyms_path)
    real, negs = read_csv(HERE / "test_queries.csv"), read_csv(HERE / "negatives.csv")
    queries = [r["query"] for r in real] + [r["query"] for r in negs]
    kb = Searcher(client, emb, settings.collection, None).kb

    stage = {}
    for name, coll in (("raw", RAW),):
        runs = retrieve_all(client, emb, queries, coll, syn)
        stage[name] = [(vs, score_hits(h, s, SW, AW)[:5]) for vs, h, s in runs]

    out = []
    timing = {p: 0.0 for p in PASSAGES}
    for i, q in enumerate(queries):
        vs = stage["raw"][i][0]
        rq = vs[-1] if len(vs) > 1 and UZ_CYRILLIC.search(vs[0]) else vs[0]
        cand = {}
        for name in ("raw",):
            for rank, c in enumerate(stage[name][i][1], start=1):
                d = cand.setdefault(c.answer_id, {"answer_id": c.answer_id, "q": c.matched_text if c.kind == "question" else kb[c.answer_id]["question"]})
                d[f"{name}_s1"], d[f"{name}_rank"] = round(c.score, 5), rank
        ids = list(cand)
        for p, n in PASSAGES.items():
            texts = [clean_kb_question(cand[a]["q"]) + (f"\n{kb[a]['answer'][:n]}" if n else "") for a in ids]
            t0 = time.time()
            for a, sc in zip(ids, rr.score(rq, texts)):
                cand[a][p] = round(sc, 6)
            timing[p] += time.time() - t0
        out.append({"query": q, "is_neg": i >= len(real), "cands": list(cand.values()),
                    "gold": [] if i >= len(real) else [int(real[i]["answer_id"])] + [int(x) for x in real[i]["alt_answer_ids"].split(";") if x.strip()],
                    "style": "" if i >= len(real) else real[i]["style"]})
        if i % 25 == 0:
            print(i, {p: round(t / (i + 1), 2) for p, t in timing.items()}, flush=True)
    (HERE / "dev_scores.json").write_text(json.dumps({"rows": out, "timing_total_s": timing, "n": len(queries)}, ensure_ascii=False))
    print("tayyor", {p: round(t / len(queries), 2) for p, t in timing.items()})


if __name__ == "__main__":
    main()
