"""Tajriba: bge-m3 ning uchinchi rejimi (ColBERT, so'zma-so'z MaxSim) 1-bosqichni yaxshilaydimi?

Barcha baza matnlari uchun ColBERT vektorlari bir marta hisoblanadi (eval/kb_colbert.npz), so'ng dev
to'plamida dense, sparse va ColBERT ballarining turli aralashmalari solishtiriladi. Reranker ishlatilmaydi.

  python -m eval.colbert_exp
"""
import json
import time
from pathlib import Path

import numpy as np
from qdrant_client import QdrantClient

from app.config import settings
from app.embedder import sparse_dot
from app.normalize import load_synonyms, normalize, query_variants
from eval.evaluate import AW, HERE, read_csv

CACHE = HERE / "kb_colbert.npz"


def encode(model, texts, bs=32):
    out = model.encode(texts, batch_size=bs, max_length=256, return_dense=True, return_sparse=True, return_colbert_vecs=True)
    return (np.asarray(out["dense_vecs"], np.float32), [{int(k): float(v) for k, v in w.items()} for w in out["lexical_weights"]],
            [np.asarray(c, np.float16) for c in out["colbert_vecs"]])


def maxsim(q: np.ndarray, d: np.ndarray) -> float:
    return float((q.astype(np.float32) @ d.astype(np.float32).T).max(1).mean())


def main():
    import torch
    torch.set_num_threads(settings.torch_threads)
    from FlagEmbedding import BGEM3FlagModel
    model = BGEM3FlagModel(settings.model_name, use_fp16=False, devices="cpu")
    client = QdrantClient(url=settings.qdrant_url)
    pts, off = [], None
    while True:
        b, off = client.scroll(settings.collection, limit=512, offset=off, with_payload=True, with_vectors=["dense", "sparse"])
        pts += b
        if off is None:
            break
    ids = [p.id for p in pts]
    if CACHE.exists():
        z = np.load(CACHE, allow_pickle=True)
        col = dict(zip(z["ids"].tolist(), z["vecs"]))
    else:
        t0 = time.time()
        _, _, vecs = encode(model, [normalize(p.payload["text"]) for p in pts])
        col = dict(zip(ids, vecs))
        np.savez(CACHE, ids=np.array(ids), vecs=np.array(vecs, dtype=object), allow_pickle=True)
        print(f"baza ColBERT vektorlari: {len(ids)} ta, {time.time() - t0:.0f} s", flush=True)
    P = {p.id: p for p in pts}
    D = np.array([p.vector["dense"] for p in pts], np.float32)
    D /= np.linalg.norm(D, axis=1, keepdims=True)

    syn = load_synonyms(settings.synonyms_path)
    real = read_csv(HERE / "test_queries.csv")
    gold = [{int(r["answer_id"])} | {int(x) for x in r["alt_answer_ids"].split(";") if x.strip()} for r in real]
    t0 = time.time()
    rows = []
    for r in real:
        vs = query_variants(r["query"], syn)
        qd, qs, qc = encode(model, vs, bs=8)
        rows.append((qd, qs, qc))
    per_q = (time.time() - t0) / len(real)
    print(f"so'rov kodlash (dense+sparse+colbert): {per_q:.2f} s", flush=True)

    def run(wd, ws, wc, top=40):
        hit1 = hit3 = 0
        for (qd, qs, qc), g in zip(rows, gold):
            best = {}
            for v in range(len(qd)):
                sims = D @ qd[v]
                for i in np.argpartition(-sims, top)[:top]:
                    p = pts[i]
                    sv = p.vector["sparse"]
                    s = wd * float(sims[i]) + ws * sparse_dot(qs[v], sv.indices, sv.values) + wc * maxsim(qc[v], col[p.id])
                    if p.payload["kind"] == "answer":
                        s *= AW
                    a = p.payload["answer_id"]
                    if s > best.get(a, -9):
                        best[a] = s
            ranked = sorted(best, key=best.get, reverse=True)
            hit1 += ranked[0] in g
            hit3 += any(a in g for a in ranked[:3])
        return hit1 / len(rows), hit3 / len(rows)

    res = {}
    for name, w in {"dense": (1, 0, 0), "dense+sparse": (1, 0.3, 0), "colbert": (0, 0, 1), "dense+colbert": (0.5, 0, 0.5),
                    "dense+sparse+colbert (0.4/0.2/0.4)": (0.4, 0.2, 0.4), "dense+sparse+colbert (1/0.3/1)": (1, 0.3, 1),
                    "dense+sparse+colbert (1/0.3/0.5)": (1, 0.3, 0.5)}.items():
        h1, h3 = run(*w)
        res[name] = {"hit@1": round(h1, 4), "hit@3": round(h3, 4)}
        print(name, res[name], flush=True)
    (HERE / "colbert_dev.json").write_text(json.dumps({"results": res, "query_encode_s": round(per_q, 2)}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
