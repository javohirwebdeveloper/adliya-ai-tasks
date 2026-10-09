"""Model o'qitish demosi: sahifa va Modal GPU'dagi o'qitilgan modelga so'rov.

Brauzer GPU'ga to'g'ridan-to'g'ri murojaat qilmaydi: kalit shu serverda qoladi, kunlik so'rovlar soni cheklangan
(GPU soniyabay pullik). Matn saqlanmaydi va jurnalga yozilmaydi.
"""
import datetime
import json
import os
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

HERE = Path(__file__).parent
URL, TOKEN = os.environ.get("MODAL_URL", ""), os.environ.get("TRENING_TOKEN", "")
DAILY_LIMIT = int(os.environ.get("DAILY_LIMIT", "300"))
PAGE = (HERE / "page.html").read_text(encoding="utf-8")
EXAMPLES = json.loads((HERE / "namunalar.json").read_text(encoding="utf-8"))
app = FastAPI(title="Model o'qitish demosi")
used = {"day": None, "n": 0}


class In(BaseModel):
    text: str = Field(min_length=3, max_length=600)


@app.post("/api/tahlil")
async def tahlil(body: In):
    today = datetime.date.today()
    if used["day"] != today:
        used.update(day=today, n=0)
    if used["n"] >= DAILY_LIMIT:
        raise HTTPException(429, "bugungi chegara tugadi")
    used["n"] += 1
    try:
        async with httpx.AsyncClient(timeout=300) as c:
            r = await c.post(URL, json={"token": TOKEN, "text": body.text})
    except httpx.HTTPError:
        raise HTTPException(502, "model bilan bog'lanib bo'lmadi")
    if r.status_code != 200:
        raise HTTPException(502, "model javob bermadi")
    return r.json()


@app.get("/api/namunalar")
def namunalar():
    return EXAMPLES


@app.get("/health")
def health():
    return {"ok": True}


app.mount("/f", StaticFiles(directory=HERE / "static" / "fonts"), name="fonts")


@app.get("/", response_class=HTMLResponse)
def page():
    return PAGE
