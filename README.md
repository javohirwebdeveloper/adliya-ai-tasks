# AI muhandisi lavozimi uchun test topshiriqlari

Ikkala topshiriq ham to'liq oflayn ishlaydi: ma'lumot tashqi bulut xizmatlariga yuborilmaydi, GPU shart emas, oddiy server protsessori yetadi.

**Jonli demo:** [javi.uz/adliya](https://javi.uz/adliya/) · Telegram bot: [@javi_faq_bot](https://t.me/javi_faq_bot)

| Topshiriq | Papka | Qisqacha natija |
|---|---|---|
| 1. Semantik qidiruvga asoslangan savol-javob tizimi | [task1-faq](task1-faq) | Alohida yozilgan «ko'r» to'plamda to'g'ri javob 87,5% holatda birinchi o'rinda, 91,7% da javob yoki variant tugmalarida. Bazada yo'q 60 ta savolning birortasiga ham noto'g'ri javob berilmadi. Telegram bot, veb-sahifa, ovozli savol, admin sahifasi |
| 2. Hujjatlarni tahlil qilish (rekvizitlar va topshiriqlar) | [task2-docs](task2-docs) | 12 ta PDF (6 matnli, 6 skaner): rekvizitlar 48/48, topshiriqlar 78/78, ijrochi va muddat ham to'g'ri. Boshqacha formatdagi qo'shimcha hujjatda ham to'g'ri. Skaner 4-9 soniyada tahlil qilinadi |

**Qo'shimcha: [pii-shield](pii-shield), shaxsiy ma'lumot qalqoni.** Test hujjatidagi vazifalardan biri asosida: matn AI
ga yuborilishidan oldin ism, pasport, JSHSHIR, telefon, karta, manzil yashiriladi, javob qaytgach joyiga qo'yiladi
(lotin, kirill, rus; 1-3 ms, GPU kerak emas). Gemma 4 yozgan, oldin ko'rilmagan murojaatlarda uch marta o'lchandi:
74.9% → 95.5% → 95.3% (qo'lda tekshiruvda 96.9%). FAQ bazasining 3553 ta matnida ortiqcha yashirish yo'q. Gemma 4
(lokal) yashirilgan murojaatni asl matndagidek tushundi: mavzu 100% bir xil, o'zidan ism yoki raqam to'qimadi.
Demo: [javi.uz/adliya/qalqon](https://javi.uz/adliya/qalqon/)

**Qo'shimcha: [rag](rag), savol-javob bazasi + qalqon + Gemma 4.** 1-topshiriqdagi qidiruv (R) va Gemma 4 (G)
ulandi: model faqat bazadan topilgan 3 ta manbaga tayanib javob yozadi va manbani ko'rsatadi, fuqaro ma'lumotini qalqon
yashiradi. 1-topshiriqning ko'r to'plamida RAG bilan va RAG'siz Gemma solishtirildi: rasmiy javobga mos javob 27.5% → 75%, rasmiy javobga zid javob
7.5% → 0%, bazada yo'q savolga "javob yo'q" deyish 41.7% → 100%. Topilma: savoldagi salom va shaxsiy ma'lumot
qidiruvni 87.5% dan 75.8% ga tushiradi; yechimi va qolgan cheklovlar [rag/README.md](rag/README.md) da.

Har bir papkadagi README da: topshiriqni qanday tushunganim, tanlangan yondashuv va uning sababi, natijani qanday o'lchaganim, cheklovlar va keyingi qadamlar, ishga tushirish yo'riqnomasi.

## Topshiriqdan tashqari qilinganlar

**Savol-javob:** ovozli savol (o'zbekcha, internetsiz; nutq modeli 5 ta ochiq model ichidan haqiqiy Telegram ovozlarida o'lchab tanlangan, xato 59% dan 25% ga tushdi), bot qaysi savolni tushunganini ko'rsatadi va o'xshash savollarni tugma qilib beradi, qisqa savolda taxmin qilmay aniqlashtiradi, mavzular menyusi, «Foydali / Bu emas» baholari, admin sahifasi va **bot javob topa olmagan savollar ro'yxati** (bazaga qaysi javoblarni qo'shish kerakligini ko'rsatadi), Excel orqali bazani yangilash.

**Hujjat tahlili:** natija hujjatning o'zida ko'rsatiladi (topshiriq bosilsa, qayerdan olingani belgilanadi), Excel'ga yuklab olish, muddatlarni eslatmalar bilan kalendarga qo'shish (.ics), skaner sifati past bo'lsa ogohlantirish.

## Umumiy yondashuv

- **Avval ma'lumotni o'rgandim.** 1-topshiriqda bazadagi savollar qolip bilan yasalganini va 10 juft javob deyarli bir xilligini topdim. 2-topshiriqda hujjatlarning ikki turi (qaror va xat) va topshiriq keladigan to'rt xil joy bor.
- **Har bir g'oyani o'lchab qabul qildim.** Mantiqan to'g'ri ko'ringan ikki g'oya (bazadagi qolip so'zlarini tozalash, ColBERT) o'lchovda foyda bermadi va olib tashlandi. Bu README larda ochiq yozilgan.
- **Natijani halol o'lchadim.** 1-topshiriqda tizim sozlab bo'lingach, alohida yozilgan «ko'r» test to'plamida faqat bir marta o'lchandi. 2-topshiriqda berilgan hujjatlardan tashqari boshqacha formatdagi hujjat ham sinaldi va unda topilgan xatolar ham yozildi.
- **Avtomatik testlar:** 1-topshiriqda 21 ta (ovozli savol bilan), 2-topshiriqda 33 ta, qalqonda 12 ta (`pytest`).
- **Xavfsizlik:** portlar faqat `127.0.0.1` ga ochiladi, tashqariga nginx orqali HTTPS, so'rovlar soni cheklangan, konteynerlar root emas, yuklangan hujjat diskka yozilmaydi, foydalanuvchi ID si jurnalda ochiq saqlanmaydi.

## Tez ishga tushirish

```bash
# 1-topshiriq
cd task1-faq && cp .env.example .env
docker compose up -d postgres qdrant
docker compose run --rm api python -m app.ingest --answers data/answers.csv --questions data/questions.csv
docker compose up -d api bot                     # http://127.0.0.1:8000

# 2-topshiriq
cd task2-docs && docker compose up -d --build    # http://127.0.0.1:8080

# shaxsiy ma'lumot qalqoni
cd pii-shield && docker compose up -d --build    # http://127.0.0.1:8095
```

`tools/loadtest.py`: yuklama sinovi (bir vaqtda N foydalanuvchi).

Muallif: Javohir Jumaboyev
