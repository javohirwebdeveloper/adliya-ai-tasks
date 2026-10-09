"""Qalqonning veb-sahifasi va API si. Matn hech qayerda saqlanmaydi va jurnalga yozilmaydi.

  POST /api/mask    {"text": "..."}              -> {"masked": "...", "key": {"[ISM_1]": "..."}, "found": [...]}
  POST /api/unmask  {"text": "...", "key": {...}} -> {"text": "..."}
  GET  /api/namunalar                             -> Gemma 4 ning oldindan yozib olingan haqiqiy javoblari
  GET  /api/rag_namunalar                         -> RAG (1-topshiriq bazasi + qalqon + Gemma 4) namunalari
"""
import json
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from shield import Shield

app = FastAPI(title="Shaxsiy ma'lumot qalqoni", version="1.0")
S = Shield()
S.mask("Karimov Akmal, AB1234567, +998 90 123 45 67")       # birinchi so'rov sekin bo'lmasin
EXAMPLES = Path(__file__).with_name("namunalar.json")
NAMUNA = json.loads(EXAMPLES.read_text(encoding="utf-8")) if EXAMPLES.exists() else []
PAGE = Path(__file__).with_name("page.html").read_text(encoding="utf-8")
RAG_FILE = Path(__file__).with_name("rag_namunalar.json")
RAG_NAMUNA = json.loads(RAG_FILE.read_text(encoding="utf-8")) if RAG_FILE.exists() else []


class MaskIn(BaseModel):
    text: str = Field(min_length=1, max_length=20000)


class UnmaskIn(BaseModel):
    text: str = Field(max_length=20000)
    key: dict[str, str]


@app.post("/api/mask")
def mask(body: MaskIn):
    t = time.perf_counter()
    masked, key = S.mask(body.text)
    ms = round((time.perf_counter() - t) * 1000, 2)        # faqat yashirish vaqti
    found = [{"tur": k, "qiymat": body.text[s:e]} for k, s, e in S.detect(body.text)]
    return {"masked": masked, "key": key, "found": found, "ms": ms}


@app.post("/api/unmask")
def unmask(body: UnmaskIn):
    if len(body.key) > 500:
        raise HTTPException(413, "kalit juda katta")
    return {"text": Shield.unmask(body.text, body.key)}


@app.get("/api/namunalar")
def namunalar():
    return NAMUNA


@app.get("/api/rag_namunalar")
def rag_namunalar():
    return RAG_NAMUNA


@app.get("/health")
def health():
    return {"ok": True}


app.mount("/f", StaticFiles(directory=Path(__file__).with_name("static") / "fonts"), name="fonts")   # IBM Plex (OFL)


@app.get("/", response_class=HTMLResponse)
def page():
    return PAGE
