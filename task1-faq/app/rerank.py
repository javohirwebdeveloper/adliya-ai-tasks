"""Ikkinchi bosqich: cross-encoder (bge-reranker-v2-m3).

Birinchi bosqich (bge-m3) savol va javobni alohida-alohida vektorga aylantiradi, shuning uchun tez,
lekin "prava olish" bilan "maktab bitiruvchisi attestat olish" kabi so'zlari o'xshash savollarni
ba'zan adashtiradi. Cross-encoder foydalanuvchi savolini va nomzod javobni birga o'qiydi va aniqroq
baholaydi, lekin sekin. Shuning uchun u faqat birinchi bosqichning eng yaxshi 5 ta nomzodiga qo'llanadi.
"""
import threading

import torch

from .config import settings
from .embedder import MODEL, PRIORITY_RERANK


class Reranker:
    def __init__(self, model_name: str | None = None, threads: int | None = None):
        self.threads = threads or settings.torch_threads
        torch.set_num_threads(self.threads)
        from FlagEmbedding import FlagReranker

        self.model = FlagReranker(model_name or settings.rerank_model, use_fp16=False, devices="cpu")
        self._lock = threading.Lock()

    def score(self, query: str, passages: list[str], max_length: int = 192) -> list[float]:
        if not passages:
            return []
        return MODEL.run(PRIORITY_RERANK, self._score, query, passages, max_length)

    def _score(self, query, passages, max_length):
        with self._lock:
            torch.set_num_threads(self.threads)          # har bir oqimda (embedder.py dagi izohga qarang)
            s = self.model.compute_score([(query, p) for p in passages], normalize=True, max_length=max_length)
        return [float(s)] if isinstance(s, (int, float)) else [float(x) for x in s]
