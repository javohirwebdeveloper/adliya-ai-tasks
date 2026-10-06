"""Qidiruv sifatini o'lchash.

To'plamlar:
  dev     eval/test_queries.csv (205) + eval/negatives.csv (100). Xatolar shu yerda tahlil qilindi,
          chegaralar ham shu yerda tanlanadi. Natija: eval/results_dev.md, eval/thresholds.json
  final   eval/final_test_queries.csv (120) + eval/final_negatives.csv (60). Tizim sozlab bo'lingach,
          alohida yozilgan "ko'r" to'plam. Faqat bir marta, dev da tanlangan chegaralar bilan o'lchanadi.
          Natija: eval/results_final.md
  holdout har bir javobning bitta savoli indeksdan olib tashlanib, so'rov sifatida beriladi (faqat dev).

1-bosqich qadamma-qadam o'lchanadi (dense, + sparse, + so'zlashuv lug'ati). Yakuniy tizim esa aynan
ishlab turgan kod bilan (app.search.Searcher) tekshiriladi: kulrang zona, reranker, qisqa savol qoidasi,
salom-rahmat, hammasi bilan. Metrikalar: Hit@1, Hit@3, MRR, foydalanuvchi ko'radigan natija, tezlik.

  python -m eval.evaluate --set dev
  python -m eval.evaluate --set final
"""
import argparse
import csv
import json
import os
import random
import statistics
import time
from collections import defaultdict
from pathlib import Path

from qdrant_client import QdrantClient, models

from app.config import settings
from app.embedder import Embedder
from app.normalize import load_synonyms, query_variants
from app.rerank import Reranker
from app.search import Searcher, final_status, score_hits

HERE = Path(__file__).parent
DATA = HERE.parent / "data"
PROD = settings.collection                                           # ishlatiladigan indeks (savollar bazadagidek)
CLEAN = os.getenv("EVAL_CLEAN_COLLECTION", "faq_clean")              # tajriba: qolip so'zlari tozalangan indeks
SETS = {"dev": ("test_queries.csv", "negatives.csv"), "final": ("final_test_queries.csv", "final_negatives.csv")}
SW = settings.sparse_weight
AW = settings.answer_weight


def read_csv(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def copy_without(client, src, dst, held_ids):
    if client.collection_exists(dst):
        client.delete_collection(dst)
    client.create_collection(dst, vectors_config={"dense": models.VectorParams(size=1024, distance=models.Distance.COSINE)},
                             sparse_vectors_config={"sparse": models.SparseVectorParams()})
    offset = None
    while True:
        pts, offset = client.scroll(src, limit=256, offset=offset, with_payload=True, with_vectors=["dense", "sparse"])
        keep = [models.PointStruct(id=p.id, vector=p.vector, payload=p.payload) for p in pts
                if not (p.payload["kind"] == "question" and p.payload["item_id"] in held_ids)]
        if keep:
            client.upsert(dst, points=keep, wait=True)
        if offset is None:
            break


def retrieve_all(client, embedder, queries, collection, synonyms=None):
    """Har bir so'rov uchun: (variantlar, variantlar bo'yicha hitlar, sparse vektorlar)."""
    variants = [query_variants(q, synonyms) for q in queries]
    flat = [v for vs in variants for v in vs]
    dense, sparse = embedder.encode(flat, batch_size=32, max_length=128)
    out, k = [], 0
    for vs in variants:
        hits, sps = [], []
        for _ in vs:
            hits.append(client.query_points(collection, query=dense[k].tolist(), using="dense", limit=40,
                                            with_payload=True, with_vectors=["sparse"]).points)
            sps.append(sparse[k])
            k += 1
        out.append((vs, hits, sps))
    return out


def rank_of(cands, gold):
    for i, c in enumerate(cands, start=1):
        if c.answer_id in gold:
            return i
    return None


def metrics(ranks):
    n = len(ranks)
    return {"n": n, "hit@1": sum(r == 1 for r in ranks) / n, "hit@3": sum(r is not None and r <= 3 for r in ranks) / n,
            "mrr": sum(1 / r for r in ranks if r) / n}


def grid():
    return sorted(set([i / 1000 for i in range(1, 50)] + [i / 100 for i in range(5, 100)]))


def calibrate(pos, neg):
    """pos: [(top_ball, to'g'rimi)], neg: [top_ball]. Javob chegarasi: berilgan javoblarning >= 95% i to'g'ri
    va bazada yo'q savollarning <= 3% i javob oladi. Variant chegarasi: negativlarning <= 20% i variant ko'radi."""
    rows = []
    for t in grid():
        ans = [ok for s, ok in pos if s >= t]
        rows.append({"t": t, "precision": (sum(ans) / len(ans)) if ans else 1.0,
                     "answered_ok": sum(ans) / max(len(pos), 1), "neg_above": sum(s >= t for s in neg) / max(len(neg), 1)})
    t_ans = next((r["t"] for r in rows if r["precision"] >= 0.95 and r["neg_above"] <= 0.03), rows[-1]["t"])
    t_sug = min(next((r["t"] for r in rows if r["neg_above"] <= 0.20), t_ans), t_ans)
    return t_ans, t_sug, rows


def run_system(searcher, queries):
    """Ishlab turgan qidiruv kodini (kesh siz) har bir so'rovga qo'llaydi."""
    out = []
    for q in queries:
        searcher._cache = {}
        t = time.perf_counter()
        res = searcher._search(q, top_k=5)
        res["ms"] = (time.perf_counter() - t) * 1000
        out.append(res)
    return out


def outcome(q, res, gold, t_ans, t_sug, reranker_on):
    """Foydalanuvchi nimani ko'radi (berilgan chegaralar bilan qayta hisoblanadi)."""
    if res["status"] == "smalltalk":
        return "smalltalk"
    cands = res["candidates"]
    if not cands:
        return "not_found"
    confident = reranker_on and not res.get("reranked")
    t_a, t_s = (t_ans, t_sug) if res.get("reranked") else (settings.t_answer, settings.t_suggest)
    status, _ = final_status(q, cands, confident, t_a, t_s)
    if status == "not_found":
        return "not_found"
    if status == "answered":
        return "answered_ok" if gold and cands[0].answer_id in gold else "answered_wrong"
    return "unsure_ok" if gold and any(x.answer_id in gold for x in cands[:3]) else "unsure_wrong"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", choices=SETS, default="dev")
    args = ap.parse_args()
    random.seed(42)

    client = QdrantClient(url=settings.qdrant_url)
    embedder = Embedder()
    synonyms = load_synonyms(settings.synonyms_path)
    reranker = Reranker() if settings.rerank else None
    searcher = Searcher(client, embedder, PROD, reranker)

    qfile, nfile = SETS[args.set]
    real, negs = read_csv(HERE / qfile), read_csv(HERE / nfile)
    rq, nq = [r["query"] for r in real], [r["query"] for r in negs]
    gold = [{int(r["answer_id"])} | {int(x) for x in r["alt_answer_ids"].split(";") if x.strip()} for r in real]
    first_q = {}
    for q in read_csv(DATA / "questions.csv"):
        first_q.setdefault(int(q["answer_id"]), q["question"])
    rep = {"set": args.set, "n_real": len(rq), "n_neg": len(nq), "steps": [], "styles": {}, "errors": [],
           "config": {"rerank": bool(reranker), "gray_t": settings.gray_t, "gray_m": settings.gray_m,
                      "rerank_top": settings.rerank_top, "rerank_chars": settings.rerank_chars}}

    # --- 1-bosqich: qadamma-qadam ---
    runs = {"prod": retrieve_all(client, embedder, rq, PROD), "prod+syn": retrieve_all(client, embedder, rq, PROD, synonyms)}
    steps = [("Dense qidiruv (bge-m3)", "prod", 0.0), ("+ sparse (leksik) og'irliklar", "prod", SW),
             ("+ so'zlashuv so'zlari lug'ati (prava, propiska, ZAGS ...)", "prod+syn", SW)]
    if client.collection_exists(CLEAN):
        runs["clean+syn"] = retrieve_all(client, embedder, rq, CLEAN, synonyms)
        steps.append(("(sinov, rad etildi) lug'at + qolip so'zlari tozalangan indeks", "clean+syn", SW))
    for name, run, sw in steps:
        cands = [score_hits(h, s, sw, AW) for _, h, s in runs[run]]
        rep["steps"].append({"name": name, **metrics([rank_of(c, g) for c, g in zip(cands, gold)])})
        print(rep["steps"][-1], flush=True)

    # --- yakuniy tizim (ishlab turgan kod bilan) ---
    real_res, neg_res = run_system(searcher, rq), run_system(searcher, nq)
    share = sum(1 for r in real_res + neg_res if r.get("reranked")) / len(real_res + neg_res)
    label = "Yakuniy tizim" + (f" (reranker so'rovlarning {round(100 * share)}% ida ishladi)" if reranker else " (reranker'siz)")
    rep["steps"].append({"name": label, **metrics([rank_of(r["candidates"], g) for r, g in zip(real_res, gold)])})
    rep["rerank_share"] = round(share, 3)
    print(rep["steps"][-1], flush=True)

    by_style = defaultdict(list)
    for r, res, g in zip(real, real_res, gold):
        by_style[r["style"]].append(rank_of(res["candidates"], g))
    rep["styles"] = {k: metrics(v) for k, v in sorted(by_style.items())}

    # --- chegaralar (reranker bali bo'yicha, faqat reranker ishlagan so'rovlar) ---
    thr_path = HERE / "thresholds.json"
    key = "rerank" if reranker else "stage1"            # reranker bali yoki 1-bosqich bali
    saved_all = json.loads(thr_path.read_text()) if thr_path.exists() else {}
    if args.set == "dev":
        use = [(r, g) for r, g in zip(real_res, gold) if r["candidates"] and bool(r.get("reranked")) == bool(reranker)]
        pos = [(r["candidates"][0].score, r["candidates"][0].answer_id in g) for r, g in use]
        neg = [r["candidates"][0].score for r in neg_res if r["candidates"] and bool(r.get("reranked")) == bool(reranker)]
        t_ans, t_sug, rows = calibrate(pos, neg)
        saved_all[key] = {"answer": t_ans, "suggest": t_sug}
        thr_path.write_text(json.dumps(saved_all, indent=1))
        rep["threshold_table"] = [r for r in rows if r["t"] in (0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)
                                  or r["t"] in (t_ans, t_sug)]
    else:
        t_ans, t_sug = saved_all[key]["answer"], saved_all[key]["suggest"]
    if not reranker:
        settings.t_answer, settings.t_suggest = t_ans, t_sug
    rep["thresholds"] = {"answer": t_ans, "suggest": t_sug, "scale": key}

    out_r, out_n = defaultdict(int), defaultdict(int)
    for q, res, g in zip(rq, real_res, gold):
        out_r[outcome(q, res, g, t_ans, t_sug, bool(reranker))] += 1
    for q, res in zip(nq, neg_res):
        out_n[outcome(q, res, None, t_ans, t_sug, bool(reranker))] += 1
    rep["final"] = {"real": dict(out_r), "negatives": dict(out_n)}

    for r, res, g in zip(real, real_res, gold):
        c = res["candidates"]
        if not c or c[0].answer_id not in g:
            rep["errors"].append({"query": r["query"], "style": r["style"], "gold": f"{r['answer_id']}: {first_q[int(r['answer_id'])]}",
                                  "pred": f"{c[0].answer_id}: {first_q.get(c[0].answer_id, '')}" if c else "-",
                                  "rank": rank_of(c, g)})
    rep["neg_errors"] = [{"query": q, "pred": first_q.get(res["candidates"][0].answer_id, "")}
                         for q, res in zip(nq, neg_res) if outcome(q, res, None, t_ans, t_sug, bool(reranker)) == "answered_wrong"]

    times = [r["ms"] for r in real_res + neg_res if r["status"] != "smalltalk"]
    rep["latency_ms"] = {"median": round(statistics.median(times)), "p90": round(sorted(times)[int(0.9 * len(times)) - 1]),
                         "mean": round(statistics.mean(times))}

    if args.set == "dev":                                    # holdout: bazadagi savolning o'zi (1-bosqich)
        by_answer = defaultdict(list)
        for q in read_csv(DATA / "questions.csv"):
            by_answer[int(q["answer_id"])].append(q)
        held = [random.choice(qs) for _, qs in sorted(by_answer.items())]
        copy_without(client, PROD, PROD + "_holdout", {int(q["id"]) for q in held})
        hr = retrieve_all(client, embedder, [q["question"] for q in held], PROD + "_holdout", synonyms)
        rep["holdout"] = metrics([rank_of(score_hits(h, s, SW, AW), {int(q["answer_id"])}) for (_, h, s), q in zip(hr, held)])
        client.delete_collection(PROD + "_holdout")

    suffix = "" if reranker else "_stage1"
    (HERE / f"results_{args.set}{suffix}.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1))
    write_md(rep, suffix)
    print(json.dumps({k: rep[k] for k in ("thresholds", "final", "latency_ms", "rerank_share")}, ensure_ascii=False))


def pct(x):
    return f"{100 * x:.1f}%"


def write_md(rep, suffix=""):
    title = {"dev": "dev to'plam (tahlil va sozlash uchun)", "final": "yakuniy ko'r to'plam (bir marta o'lchandi)"}[rep["set"]]
    L = [f"# Qidiruv sifati: {title}", "",
         f"Real so'rovlar: {rep['n_real']} ta, bazada javobi yo'q so'rovlar: {rep['n_neg']} ta.", "",
         "## Qadamma-qadam", "", "| Qadam | Hit@1 | Hit@3 | MRR |", "|---|---|---|---|"]
    for s in rep["steps"]:
        L.append(f"| {s['name']} | {pct(s['hit@1'])} | {pct(s['hit@3'])} | {s['mrr']:.3f} |")
    if rep.get("holdout"):
        h = rep["holdout"]
        L += ["", f"Holdout (bazadagi savolning o'zi, indeksdan olib tashlangan holda): Hit@1 {pct(h['hit@1'])}, "
                  f"Hit@3 {pct(h['hit@3'])}. Bazadagi savollar bir-biriga juda o'xshash qolip, shuning uchun bu sinov oson."]
    L += ["", "## Yozilish uslubi bo'yicha (yakuniy tizim)", "", "| Uslub | Soni | Hit@1 | Hit@3 |", "|---|---|---|---|"]
    for k, m in rep["styles"].items():
        L.append(f"| {k} | {m['n']} | {pct(m['hit@1'])} | {pct(m['hit@3'])} |")
    t = rep["thresholds"]
    names = {"answered_ok": "to'g'ri javob berildi", "unsure_ok": "variantlar ko'rsatildi, to'g'risi ichida",
             "unsure_wrong": "variantlar ko'rsatildi, to'g'risi yo'q", "answered_wrong": "noto'g'ri javob berildi",
             "not_found": "\"topilmadi\" deyildi", "smalltalk": "salom/rahmat deb javob berildi"}
    L += ["", "## Tizim foydalanuvchiga nima qaytaradi", "",
          f"Chegaralar ({'reranker bali' if t['scale'] == 'rerank' else '1-bosqich bali'}): javob >= {t['answer']}, "
          f"variantlar >= {t['suggest']} (dev to'plamida tanlangan).", "",
          "| Natija | Real so'rovlar | Bazada yo'q so'rovlar |", "|---|---|---|"]
    for k in ["answered_ok", "unsure_ok", "unsure_wrong", "answered_wrong", "not_found", "smalltalk"]:
        a, b = rep["final"]["real"].get(k, 0), rep["final"]["negatives"].get(k, 0)
        if a or b:
            L.append(f"| {names[k]} | {a} ({pct(a / rep['n_real'])}) | {b} ({pct(b / rep['n_neg'])}) |")
    if rep.get("threshold_table"):
        L += ["", "### Chegara tanlash jadvali (reranker ishlagan so'rovlar)", "",
              "| Chegara | Javoblar aniqligi | Darhol to'g'ri javob | Bazada yo'q savollar chegaradan yuqori |", "|---|---|---|---|"]
        for r in rep["threshold_table"]:
            L.append(f"| {r['t']} | {pct(r['precision'])} | {pct(r['answered_ok'])} | {pct(r['neg_above'])} |")
    lat = rep["latency_ms"]
    L += ["", f"Tezlik (CPU, kesh siz, bitta so'rov): mediana {lat['median']} ms, o'rtacha {lat['mean']} ms, p90 {lat['p90']} ms.",
          "", "## Birinchi o'rinda noto'g'ri javob chiqqan so'rovlar", "",
          "| So'rov | Uslub | To'g'ri javob | Tizim topgani | To'g'risi nechanchi |", "|---|---|---|---|---|"]
    for e in rep["errors"]:
        L.append(f"| {e['query']} | {e['style']} | {e['gold']} | {e['pred']} | {e['rank'] or '-'} |")
    if rep["neg_errors"]:
        L += ["", "## Bazada yo'q, lekin javob berilgan savollar", "", "| So'rov | Tizim topgani |", "|---|---|"]
        for e in rep["neg_errors"]:
            L.append(f"| {e['query']} | {e['pred']} |")
    (HERE / f"results_{rep['set']}{suffix}.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
