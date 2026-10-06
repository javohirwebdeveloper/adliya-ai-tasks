"""Telegram botni boshidan oxirigacha sinash: haqiqiy foydalanuvchi akkauntidan botga yoziladi va har bir javob tekshiriladi.

Sessiya faqat xotirada (StringSession), oxirida akkauntdan chiqiladi. Kirish kodi va 2FA paroli
/dev/shm/tgl/code va /dev/shm/tgl/pw fayllaridan o'qiladi (ekranga chiqarilmaydi).
Telegram API kaliti (my.telegram.org): TG_API_ID va TG_API_HASH muhit o'zgaruvchilari.

  TG_API_ID=... TG_API_HASH=... python tools/bot_e2e.py @javi_faq_bot +998XXXXXXXXX
"""
import asyncio
import os
import re
import sys
import time

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession

D = "/dev/shm/tgl"
BOT, PHONE = sys.argv[1], sys.argv[2]
API_ID = int(os.environ["TG_API_ID"])
API_HASH = os.environ["TG_API_HASH"]
results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok)))
    print(f"{'OK ' if ok else 'XATO'}  {name}" + (f"  ({detail})" if detail and not ok else ""), flush=True)


def buttons(msg):
    return [b.text for row in (msg.buttons or []) for b in row]


async def login():
    client = TelegramClient(StringSession(), API_ID, API_HASH, device_model="Javi server", system_version="Linux",
                            app_version="1.0")
    await client.connect()
    sent = await client.send_code_request(PHONE)
    print("KOD_YUBORILDI", flush=True)
    for _ in range(900):
        if os.path.exists(f"{D}/code"):
            code = re.sub(r"\D", "", open(f"{D}/code").read())
            os.remove(f"{D}/code")
            break
        await asyncio.sleep(1)
    else:
        raise SystemExit("kod kelmadi")
    try:
        await client.sign_in(PHONE, code, phone_code_hash=sent.phone_code_hash)
    except SessionPasswordNeededError:
        await client.sign_in(password=open(f"{D}/pw").read().strip())
    finally:
        if os.path.exists(f"{D}/pw"):
            os.remove(f"{D}/pw")
    return client


async def run(client):
    bot = await client.get_entity(BOT)
    async with client.conversation(bot, timeout=90) as conv:
        await conv.send_message("/start")
        r = await conv.get_response()
        check("/start: salom va mavzular tugmasi", "Assalomu alaykum" in r.raw_text and any("Mavzular" in b for b in buttons(r)))

        await r.click(text=next(b for b in buttons(r) if "Mavzular" in b))
        r = await conv.get_response()
        check("mavzular ro'yxati: 9 ta", "Qaysi mavzu" in r.raw_text and len(buttons(r)) == 9, buttons(r))

        await r.click(2)                                             # Avtomobil va haydovchilik guvohnomasi
        r = await conv.get_edit()
        check("mavzu ichidagi savollar va sahifalash", "(1/" in r.raw_text and any("Keyingi" in b for b in buttons(r)), r.raw_text)
        await r.click(text=next(b for b in buttons(r) if "Keyingi" in b))
        r = await conv.get_edit()
        check("keyingi sahifa", "(2/" in r.raw_text, r.raw_text)
        await r.click(0)
        r = await conv.get_response()
        check("savol bosilganda javob chiqadi", len(r.raw_text) > 40 and "\n" in r.raw_text)

        t0 = time.time()
        await conv.send_message("pravamning muddati tugab qoldi, qayerda almashtiraman")
        r = await conv.get_response()
        check("to'liq savolga javob: sarlavha, baho tugmalari", "Foydali" in " ".join(buttons(r)) and "\n\n" in r.raw_text,
              r.raw_text[:80])
        check("javob vaqti 3 soniyadan kam", time.time() - t0 < 3, f"{time.time() - t0:.1f} s")

        await r.click(text=next(b for b in buttons(r) if "Bu emas" in b))
        r2 = await conv.get_response()
        check("'Bu emas' bosilganda boshqa variantlar", "Kechirasiz" in r2.raw_text, r2.raw_text[:60])
        if buttons(r2) and "Mavzular" not in buttons(r2)[0]:
            await r2.click(0)
            r3 = await conv.get_response()
            check("variant bosilganda javob", len(r3.raw_text) > 30)

        await conv.send_message("prava")
        r = await conv.get_response()
        check("qisqa savol: variantlar so'raladi", "qisqa" in r.raw_text.lower() and len(buttons(r)) >= 3, r.raw_text)

        await conv.send_message("Ertaga Toshkentda havo qanday bo'ladi?")
        r = await conv.get_response()
        check("bazada yo'q savol: topilmadi", "topmadim" in r.raw_text, r.raw_text[:60])

        await conv.send_message("Паспортни қандай алмаштирса бўлади?")
        r = await conv.get_response()
        check("kirillcha savolga javob", "Foydali" in " ".join(buttons(r)) or "tushunmadim" in r.raw_text, r.raw_text[:60])

        await conv.send_message("salom")
        r = await conv.get_response()
        check("salomga javob", "Assalomu alaykum" in r.raw_text)

        await client.send_file(bot, os.getenv("VOICE_FILE", "/tmp/voice_test.ogg"), voice_note=True)
        r = await conv.get_response()
        check("ovozli xabar: eshitgani yoziladi", "Eshitdim" in r.raw_text, r.raw_text)
        r = await conv.get_response()
        check("ovozli savolga javob", len(r.raw_text) > 10)

        await client.send_file(bot, os.path.join(os.path.dirname(__file__), "..", "task2-docs", "docs", "screenshot.png"))
        r = await conv.get_response()
        check("rasm yuborilsa: tushuntirish", "matn yoki ovozli" in r.raw_text, r.raw_text)


async def main():
    client = await login()
    try:
        await run(client)
    finally:
        await client.log_out()
        print("AKKAUNTDAN_CHIQILDI", flush=True)
    ok = sum(1 for _, x in results if x)
    print(f"NATIJA: {ok}/{len(results)}")


asyncio.run(main())
