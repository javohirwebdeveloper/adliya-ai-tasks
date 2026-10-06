"""Yuklama sinovi: bir vaqtda N foydalanuvchi savol beradi yoki hujjat yuklaydi.

  python tools/loadtest.py faq  --url http://127.0.0.1:8091 --users 20 --seconds 60 --mode mixed
  python tools/loadtest.py docs --url http://127.0.0.1:8093 --users 5 --seconds 60

faq rejimlari: unique (har savol yangi, kesh yordam bermaydi), popular (mashhur savollar, kesh ishlaydi),
mixed (70% mashhur, 30% yangi; real botga yaqin).
"""
import argparse
import asyncio
import csv
import json
import random
import statistics
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent


def pct(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(p / 100 * len(xs)))] if xs else 0


async def faq_user(client, queries, popular, mode, stop, out):
    while time.time() < stop:
        if mode == "unique" or (mode == "mixed" and random.random() < 0.3):
            q = random.choice(queries) + " " + random.choice(["", "iltimos", "aytib bering", "bilmoqchiman", "?"]) + f" {random.randint(1, 10**6)}"
        else:
            q = random.choice(popular)
        t = time.perf_counter()
        try:
            r = await client.post("/ask", json={"question": q, "channel": "loadtest"})
            d = r.json() if r.status_code == 200 else {}
            out.append(((time.perf_counter() - t) * 1000, r.status_code, d.get("cached", False), d.get("timing") or {}))
        except Exception:
            out.append(((time.perf_counter() - t) * 1000, 0, False, {}))


async def docs_user(client, files, stop, out):
    while time.time() < stop:
        f = random.choice(files)
        t = time.perf_counter()
        try:
            r = await client.post("/api/analyze", files={"file": (f.name, f.read_bytes(), "application/pdf")})
            out.append(((time.perf_counter() - t) * 1000, r.status_code, f.name))
        except Exception:
            out.append(((time.perf_counter() - t) * 1000, 0, f.name))


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", choices=["faq", "docs"])
    ap.add_argument("--url", required=True)
    ap.add_argument("--users", type=int, default=10)
    ap.add_argument("--seconds", type=int, default=60)
    ap.add_argument("--mode", default="mixed", choices=["unique", "popular", "mixed"])
    a = ap.parse_args()
    out, stop = [], time.time() + a.seconds
    async with httpx.AsyncClient(base_url=a.url, timeout=180) as client:
        if a.target == "faq":
            rows = list(csv.DictReader(open(ROOT / "task1-faq/eval/test_queries.csv", encoding="utf-8")))
            queries = [r["query"] for r in rows]
            popular = queries[:30]
            await asyncio.gather(*[faq_user(client, queries, popular, a.mode, stop, out) for _ in range(a.users)])
        else:
            files = sorted((ROOT / "task2-docs/samples").glob("*/*.pdf"))
            await asyncio.gather(*[docs_user(client, files, stop, out) for _ in range(a.users)])
    lat = [x[0] for x in out if x[1] == 200]
    errors = sum(1 for x in out if x[1] != 200)
    res = {"target": a.target, "users": a.users, "seconds": a.seconds, "mode": a.mode if a.target == "faq" else None,
           "requests": len(out), "errors": errors, "rps": round(len(out) / a.seconds, 2),
           "p50_ms": round(pct(lat, 50)), "p95_ms": round(pct(lat, 95)), "max_ms": round(max(lat) if lat else 0)}
    if a.target == "faq":
        res["cache_hits"] = sum(1 for x in out if x[2])
        tm = [x[3] for x in out if x[3]]
        if tm:
            res["reranked"] = sum(1 for t in tm if t.get("reranked"))
            res["skipped_busy"] = sum(1 for t in tm if t.get("busy"))
            res["stage1_p50_ms"] = round(pct([t["stage1_ms"] for t in tm], 50))
            rr = [t["rerank_ms"] for t in tm if t.get("reranked")]
            res["rerank_p50_ms"] = round(pct(rr, 50)) if rr else 0
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
