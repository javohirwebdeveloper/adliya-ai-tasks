"""Savolga eng mos javobni topish va qaror qabul qilish.

1-bosqich (tez, bge-m3):
  savol normallashtiriladi (apostroflar, salom-rahmatlar, kirill -> lotin varianti), so'zlashuv
  so'zlariga rasmiy nomi qo'shiladi ("prava" -> "haydovchilik guvohnomasi"). Qdrant'dan dense vektor
  bo'yicha eng yaqin 40 ta matn olinadi va bge-m3 ning leksik og'irliklari bilan qayta baholanadi:
  ball = cosine + 0.3 * sparse. Natijalar javob bo'yicha guruhlanadi (javobning eng mos savoli olinadi).
2-bosqich (aniq, bge-reranker-v2-m3):
  eng yaxshi 5 ta nomzod "savol + javob" ko'rinishida foydalanuvchi savoli bilan birga baholanadi.
Qaror (dev to'plamida tanlangan chegaralar bilan):
  ball >= R_ANSWER -> javob beriladi; R_SUGGEST..R_ANSWER -> "balki shuni so'ramoqchimisiz" variantlari;
  undan past -> "bazada javob topilmadi".
"""
import re
import threading
import time
from dataclasses import dataclass

from qdrant_client import QdrantClient, models

from .config import settings
from .embedder import Embedder, sparse_dot
from .normalize import clean_kb_question, load_synonyms, normalize, query_variants

SMALLTALK = [
    # ovozli xabar matnga aylanganda "aleykum", "alaykim" kabi og'zaki shakllar ham chiqadi
    (re.compile(r"^\W*((va\s+)?(assalomu?|salom)?\s*(alaykum|aleykum|alaykim|aleykim|alaikum)(\s+assalom)?|assalom|salom|salem|"
                r"xayrli kun|hayrli kun|привет|здравствуйте|салом|ассалому алайкум|hello|hi)\W*$", re.I), "greeting"),
    (re.compile(r"^\W*(katta\s+)?(rahmat|raxmat|tashakkur|спасибо|рахмат|раҳмат|thanks|thank you)\W*$", re.I), "thanks"),
]
UZ_CYRILLIC = re.compile(r"[ўқғҳЎҚҒҲ]")
# savol ichidagi mazmunsiz so'zlar: qisqa savolni aniqlashda sanalmaydi
STOPWORDS = {"qanday", "qanaqa", "nima", "nimalar", "qayerda", "qayerga", "qayerdan", "kerak", "kerakmi", "menga",
             "iltimos", "haqida", "bo'yicha", "uchun", "qilish", "qilsam", "bo'ladi", "bo'ladimi", "mumkin", "mumkinmi",
             "va", "yoki", "bilan", "men", "bu", "shu", "qancha", "necha", "qachon", "nega", "как", "что", "где"}
CACHE_TTL = 3600


@dataclass
class Candidate:
    answer_id: int
    score: float
    matched_text: str
    kind: str                 # "question" yoki "answer": nima bilan mos keldi
    stage1: float = 0.0


def score_hits(hits_per_variant, sparse_per_variant, sparse_weight: float, answer_weight: float,
               use_answers: bool = True, colbert_per_variant=None) -> list[Candidate]:
    best: dict[int, Candidate] = {}
    colbert_per_variant = colbert_per_variant or [{}] * len(hits_per_variant)
    for hits, q_sparse, col in zip(hits_per_variant, sparse_per_variant, colbert_per_variant):
        for h in hits:
            p = h.payload
            if p["kind"] == "answer" and not use_answers:
                continue
            s = h.score
            if sparse_weight and h.vector and "sparse" in h.vector:
                sv = h.vector["sparse"]
                s += sparse_weight * sparse_dot(q_sparse, sv.indices, sv.values)
            s += col.get(h.id, 0.0)
            if p["kind"] == "answer":
                s *= answer_weight
            cur = best.get(p["answer_id"])
            if cur is None or s > cur.score:
                best[p["answer_id"]] = Candidate(p["answer_id"], s, p["text"], p["kind"], s)
    return sorted(best.values(), key=lambda c: c.score, reverse=True)


def s1_norm(x: float) -> float:
    """1-bosqich bali (cosine + 0.3*sparse) amalda 0.5..1.1 oralig'ida; reranker bali bilan aralashtirish uchun 0..1 ga."""
    return min(max((x - 0.5) / 0.5, 0.0), 1.0)


def decide(top_score: float | None, t_answer: float, t_suggest: float) -> str:
    if top_score is None or top_score < t_suggest:
        return "not_found"
    return "answered" if top_score >= t_answer else "unsure"


def content_words(query: str) -> int:
    words = re.findall(r"[\w']{3,}", normalize(query).lower())
    return sum(w not in STOPWORDS for w in words)


def final_status(query: str, cands: list[Candidate], confident: bool, t_answer: float, t_suggest: float):
    """Yakuniy qaror: javob / variantlar / topilmadi. Qidiruv ham, baholash skripti ham shu funksiyadan foydalanadi."""
    status = "answered" if confident else decide(cands[0].score if cands else None, t_answer, t_suggest)
    reason = None
    short = content_words(query) <= 2
    if status == "answered" and short:
        # "prava", "muddat" kabi qisqa savolda bitta javobni tanlab berish taxmin bo'lib qoladi:
        # ikkinchi nomzoddan keskin ustun bo'lmasa, variantlar ko'rsatiladi
        second = cands[1].score if len(cands) > 1 else 0.0
        if not (cands[0].score >= 0.8 and cands[0].score - second >= 0.3):
            status, reason = "unsure", "short"
    elif status == "not_found" and short and cands and cands[0].stage1 >= 0.6:
        status, reason = "unsure", "short"           # "muddat": mavzu bazada bor, lekin savol juda umumiy
    return status, reason


def smalltalk_kind(query: str) -> str | None:
    q = normalize(query).lower()
    for rx, kind in SMALLTALK:
        if rx.match(q):
            return kind
    return None


def _retry(fn, *args, **kwargs):
    """Qdrant bilan ulanish uzoq bo'sh turgandan keyin yopilgan bo'lishi mumkin: bir marta qayta urinib ko'riladi."""
    from qdrant_client.http.exceptions import ResponseHandlingException
    try:
        return fn(*args, **kwargs)
    except ResponseHandlingException:
        return fn(*args, **kwargs)


class Searcher:
    def __init__(self, client: QdrantClient, embedder: Embedder, collection: str | None = None, reranker=None):
        self.client = client
        self.embedder = embedder
        self.collection = collection or settings.collection
        self.reranker = reranker
        self.synonyms = load_synonyms(settings.synonyms_path)
        self._cache: dict[str, tuple[float, dict]] = {}
        from .batching import BatchEncoder
        self.encoder = BatchEncoder(embedder) if settings.batching else embedder
        self._state = threading.Lock()
        self._rerank_queue = 0
        self.refresh_kb()

    def refresh_kb(self) -> None:
        """Reranker uchun javob matnlari va har bir javobning birinchi savoli (xotirada, ~500 ta)."""
        self._cache = {}
        self.kb: dict[int, dict] = {}
        offset = None
        while True:
            pts, offset = _retry(self.client.scroll, self.collection, limit=512, offset=offset, with_payload=True)
            for p in pts:
                d = self.kb.setdefault(p.payload["answer_id"], {"answer": "", "question": "", "qid": 10**9})
                if p.payload["kind"] == "answer":
                    d["answer"] = p.payload["text"]
                elif p.payload["item_id"] < d["qid"]:
                    d["qid"], d["question"] = p.payload["item_id"], p.payload["text"]
            if offset is None:
                break

    def passage(self, c: Candidate) -> str:
        kb = self.kb.get(c.answer_id, {})
        q = clean_kb_question(c.matched_text if c.kind == "question" else kb.get("question", ""))
        n = settings.rerank_chars
        return f"{q}\n{kb.get('answer', '')[:n]}" if n else q

    def retrieve(self, query: str, limit: int | None = None):
        variants = query_variants(query, self.synonyms)
        wc = settings.colbert_weight
        enc = self.encoder.encode(variants, max_length=128, colbert=wc > 0)
        dense, sparse = enc[0], enc[1]
        hits, cols = [], []
        for i, d in enumerate(dense):
            hs = _retry(self.client.query_points, self.collection, query=d.tolist(), using="dense",
                        limit=limit or settings.candidates, with_payload=True, with_vectors=["sparse"]).points
            if wc > 0 and hs:
                # o'sha nomzodlarni ColBERT (MaxSim) bilan qayta baholash Qdrant ichida bajariladi
                q = enc[2][i]
                cb = _retry(self.client.query_points,
                    self.collection, query=q.tolist(), using="colbert", limit=len(hs),
                    query_filter=models.Filter(must=[models.HasIdCondition(has_id=[h.id for h in hs])])).points
                cols.append({p.id: wc * p.score / len(q) for p in cb})   # MaxSim yig'indisi -> token bo'yicha o'rtacha
            else:
                cols.append({})
            hits.append(hs)
        return variants, hits, sparse, cols

    def rerank(self, variants: list[str], cands: list[Candidate], top: int | None = None) -> list[Candidate]:
        top = cands[: top or settings.rerank_top]
        query = variants[-1] if len(variants) > 1 and UZ_CYRILLIC.search(variants[0]) else variants[0]
        scores = self.reranker.score(query, [self.passage(c) for c in top])
        w = settings.rerank_weight
        for c, s in zip(top, scores):
            c.score = w * s + (1 - w) * s1_norm(c.stage1)
        return sorted(top, key=lambda c: c.score, reverse=True)

    def question_of(self, answer_id: int) -> str:
        """Javobning birinchi (eng aniq yozilgan) savoli: foydalanuvchiga sarlavha sifatida ko'rsatiladi."""
        return self.kb.get(answer_id, {}).get("question", "")

    def search(self, query: str, top_k: int = 3) -> dict:
        """Natija keshlanadi: bir xil savol (normallashtirilgandan keyin) bir soat davomida darhol qaytadi."""
        key = normalize(query).lower()
        hit = self._cache.get(key)
        if hit and time.time() - hit[0] < CACHE_TTL:
            return dict(hit[1], cached=True, latency_ms=0)
        res = self._search(query, top_k)
        if res["status"] != "smalltalk":
            if len(self._cache) > 2000:
                self._cache.clear()
            self._cache[key] = (time.time(), res)
        return dict(res, cached=False)

    def _search(self, query: str, top_k: int) -> dict:
        t0 = time.perf_counter()
        kind = smalltalk_kind(query)
        if kind:
            return {"status": "smalltalk", "kind": kind, "reason": None, "candidates": [], "latency_ms": 0}
        if len(normalize(query)) < 3 or not re.search(r"\w{2,}", query):
            return {"status": "not_found", "reason": None, "candidates": [], "latency_ms": 0}
        variants, hits, sparse, cols = self.retrieve(query)
        cands = score_hits(hits, sparse, settings.sparse_weight, settings.answer_weight, colbert_per_variant=cols)
        t1 = time.perf_counter()
        reranked = False
        confident = bool(cands) and cands[0].score >= settings.gray_t and (
            len(cands) < 2 or cands[0].score - cands[1].score >= settings.gray_m)
        busy = False
        if self.reranker is not None and settings.rerank and cands and not confident:
            with self._state:
                busy = self._rerank_queue >= settings.rerank_queue
                if not busy:
                    self._rerank_queue += 1
            if not busy:
                try:
                    cands = self.rerank(variants, cands)
                finally:
                    with self._state:
                        self._rerank_queue -= 1
                reranked = True
        if reranked:
            t_answer, t_suggest = settings.r_answer, settings.r_suggest
        else:
            t_answer, t_suggest = settings.t_answer, settings.t_suggest
        status, reason = final_status(query, cands, confident, t_answer, t_suggest)
        t2 = time.perf_counter()
        return {"status": status, "reason": reason, "candidates": cands[:max(top_k, 3)], "reranked": reranked,
                "busy": busy, "latency_ms": int((t2 - t0) * 1000),
                "timing": {"stage1_ms": int((t1 - t0) * 1000), "rerank_ms": int((t2 - t1) * 1000)}}
