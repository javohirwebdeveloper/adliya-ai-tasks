"""bge-m3 bilan vektor olish: dense (1024 o'lchamli) va sparse (so'z og'irliklari)."""
import itertools
import queue
import threading
from concurrent.futures import Future

import numpy as np
import torch

from .config import settings

class ModelThread:
    """Ikkala model (bge-m3 va reranker) ham faqat shu bitta doimiy oqimda hisoblaydi.

    PyTorch protsessor oqimlari guruhi (OpenMP) har bir Python oqimi uchun alohida yaratiladi. Hisoblash turli
    oqimlarga sochilsa, guruhlar bir-biriga xalaqit beradi va javob 2 barobargacha sekinlashadi (o'lchangan:
    bitta oqimda 2,6 s, ikki oqimda 5,7 s). Navbat ustuvorlik bilan: bge-m3 (tez, har bir savolga kerak)
    reranker'dan oldin bajariladi, shuning uchun yuklama paytida yangi savollar reranker'ni kutib qolmaydi.
    """

    def __init__(self):
        self._q: queue.PriorityQueue = queue.PriorityQueue()
        self._seq = itertools.count()
        threading.Thread(target=self._loop, daemon=True, name="model").start()

    def run(self, priority: int, fn, *args):
        fut: Future = Future()
        self._q.put((priority, next(self._seq), fn, args, fut))
        return fut.result()

    def _loop(self):
        while True:
            _, _, fn, args, fut = self._q.get()
            if not fut.set_running_or_notify_cancel():
                continue
            try:
                fut.set_result(fn(*args))
            except BaseException as e:               # noqa: BLE001
                fut.set_exception(e)


MODEL = ModelThread()
PRIORITY_EMBED, PRIORITY_RERANK = 0, 1


class Embedder:
    def __init__(self, model_name: str | None = None, threads: int | None = None):
        self.threads = threads or settings.torch_threads
        torch.set_num_threads(self.threads)
        from FlagEmbedding import BGEM3FlagModel  # og'ir import, faqat kerak bo'lganda

        self.model = BGEM3FlagModel(model_name or settings.model_name, use_fp16=False, devices="cpu")
        self._lock = threading.Lock()  # model bitta, so'rovlar navbat bilan

    def encode(self, texts: list[str], batch_size: int = 16, max_length: int = 256, colbert: bool = False):
        """dense (1024), sparse (so'z og'irliklari) va ixtiyoriy ColBERT (har bir token uchun vektor)."""
        return MODEL.run(PRIORITY_EMBED, self._encode, texts, batch_size, max_length, colbert)

    def _encode(self, texts, batch_size, max_length, colbert):
        with self._lock:
            # OpenMP oqimlar soni har bir oqim (thread) uchun alohida: API ishchi oqimida ham o'rnatilmasa,
            # hisoblash ikki barobar sekinlashadi (o'lchangan: 2,6 s o'rniga 5 s)
            torch.set_num_threads(self.threads)
            out = self.model.encode(
                list(texts), batch_size=batch_size, max_length=max_length,
                return_dense=True, return_sparse=True, return_colbert_vecs=colbert,
            )
        dense = np.asarray(out["dense_vecs"], dtype=np.float32)
        sparse = [{int(k): float(v) for k, v in w.items()} for w in out["lexical_weights"]]
        if colbert:
            return dense, sparse, [np.asarray(c, dtype=np.float32) for c in out["colbert_vecs"]]
        return dense, sparse


def sparse_dot(a: dict[int, float], indices, values) -> float:
    return float(sum(a.get(i, 0.0) * v for i, v in zip(indices, values)))
