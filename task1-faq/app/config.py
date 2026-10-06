"""Sozlamalar muhit o'zgaruvchilaridan (.env) olinadi."""
import os

from dotenv import load_dotenv

load_dotenv()


def _float(name: str, default: str) -> float:
    return float(os.getenv(name, default))


class Settings:
    database_url = os.getenv("DATABASE_URL", "postgresql://faq:faq@localhost:5433/faq")
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    collection = os.getenv("QDRANT_COLLECTION", "faq")

    # bge-m3: internetsiz muhitda modelni oldindan yuklab, EMBED_MODEL ga papka yo'lini berish mumkin
    model_name = os.getenv("EMBED_MODEL", "BAAI/bge-m3")
    torch_threads = int(os.getenv("TORCH_THREADS", "4"))

    # qidiruv: dense natija + bge-m3 leksik (sparse) og'irliklari bilan qayta baholash
    candidates = int(os.getenv("CANDIDATES", "40"))
    sparse_weight = _float("SPARSE_WEIGHT", "0.3")
    colbert_weight = _float("COLBERT_WEIGHT", "0")      # bge-m3 ning ColBERT (so'zma-so'z) bali; 0: o'chiq
    answer_weight = _float("ANSWER_WEIGHT", "0.95")  # javob matniga mos kelish savolga qaraganda sal kuchsizroq dalil

    synonyms_path = os.getenv("SYNONYMS", os.path.join(os.path.dirname(__file__), "..", "data", "synonyms.csv"))

    # ikkinchi bosqich (cross-encoder): eng yaxshi RERANK_TOP nomzodni qayta baholaydi
    rerank = os.getenv("RERANK", "1") == "1"
    rerank_model = os.getenv("RERANK_MODEL", "BAAI/bge-reranker-v2-m3")
    rerank_top = int(os.getenv("RERANK_TOP", "3"))
    rerank_chars = int(os.getenv("RERANK_CHARS", "300"))     # javob matnidan nechta belgi reranker'ga beriladi (0: faqat savol)
    rerank_weight = _float("RERANK_WEIGHT", "1.0")           # yakuniy ball = w*reranker + (1-w)*1-bosqich
    # "kulrang zona": 1-bosqich ishonchli bo'lsa (bali >= GRAY_T va ikkinchisidan GRAY_M ga oldinda) reranker chaqirilmaydi
    gray_t = _float("GRAY_T", "0.8")
    gray_m = _float("GRAY_M", "0.1")
    # yuklama: bir vaqtda kelgan savollar paket bo'lib kodlanadi; reranker navbatida RERANK_QUEUE tadan ortiq
    # so'rov bo'lsa, keyingilari kutmaydi va 1-bosqich natijasi bilan javob oladi (aniqlik biroz pastroq, lekin tez)
    batching = os.getenv("BATCHING", "1") == "1"
    rerank_queue = int(os.getenv("RERANK_QUEUE", "2"))

    # qaror chegaralari (eval/evaluate.py dev to'plamida tanlangan, eval/thresholds.json)
    t_answer = _float("T_ANSWER", "0.81")     # 1-bosqich bali (reranker o'chiq yoki band bo'lsa)
    t_suggest = _float("T_SUGGEST", "0.65")
    r_answer = _float("R_ANSWER", "0.25")     # reranker bali
    r_suggest = _float("R_SUGGEST", "0.002")

    admin_token = os.getenv("ADMIN_TOKEN", "")
    api_url = os.getenv("API_URL", "http://localhost:8000")
    bot_token = os.getenv("BOT_TOKEN", "")


settings = Settings()
