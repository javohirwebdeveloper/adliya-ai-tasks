"""Bir vaqtda kelgan savollarni bitta paketga yig'ib kodlash.

CPU da bge-m3 bitta savolni 0,5 soniyada, 8 ta savolni bitta paketda 1,5 soniyada kodlaydi: paketda har biriga
3 barobar kam vaqt ketadi. Yuklama paytida so'rovlar navbat bilan emas, paket bo'lib ishlanadi.
Yolg'iz so'rov esa deyarli kutmaydi (paket yig'ish uchun ko'pi bilan 10 ms).
"""
import queue
import threading
import time


class BatchEncoder:
    def __init__(self, embedder, max_batch: int = 16, wait_ms: float = 10):
        self.embedder = embedder
        self.max_batch = max_batch
        self.wait = wait_ms / 1000
        self._q: queue.Queue = queue.Queue()
        threading.Thread(target=self._loop, daemon=True, name="batch-encoder").start()

    def encode(self, texts: list[str], max_length: int = 128, colbert: bool = False, **_):
        if colbert:                                  # ColBERT vektorlari o'lchami har xil, paketlanmaydi
            return self.embedder.encode(texts, max_length=max_length, colbert=True)
        req = {"texts": list(texts), "max_length": max_length, "done": threading.Event()}
        self._q.put(req)
        req["done"].wait()
        if "error" in req:
            raise req["error"]
        return req["dense"], req["sparse"]

    def _loop(self):
        while True:
            batch = [self._q.get()]
            n, deadline = len(batch[0]["texts"]), time.time() + self.wait
            while n < self.max_batch:
                try:
                    r = self._q.get(timeout=max(0.0, deadline - time.time()))
                except queue.Empty:
                    break
                batch.append(r)
                n += len(r["texts"])
            texts = [t for r in batch for t in r["texts"]]
            try:
                dense, sparse = self.embedder.encode(texts, batch_size=32, max_length=max(r["max_length"] for r in batch))
                k = 0
                for r in batch:
                    m = len(r["texts"])
                    r["dense"], r["sparse"] = dense[k:k + m], sparse[k:k + m]
                    k += m
            except Exception as e:                   # noqa: BLE001
                for r in batch:
                    r["error"] = e
            for r in batch:
                r["done"].set()
