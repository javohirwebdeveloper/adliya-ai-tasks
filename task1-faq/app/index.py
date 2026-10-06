"""Qdrant indeksini PostgreSQL dagi faol savol-javoblardan quradi.

Qolip so'zlarini tozalash (clean=True) sinab ko'rilgan, lekin dev to'plamda natijani yomonlashtirdi
(eval/results_dev.md), shuning uchun standart holatda o'chiq: savollar bazadagidek indekslanadi.

Har bir savol va har bir javob matni alohida nuqta bo'ladi. Javob matnining o'zi ham
indekslanadi: foydalanuvchi ba'zan savolni emas, javob ichidagi tafsilotni so'raydi
("kvitansiya shartmi?"), bunday so'z bazadagi savollarda bo'lmasligi mumkin.
"""
import time

from qdrant_client import QdrantClient, models

from .config import settings
from .embedder import Embedder
from .normalize import clean_kb_question, normalize

ANSWER_ID_OFFSET = 10_000_000  # javob nuqtalari savol id lari bilan to'qnashmasin


def point_id(item: dict) -> int:
    return item["item_id"] if item["kind"] == "question" else ANSWER_ID_OFFSET + item["item_id"]


def index_text(item: dict, clean: bool = False) -> str:
    if item["kind"] == "question" and clean:
        return clean_kb_question(item["text"])
    return normalize(item["text"])


def build(client: QdrantClient, embedder: Embedder, items: list[dict], collection: str | None = None,
          batch: int = 64, log=print, clean: bool = False, colbert: bool | None = None) -> None:
    collection = collection or settings.collection
    colbert = settings.colbert_weight > 0 if colbert is None else colbert
    if client.collection_exists(collection):
        client.delete_collection(collection)
    vectors = {"dense": models.VectorParams(size=1024, distance=models.Distance.COSINE)}
    if colbert:
        # ColBERT: har bir matn uchun tokenlar soncha vektor, Qdrant ularni MaxSim bilan solishtiradi
        vectors["colbert"] = models.VectorParams(
            size=1024, distance=models.Distance.COSINE, on_disk=True,
            multivector_config=models.MultiVectorConfig(comparator=models.MultiVectorComparator.MAX_SIM),
            hnsw_config=models.HnswConfigDiff(m=0))                # faqat qayta baholash uchun, alohida qidiruv yo'q
    client.create_collection(collection, vectors_config=vectors,
                             sparse_vectors_config={"sparse": models.SparseVectorParams()})
    t0 = time.time()
    for i in range(0, len(items), batch):
        chunk = items[i:i + batch]
        enc = embedder.encode([index_text(it, clean) for it in chunk], batch_size=batch, colbert=colbert)
        dense, sparse = enc[0], enc[1]
        points = [
            models.PointStruct(
                id=point_id(it),
                vector={
                    "dense": dense[j].tolist(),
                    "sparse": models.SparseVector(indices=list(sparse[j]), values=list(sparse[j].values())),
                    **({"colbert": enc[2][j].tolist()} if colbert else {}),
                },
                payload={k: it[k] for k in ("kind", "answer_id", "item_id", "text", "category_id", "topic_id")},
            )
            for j, it in enumerate(chunk)
        ]
        client.upsert(collection, points=points, wait=True)
        log(f"  {min(i + batch, len(items))}/{len(items)}")
    log(f"indeks tayyor: {len(items)} ta matn, {time.time() - t0:.0f} s")
