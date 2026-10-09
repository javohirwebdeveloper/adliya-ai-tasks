"""FastAPI: savol-javob, ovozli savol, baho, mavzular va admin sahifasi.

Asosiy so'rovlar:
  POST /ask                  savolga javob (yoki variantlar, yoki "topilmadi")
  POST /stt                  ovozli xabar -> matn (o'zbekcha, internetsiz; model: app/speech.py)
  POST /feedback             foydalanuvchi bahosi; "foydasiz" bo'lsa boshqa variantlar qaytadi
  GET  /answers/{id}         javob matni
  GET  /categories           mavzular ro'yxati, GET /categories/{id}?page=N mavzu ichidagi savollar
  GET  /health
Admin (ADMIN_TOKEN bilan): /admin sahifasi, /admin/data, /admin/upload, /admin/reindex
"""
import csv
import hmac
import io
import json
import os
import tempfile
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import Cookie, FastAPI, File, Form, Header, HTTPException, Query, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient

from . import db
from .config import settings
from .embedder import Embedder
from .index import build
from .rerank import Reranker
from .search import Searcher
from .speech import load_speech
from .web import ADMIN_PAGE, PAGE

HERE = Path(__file__).resolve().parent
MESSAGES = {
    "not_found": "Bu savol bo'yicha bazada ma'lumot topmadim. Savolni boshqacharoq yozib ko'ring yoki mavzular ro'yxatidan qidiring.",
    "unsure": "Savolingizni to'liq tushunmadim. Shulardan biri kerakmi?",
    "short": "Savolingiz qisqa ekan. Qaysi biri haqida so'rayapsiz?",
    "greeting": "Assalomu alaykum! Davlat xizmatlari bo'yicha savolingizni yozing.",
    "thanks": "Arzimaydi! Yana savolingiz bo'lsa, yozavering.",
}
PAGE_SIZE = 8


def load_categories() -> dict[int, str]:
    path = Path(os.getenv("CATEGORIES", HERE.parent / "data" / "categories.csv"))
    try:
        with open(path, encoding="utf-8") as f:
            return {int(r["id"]): r["name"] for r in csv.DictReader(f)}
    except FileNotFoundError:
        return {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = ConnectionPool(settings.database_url, min_size=1, max_size=8,
                                    kwargs={"autocommit": True, "row_factory": dict_row})
    with app.state.pool.connection() as conn:
        db.init_schema(conn)
    app.state.qdrant = QdrantClient(url=settings.qdrant_url)
    app.state.embedder = Embedder()
    app.state.reranker = Reranker() if settings.rerank else None
    app.state.searcher = Searcher(app.state.qdrant, app.state.embedder, reranker=app.state.reranker)
    app.state.categories = load_categories()
    app.state.speech = load_speech(settings.torch_threads)
    app.state.job = {"state": "idle"}
    app.state.searcher._search("pasport almashtirish uchun qanday hujjatlar kerak", 3)   # birinchi foydalanuvchi kutmasin
    app.state.searcher._cache = {}
    threading.Thread(target=_keep_warm, daemon=True, name="keep-warm").start()
    yield
    app.state.pool.close()


def _keep_warm(every: int = 300):
    """Uzoq so'rov bo'lmasa, operatsion tizim model fayllarini xotiradan chiqarib yuboradi va keyingi birinchi
    savol 2 barobar sekin javob oladi (o'lchangan: 5,3 s). Har 5 daqiqada kichik hisob modellarni "issiq" tutadi."""
    while True:
        time.sleep(every)
        try:
            app.state.embedder.encode(["salom"], max_length=16)
            if app.state.reranker is not None:
                app.state.reranker.score("salom", ["salom"], max_length=16)
        except Exception:                        # noqa: BLE001
            pass


app = FastAPI(title="Savol-javob: semantik qidiruv", version="2.0", lifespan=lifespan)


class AskIn(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    channel: str = "api"
    user_id: str | None = None
    voice: bool = False


class Item(BaseModel):
    answer_id: int
    question: str


class AskOut(BaseModel):
    status: Literal["answered", "unsure", "not_found", "smalltalk"]
    message: str | None = None
    answer_id: int | None = None
    question: str | None = None          # bot qaysi savolni tushundi (javob sarlavhasi)
    answer: str | None = None
    score: float | None = None
    alternatives: list[Item] = []
    log_id: int | None = None
    latency_ms: int
    cached: bool = False
    timing: dict | None = None          # qayerga qancha vaqt ketdi (1-bosqich, reranker), tezlikni kuzatish uchun


def _items(searcher: Searcher, cands, skip: int | None = None, limit: int = 3) -> list[Item]:
    out = [Item(answer_id=c.answer_id, question=searcher.question_of(c.answer_id)) for c in cands
           if c.answer_id != skip]
    return out[:limit]


@app.post("/ask", response_model=AskOut)
def ask(body: AskIn):
    t0 = time.perf_counter()
    s: Searcher = app.state.searcher
    res = s.search(body.question)
    cands = res["candidates"]
    out = AskOut(status=res["status"], latency_ms=0, cached=res.get("cached", False),
                 timing=None if res.get("cached") else dict(res.get("timing") or {}, reranked=bool(res.get("reranked")),
                                                            busy=bool(res.get("busy"))))
    with app.state.pool.connection() as conn:
        if res["status"] == "smalltalk":
            out.message = MESSAGES[res["kind"]]
        elif res["status"] == "answered":
            top = cands[0]
            row = db.get_answers(conn, [top.answer_id]).get(top.answer_id)
            out.answer_id, out.score = top.answer_id, round(top.score, 4)
            out.question, out.answer = s.question_of(top.answer_id), row["answer"] if row else None
            # javob ostida o'xshash savollar: bot noto'g'ri tushungan bo'lsa, odam bitta bosish bilan to'g'risini oladi.
            # Faqat haqiqatan yaqin nomzodlar ko'rsatiladi, aloqasiz "o'xshash savol" sun'iy ko'rinadi.
            near = [c for c in cands[1:] if (c.score >= 0.3 * top.score if res.get("reranked") else c.score >= top.score - 0.12)]
            out.alternatives = _items(s, near, limit=2)
        elif res["status"] == "unsure":
            out.message = MESSAGES["short" if res.get("reason") == "short" else "unsure"]
            out.score = round(cands[0].score, 4)
            out.alternatives = _items(s, cands)
        else:
            out.message = MESSAGES["not_found"]
            out.score = round(cands[0].score, 4) if cands else None
        out.latency_ms = int((time.perf_counter() - t0) * 1000)
        if res["status"] != "smalltalk":
            out.log_id = db.log_query(conn, channel=body.channel, user_id=body.user_id, query=body.question,
                                      status=out.status, answer_id=out.answer_id, score=out.score,
                                      latency_ms=out.latency_ms, voice=body.voice)
    return out


class RetrieveIn(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    k: int = Field(3, ge=1, le=5)


@app.post("/retrieve")
def retrieve(body: RetrieveIn):
    """RAG uchun qidirish: savolga eng yaqin k ta javobning to'liq matni. Bot statistikasiga yozilmaydi.
    status - botning o'z qarori (answered / unsure / not_found): javob beruvchi model buni ham hisobga oladi."""
    s: Searcher = app.state.searcher
    res = s.search(body.question, top_k=body.k)
    cands = res["candidates"][:body.k]
    with app.state.pool.connection() as conn:
        rows = db.get_answers(conn, [c.answer_id for c in cands])
    return {"status": res["status"], "reason": res.get("reason"),
            "items": [{"answer_id": c.answer_id, "question": s.question_of(c.answer_id),
                       "answer": rows[c.answer_id]["answer"], "score": round(c.score, 4)}
                      for c in cands if c.answer_id in rows]}


class FeedbackIn(BaseModel):
    log_id: int
    useful: bool


@app.post("/feedback")
def feedback(body: FeedbackIn):
    with app.state.pool.connection() as conn:
        row = db.set_feedback(conn, body.log_id, 1 if body.useful else -1)
    if not row:
        raise HTTPException(404, "so'rov topilmadi")
    alternatives = []
    if not body.useful:
        res = app.state.searcher.search(row["query"])
        alternatives = _items(app.state.searcher, res["candidates"], skip=row["answer_id"])
    return {"ok": True, "alternatives": alternatives}


@app.post("/stt")
async def stt(file: UploadFile = File(...)):
    if app.state.speech is None:
        raise HTTPException(503, "ovozni tanish moduli o'rnatilmagan")
    data = await file.read()
    if len(data) > 3 * 1024 * 1024:
        raise HTTPException(413, "ovozli xabar juda uzun")
    text = await run_in_threadpool(app.state.speech.transcribe, data)
    return {"text": text}


@app.get("/answers/{answer_id}")
def get_answer(answer_id: int):
    with app.state.pool.connection() as conn:
        row = db.get_answers(conn, [answer_id]).get(answer_id)
    if not row:
        raise HTTPException(404, "javob topilmadi")
    return dict(row, question=app.state.searcher.question_of(answer_id))


@app.get("/categories")
def categories():
    with app.state.pool.connection() as conn:
        counts = db.category_counts(conn)
    names = app.state.categories
    return [{"id": cid, "name": names.get(cid, f"Mavzu {cid}"), "count": n} for cid, n in sorted(counts.items())]


@app.get("/categories/{category_id}")
def category(category_id: int, page: int = Query(0, ge=0)):
    with app.state.pool.connection() as conn:
        n = db.category_counts(conn).get(category_id, 0)
        items = db.category_questions(conn, category_id, PAGE_SIZE, page * PAGE_SIZE)
    if not n:
        raise HTTPException(404, "mavzu topilmadi")
    return {"id": category_id, "name": app.state.categories.get(category_id, f"Mavzu {category_id}"),
            "page": page, "pages": (n + PAGE_SIZE - 1) // PAGE_SIZE, "items": items}


@app.get("/health")
def health():
    with app.state.pool.connection() as conn:
        c = db.counts(conn)
    points = app.state.qdrant.count(settings.collection).count
    thr = {"answer": settings.r_answer, "suggest": settings.r_suggest} if app.state.reranker else \
        {"answer": settings.t_answer, "suggest": settings.t_suggest}
    return {"ok": True, "db": c, "qdrant_points": points, "model": settings.model_name,
            "reranker": settings.rerank_model if app.state.reranker else None, "thresholds": thr,
            "speech": app.state.speech.name if app.state.speech else None}


# ---------------- admin ----------------

def _admin_ok(token: str | None) -> bool:
    return bool(settings.admin_token) and bool(token) and hmac.compare_digest(token, settings.admin_token)


def _require(token: str | None) -> None:
    if not _admin_ok(token):
        raise HTTPException(403, "ruxsat yo'q")


@app.get("/admin", response_class=HTMLResponse)
def admin_page(token: str | None = None, admin: str | None = Cookie(default=None)):
    if token and _admin_ok(token):
        r = RedirectResponse("admin", status_code=303)
        r.set_cookie("admin", token, httponly=True, samesite="strict", max_age=12 * 3600)
        return r
    if not _admin_ok(admin):
        return HTMLResponse("<p style='font:16px system-ui;margin:40px'>Kirish uchun havola kerak: /admin?token=...</p>",
                            status_code=403)
    return ADMIN_PAGE


@app.get("/admin/data")
def admin_data(days: int = Query(7, ge=1, le=90), admin: str | None = Cookie(default=None)):
    _require(admin)
    with app.state.pool.connection() as conn:
        st = db.stats(conn, days)
        names = db.first_questions(conn, [r["answer_id"] for r in st["top"]])
    st["top"] = [dict(r, question=names.get(r["answer_id"], "")) for r in st["top"]]
    st["job"] = app.state.job
    st["categories"] = app.state.categories
    return JSONResponse(json.loads(json.dumps(st, default=str)))


def _reindex_job(answers=None, questions=None, replace=False):
    app.state.job = {"state": "running", "started": time.time(), "step": "baza"}
    try:
        with app.state.pool.connection() as conn:
            if answers is not None:
                if replace:
                    conn.execute("TRUNCATE questions, answers")
                db.upsert_answers(conn, answers)
                db.upsert_questions(conn, questions)
            items = db.index_items(conn)
        app.state.job["step"] = f"indeks ({len(items)} ta matn)"
        build(app.state.qdrant, app.state.embedder, items, log=lambda m: None)
        app.state.searcher.refresh_kb()
        app.state.job = {"state": "done", "finished": time.time(), "items": len(items)}
    except Exception as e:                        # noqa: BLE001
        app.state.job = {"state": "error", "error": str(e)[:300]}


@app.post("/admin/upload")
async def admin_upload(file: UploadFile = File(...), replace: bool = Form(False), admin: str | None = Cookie(default=None)):
    """Excel (answers va questions varaqlari yoki savol | javob ustunlari) yoki CSV ni yuklab, indeksni qayta quradi."""
    _require(admin)
    if app.state.job.get("state") == "running":
        raise HTTPException(409, "yangilash allaqachon ketyapti")
    from .ingest import from_flat, from_tables, read_table, validate
    data = await file.read()
    suffix = ".xlsx" if file.filename.lower().endswith((".xlsx", ".xls")) else ".csv"
    with tempfile.NamedTemporaryFile(suffix=suffix) as f:
        f.write(data)
        f.flush()
        try:
            if suffix == ".xlsx":
                import pandas as pd
                sheets = pd.ExcelFile(f.name).sheet_names
                if {"answers", "questions"} <= set(sheets):
                    answers, questions = from_tables(read_table(f.name, "answers"), read_table(f.name, "questions"))
                else:
                    answers, questions = from_flat(read_table(f.name))
            else:
                answers, questions = from_flat(read_table(f.name))
        except Exception as e:                    # noqa: BLE001
            raise HTTPException(400, f"faylni o'qib bo'lmadi: {e}")
    answers, questions, problems = validate(answers, questions)
    if not answers:
        raise HTTPException(400, "faylda javob topilmadi")
    threading.Thread(target=_reindex_job, args=(answers, questions, replace), daemon=True).start()
    return {"ok": True, "answers": len(answers), "questions": len(questions), "warnings": problems[:20]}


@app.post("/admin/reindex")
def reindex(x_admin_token: str = Header(default=""), admin: str | None = Cookie(default=None)):
    _require(x_admin_token or admin)
    if app.state.job.get("state") == "running":
        raise HTTPException(409, "yangilash allaqachon ketyapti")
    threading.Thread(target=_reindex_job, daemon=True).start()
    return {"ok": True, "state": "running"}


@app.get("/", response_class=HTMLResponse)
def page():
    return PAGE
