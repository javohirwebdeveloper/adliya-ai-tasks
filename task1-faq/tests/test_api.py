"""Ishlab turgan API ga qarshi sinov (API_URL, standart http://127.0.0.1:8000). API ishlamasa, o'tkazib yuboriladi."""
import os
from pathlib import Path

import httpx
import pytest

URL = os.getenv("API_URL", "http://127.0.0.1:8000")
try:
    httpx.get(URL + "/health", timeout=3).raise_for_status()
except Exception:                                   # noqa: BLE001
    pytest.skip("API ishlamayapti", allow_module_level=True)

c = httpx.Client(base_url=URL, timeout=120)


def ask(q):
    r = c.post("/ask", json={"question": q, "channel": "eval"})
    assert r.status_code == 200
    return r.json()


def test_answer_has_title_and_alternatives():
    d = ask("ID karta olish uchun qanday hujjatlar kerak?")
    assert d["status"] == "answered" and d["answer_id"] == 2 and d["question"] and d["log_id"]


def test_short_query_shows_options():
    for q in ("prava", "muddat"):
        d = ask(q)
        assert d["status"] == "unsure" and len(d["alternatives"]) >= 2


def test_not_found_and_smalltalk():
    assert ask("Ertaga Toshkentda havo qanday bo'ladi?")["status"] == "not_found"
    assert ask("salom")["status"] == "smalltalk"


def test_cache():
    ask("Nikoh guvohnomasi yo'qolsa nima qilish kerak")
    assert ask("Nikoh guvohnomasi yo'qolsa nima qilish kerak")["cached"] is True


def test_feedback_returns_alternatives():
    d = ask("Pasportni almashtirish tartibi qanday?")
    r = c.post("/feedback", json={"log_id": d["log_id"], "useful": False}).json()
    assert r["ok"] and all(a["answer_id"] != d["answer_id"] for a in r["alternatives"])


def test_categories():
    cats = c.get("/categories").json()
    assert len(cats) == 9 and sum(x["count"] for x in cats) == 505
    page = c.get("/categories/3", params={"page": 0}).json()
    assert page["items"] and page["pages"] >= 1


def test_admin_requires_token():
    assert c.get("/admin/data").status_code == 403


def need_speech():
    if not c.get("/health").json().get("speech"):
        pytest.skip("ovozni tanish moduli o'rnatilmagan")


def test_voice_question():
    need_speech()
    voice = (Path(__file__).parent / "data" / "fleurs_uz.ogg").read_bytes()     # 6 s, Telegram formatida
    r = c.post("/stt", files={"file": ("voice.ogg", voice, "audio/ogg")})
    assert r.status_code == 200
    text = r.json()["text"].lower()
    assert "gubernator" in text and "politsiya xodimlari" in text


def test_voice_too_large():
    need_speech()
    r = c.post("/stt", files={"file": ("voice.ogg", b"0" * (3 * 1024 * 1024 + 1), "audio/ogg")})
    assert r.status_code == 413
