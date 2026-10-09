"""3-qadam (shu serverda, yengil): Gemma qayta yozgan qidiruv savollari bilan qidiruvni o'lchash (query rewriting).
Natija natija/gemma_rag.json ga "qidiruv_qayta" bo'lib yoziladi; evaluate.py uni jadvalga qo'shadi.
Bu faqat qidiruvni o'lchaydi: Gemma'ning javoblari yashirilgan matnning o'zi bo'yicha topilgan manbalarda yozilgan.

    python rag/qayta_qidirish.py
"""
import json
import time

import httpx

from prepare import API, PAUSE, ROOT, TAG, wait_for_quiet_server


def main():
    path = ROOT / "rag" / "natija" / "gemma_rag.json"
    items = json.load(open(path, encoding="utf-8"))
    cache_file = ROOT / "rag" / "natija" / "qidiruv_kesh.jsonl"
    cache = {}
    for line in open(cache_file, encoding="utf-8"):
        d = json.loads(line)
        cache[d["q"]] = d["r"]
    client = httpx.Client(base_url=API, timeout=60)
    for n, it in enumerate(items, 1):
        q = TAG.sub("", it.get("qayta_yozilgan") or "").strip() or it["masked"]   # belgi qolgan bo'lsa ham o'chadi
        if q not in cache:
            wait_for_quiet_server()
            r = client.post("/retrieve", json={"question": q, "k": 3})
            r.raise_for_status()
            cache[q] = r.json()
            with open(cache_file, "a", encoding="utf-8") as f:
                f.write(json.dumps({"q": q, "r": cache[q]}, ensure_ascii=False) + "\n")
            time.sleep(PAUSE)
        it["qidiruv_qayta"] = cache[q]
        if n % 30 == 0:
            print(f"{n}/{len(items)}", flush=True)
    path.write_text(json.dumps(items, ensure_ascii=False))
    print("tayyor")


if __name__ == "__main__":
    main()
