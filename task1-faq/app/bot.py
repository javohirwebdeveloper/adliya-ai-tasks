"""Telegram bot: matnli va ovozli savollar, variant tugmalari, baho, mavzular menyusi.

Bot qidiruvni o'zi qilmaydi, API ni chaqiradi. Shunda bot ham, veb ham bitta mantiqdan foydalanadi,
modellar esa bitta jarayon xotirasida turadi.
"""
import asyncio
import html
import logging
import time
from collections import defaultdict, deque

import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .config import settings

log = logging.getLogger("bot")
dp = Dispatcher()
http = httpx.AsyncClient(base_url=settings.api_url, timeout=60)

START = ("Assalomu alaykum! Davlat xizmatlari bo'yicha savolingizni o'z so'zingiz bilan yozing yoki ovozli xabar yuboring.\n\n"
         "Masalan: <i>ID-karta olish uchun nima kerak?</i>\n\n"
         "Nima so'rashni bilmasangiz, mavzular ro'yxatidan tanlang.")
NOT_TEXT = "Savolingizni matn yoki ovozli xabar qilib yuboring."
ERROR = "Hozir javob bera olmayapman, birozdan keyin qayta urinib ko'ring."
SLOW_DOWN = "Juda tez yozyapsiz. Bir daqiqadan keyin qayta urinib ko'ring."
LIMIT_PER_MIN = 15
_hits: dict[int, deque] = defaultdict(deque)


def too_fast(user_id: int) -> bool:
    """Bir foydalanuvchidan daqiqasiga 15 tadan ortiq so'rov kelsa, vaqtincha to'xtatiladi (spam va yuklamaga qarshi)."""
    q, now = _hits[user_id], time.time()
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= LIMIT_PER_MIN:
        return True
    q.append(now)
    return False


def short(text: str, n: int = 60) -> str:
    return text if len(text) <= n else text[: n - 1] + "…"


def kb(rows: list[list[tuple[str, str]]]) -> InlineKeyboardMarkup | None:
    rows = [r for r in rows if r]
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t, callback_data=d) for t, d in r] for r in rows]) if rows else None


def alt_rows(items: list[dict]) -> list[list[tuple[str, str]]]:
    return [[(short(a["question"]), f"a:{a['answer_id']}")] for a in items]


TOPICS_BUTTON = [("📚 Mavzular", "t")]


async def reply(m: Message, question: str, voice: bool = False):
    try:
        r = await http.post("/ask", json={"question": question, "channel": "telegram", "user_id": str(m.from_user.id),
                                          "voice": voice})
        r.raise_for_status()
        d = r.json()
    except Exception:
        log.exception("API xatosi")
        await m.answer(ERROR)
        return
    if d["status"] == "answered":
        text = f"<b>{html.escape(d['question'])}</b>\n\n{html.escape(d['answer'])}"
        rows = [[("👍 Foydali", f"f:{d['log_id']}:1"), ("👎 Bu emas", f"f:{d['log_id']}:0")]]
        if d["alternatives"]:
            text += "\n\n<i>O'xshash savollar:</i>"
            rows += alt_rows(d["alternatives"])
        await m.answer(text, reply_markup=kb(rows))
    elif d["status"] == "unsure":
        await m.answer(html.escape(d["message"]), reply_markup=kb(alt_rows(d["alternatives"]) + [TOPICS_BUTTON]))
    elif d["status"] == "not_found":
        await m.answer(html.escape(d["message"]), reply_markup=kb([TOPICS_BUTTON]))
    else:
        await m.answer(html.escape(d["message"]))


@dp.message(CommandStart())
async def start(m: Message):
    await m.answer(START, reply_markup=kb([TOPICS_BUTTON]))


@dp.message(Command("mavzular"))
async def topics_cmd(m: Message):
    await show_topics(m)


@dp.message(F.text)
async def text_question(m: Message):
    if too_fast(m.from_user.id):
        await m.answer(SLOW_DOWN)
        return
    await m.bot.send_chat_action(m.chat.id, "typing")
    await reply(m, m.text)


@dp.message(F.voice | F.audio)
async def voice_question(m: Message):
    if too_fast(m.from_user.id):
        await m.answer(SLOW_DOWN)
        return
    media = m.voice or m.audio
    if media.duration and media.duration > 60:
        await m.answer("Ovozli xabar bir daqiqadan qisqa bo'lsin.")
        return
    await m.bot.send_chat_action(m.chat.id, "typing")
    try:
        f = await m.bot.download(media)
        r = await http.post("/stt", files={"file": ("voice.ogg", f.read(), "audio/ogg")})
        r.raise_for_status()
        text = r.json()["text"]
    except Exception:
        log.exception("STT xatosi")
        await m.answer("Ovozni tanib bo'lmadi, savolni yozib yuboring.")
        return
    if not text:
        await m.answer("Ovozli xabarni tushuna olmadim. Yana bir bor aniqroq aytib ko'ring yoki yozib yuboring.")
        return
    await m.answer(f"🎙 Eshitdim: «{html.escape(text)}»")
    await reply(m, text, voice=True)


@dp.message()
async def other(m: Message):
    await m.answer(NOT_TEXT)


async def show_topics(m: Message):
    r = await http.get("/categories")
    rows = [[(f"{c['name']} ({c['count']})", f"c:{c['id']}:0")] for c in r.json()]
    await m.answer("Qaysi mavzu kerak?", reply_markup=kb(rows))


@dp.callback_query(F.data == "t")
async def topics_cb(c: CallbackQuery):
    await c.answer()
    await show_topics(c.message)


@dp.callback_query(F.data.startswith("c:"))
async def topic_cb(c: CallbackQuery):
    _, cid, page = c.data.split(":")
    r = await http.get(f"/categories/{cid}", params={"page": page})
    await c.answer()
    if r.status_code != 200:
        return
    d = r.json()
    rows = alt_rows(d["items"])
    nav = []
    if d["page"] > 0:
        nav.append(("◀️ Oldingi", f"c:{cid}:{d['page'] - 1}"))
    if d["page"] + 1 < d["pages"]:
        nav.append(("Keyingi ▶️", f"c:{cid}:{d['page'] + 1}"))
    rows.append(nav)
    rows.append([("📚 Barcha mavzular", "t")])
    text = f"<b>{html.escape(d['name'])}</b> ({d['page'] + 1}/{d['pages']})"
    try:
        await c.message.edit_text(text, reply_markup=kb(rows))      # sahifalash xabarni almashtiradi, chatni to'ldirmaydi
    except Exception:
        await c.message.answer(text, reply_markup=kb(rows))


@dp.callback_query(F.data.startswith("a:"))
async def answer_cb(c: CallbackQuery):
    answer_id = int(c.data.split(":", 1)[1])
    r = await http.get(f"/answers/{answer_id}")
    await c.answer()
    if r.status_code == 200:
        d = r.json()
        await c.message.answer(f"<b>{html.escape(d['question'])}</b>\n\n{html.escape(d['answer'])}")
    else:
        await c.message.answer("Bu javob hozir mavjud emas.")


@dp.callback_query(F.data.startswith("f:"))
async def feedback_cb(c: CallbackQuery):
    _, log_id, v = c.data.split(":")
    useful = v == "1"
    try:
        r = await http.post("/feedback", json={"log_id": int(log_id), "useful": useful})
        alts = r.json().get("alternatives", [])
    except Exception:
        alts = []
    try:
        await c.message.edit_reply_markup(reply_markup=None)       # bir marta baholanadi
    except Exception:
        pass
    if useful:
        await c.answer("Rahmat!")
        return
    await c.answer()
    if alts:
        await c.message.answer("Kechirasiz. Balki shulardan biri kerakdir:", reply_markup=kb(alt_rows(alts) + [TOPICS_BUTTON]))
    else:
        await c.message.answer("Kechirasiz. Savolni boshqacharoq yozib ko'ring.", reply_markup=kb([TOPICS_BUTTON]))


async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if not settings.bot_token:
        log.error("BOT_TOKEN berilmagan, bot ishga tushmaydi")
        return
    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode="HTML"))
    await bot.set_my_commands([BotCommand(command="start", description="Boshlash"),
                               BotCommand(command="mavzular", description="Mavzular ro'yxati")])
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
