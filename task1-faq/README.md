# 1-topshiriq. Semantik qidiruvga asoslangan savol-javob tizimi

Fuqaro savolni o'z so'zi bilan yozadi yoki ovozli aytadi: xato bilan, apostrofsiz, kirillda, ruscha yoki «prava», «propiska» kabi so'zlashuv so'zlari bilan. Tizim bazadagi 505 ta javobdan eng mosini topadi. Ikkilansa, «shulardan biri kerakmi?» deb variantlar beradi. Bazada umuman mos javob bo'lmasa, buni ochiq aytadi.

**Sinab ko'rish:** Telegram bot [@javi_faq_bot](https://t.me/javi_faq_bot) va veb-sahifa [javi.uz/adliya/savol-javob](https://javi.uz/adliya/savol-javob/).

Stek: **bge-m3** (embedding), **Qdrant** (vektor baza), **PostgreSQL** (savol-javoblar, jurnal, baholar), **FastAPI**, **aiogram** (Telegram bot). Qo'shimcha: **bge-reranker-v2-m3** (ikkinchi bosqich), **Vosk** (o'zbekcha nutqni tanish, internetsiz).

## Natija qisqacha

Tizim sozlab bo'lingach alohida yozilgan «ko'r» test to'plamida (120 ta real savol va bazada javobi yo'q 60 ta savol) faqat bir marta o'lchandi:

| | Ko'r to'plam | Dev to'plam |
|---|---|---|
| To'g'ri javob birinchi o'rinda (Hit@1) | **87,5%** | 86,8% |
| To'g'ri javob javobning o'zida yoki variant tugmalarida (Hit@3) | **91,7%** | 90,7% |
| Bazada yo'q savolga noto'g'ri javob berildi | **0 / 60** | 0 / 100 |

Ko'r to'plamdagi natija dev bilan deyarli bir xil: tizim dev savollariga moslashib qolmagan.

Foydalanuvchi nimani ko'radi (ko'r to'plam, 120 ta real savol): 63% darhol to'g'ri javob oladi, 23% variantlarni ko'radi va to'g'risi ularning ichida bo'ladi, 1,7% noto'g'ri javob oladi, 5% «topilmadi» degan javob oladi. Bazada yo'q savollarning 75% iga «topilmadi» deyiladi, qolganiga variantlar ko'rsatiladi.

Tezlik (shu server, GPU siz): bitta yangi savol o'rtacha 2,5 soniya, 1-bosqich ishonchli bo'lsa 0,6 soniya, takroriy savol keshdan 10 ms.

## Oddiy foydalanuvchi uchun nima qilindi

Topshiriqda so'ralgan asosiy narsa savolga javob topish. Lekin bot real odamlar uchun, shuning uchun yana quyidagilar qilindi:

- **Bot qaysi savolni tushunganini ko'rsatadi.** Javob ustida sarlavha turadi, masalan «Haydovchilik guvohnomasi muddati tugasa yoki yo'qolsa nima qilinadi?». Odam bot uni to'g'ri tushunganini darhol ko'radi.
- **O'xshash savollar tugma bo'lib chiqadi.** Bot noto'g'ri tushunsa, odam bitta bosish bilan to'g'ri javobni oladi. Faqat haqiqatan yaqin savollar ko'rsatiladi, aloqasiz taklif chiqmaydi.
- **Qisqa savolda taxmin qilinmaydi.** «prava», «muddat», «pasport» kabi bir-ikki so'zli savolga bot bitta javobni tanlab bermaydi, «Qaysi biri haqida so'rayapsiz?» deb variantlarni ko'rsatadi.
- **Ovozli savol.** Telegram'da ovozli xabar yuborish yoki veb-sahifada mikrofon tugmasini bosish mumkin. Nutq serverning o'zida, internetsiz tanib olinadi (Vosk, o'zbekcha model). Bot nima eshitganini ham yozadi: «Eshitdim: ...». Bu yozishga qiynaladigan keksa odamlar uchun qulay.
- **Mavzular menyusi.** Nima so'rashni bilmagan odam 9 ta mavzudan birini tanlab, savollar ro'yxatini varaqlaydi: «Pasport, propiska va FHDYo», «Notarius va meros», «Avtomobil va haydovchilik guvohnomasi» va hokazo.
- **Baho.** Har javob ostida «Foydali» va «Bu emas» tugmalari bor. «Bu emas» bosilsa, bot boshqa variantlarni taklif qiladi. Baho jurnalga yoziladi.
- **Salom va rahmat**ga oddiy odamdek javob beradi, «?» yoki tushunarsiz matnga «topilmadi» deydi.

## Tashkilot uchun nima qilindi

- **Admin sahifasi** (`/admin`, maxfiy kalit bilan): necha savol kelgani, qanchasiga darhol javob berilgani, «Foydali» va «Bu emas» baholari, javob vaqti, ovozli savollar soni.
- **Bot javob topa olmagan savollar ro'yxati.** «Topilmadi» deyilgan yoki foydalanuvchi «Bu emas» degan savollar takrorlanish soni bilan chiqadi. Kontent jamoasi bazaga qaysi javoblarni qo'shish kerakligini shundan biladi. Bot shu tariqa bazani to'ldirish vositasiga aylanadi.
- **Bazani yangilash.** Admin sahifasidan Excel yuklanadi, indeks fonda qayta quriladi, bot shu vaqtda ishlashda davom etadi.
- **So'zlashuv lug'ati** (`data/synonyms.csv`). «prava -> haydovchilik guvohnomasi» kabi juftliklar. Admin oddiy CSV ni to'ldiradi, modelni qayta o'qitish kerak emas.

## 1. Topshiriqni qanday tushundim

- **Ma'lumot.** Excel o'rniga ikkita CSV berilgan (baza eksporti): `answers.csv` (505 javob, 9 kategoriya) va `questions.csv` (3 048 savol, har javobga 6 tadan qolip savol). Yuklagich ikkalasini ham, Excel faylni ham qabul qiladi (ikki varaqli yoki «savol | javob» ko'rinishidagi bitta varaq).
- **Asosiy qiyinchilik.** Bazadagi savollar qolip bilan yasalgan va bir-biriga juda o'xshash, real odamlar esa butunlay boshqacha yozadi. Shuning uchun bazadagi savollarning o'zini qidirib ko'rish sifat haqida deyarli hech narsa demaydi (u yerda Hit@1 100%). Real savollarga o'xshash alohida test to'plami kerak.
- **«Mos javob topilmasa, to'g'ri bildirish».** Bitta chegara yetmaydi. Uch zona qildim: aniq javob, variantlar, «topilmadi». Xato javob berishdan ko'ra variant ko'rsatish yaxshiroq. Variant ko'rsatishdan ko'ra, agar rostdan yo'q bo'lsa, «topilmadi» deyish yaxshiroq.

## 2. Arxitektura

```
Excel / CSV --> ingest --> PostgreSQL (javoblar, savollar, so'rovlar jurnali, baholar)
                                 |
                       bge-m3: dense + sparse vektorlar
                                 |
                       Qdrant (har bir savol va har bir javob matni alohida nuqta)

Ovozli xabar --> ffmpeg --> Vosk (o'zbekcha, internetsiz) --> matn
Savol --> tozalash: apostroflar, salom-rahmat, kirill -> lotin, so'zlashuv lug'ati
      --> 1-bosqich: bge-m3, Qdrant'dan eng yaqin 40 ta matn, ball = dense + 0.3 * sparse,
          javob bo'yicha guruhlash (har javobning eng mos savoli)
      --> kulrang zona: 1-bosqich ishonchli bo'lsa (ball >= 0.8 va ikkinchisidan 0.1 ga oldinda), javob darhol beriladi
      --> aks holda 2-bosqich: reranker eng yaxshi 3 nomzodni savol va javob matni bilan birga o'qib qayta baholaydi
      --> qaror: javob / variantlar / "topilmadi" (+ qisqa savol qoidasi)
      --> kesh (bir xil savol 1 soat davomida darhol qaytadi)
      --> FastAPI --> Telegram bot, veb-sahifa, admin sahifasi
```

- **PostgreSQL** asosiy manba: admin javobni shu yerda o'zgartiradi, so'rovlar jurnali va baholar shu yerda. Qdrant indeksini istalgan payt PostgreSQL dan qayta qurish mumkin.
- **Qdrant'da** har bir savol va har bir javob matni alohida nuqta. Javob matni ham indekslanadi, chunki odam ba'zan javob ichidagi tafsilotni so'raydi («kvitansiya shartmi?»).
- **Bot qidiruvni o'zi qilmaydi**, API ni chaqiradi. Shunda bot ham, veb ham bitta mantiqdan foydalanadi, modellar esa bitta jarayon xotirasida turadi.

## 3. Nega shunday qildim: har bir qadam o'lchangan

Har bir yaxshilash dev to'plamida (205 ta real savol) alohida o'lchandi. Foyda bermaganlari olib tashlandi.

Dev to'plami (205 ta real savol):

| Qadam | Hit@1 | Hit@3 | Qaror |
|---|---|---|---|
| bge-m3, dense qidiruv | 74,6% | 86,8% | asos |
| + sparse (so'zlar og'irligi) | 74,6% | 87,3% | qoldi |
| + so'zlashuv lug'ati | 81,0% | 90,7% | qoldi |
| + bazadagi qolip so'zlarini tozalash | 78,5% | 87,8% | **olib tashlandi** |
| + ColBERT (bge-m3 ning uchinchi rejimi) | +0,5 punkt | +0,5 punkt | **olib tashlandi** |
| + reranker, 3 nomzod, kulrang zona | **86,8%** | **90,7%** | qoldi |

Reranker'ni qanday ishlatish bo'yicha solishtirish (dev, birinchi bosqich nomzodlari bir xil):

| Variant | Hit@1 | Reranker vaqti |
|---|---|---|
| Reranker'siz | 81,5% | 0 |
| 5 nomzod, savol + javob matni | 86,3% | 3,3 s |
| **3 nomzod, savol + javob matni** | **86,8%** | 2,0 s |
| 3 nomzod, faqat savol matni | 79,0% | 1,1 s |
| 3 nomzod + kulrang zona | **86,8%** | o'rtacha 1,6 s |

- **So'zlashuv lug'ati qoldi.** Odamlar «prava», «propiska», «ZAGS», «svet», «bolnichniy», «spravka» deb yozadi, bazada esa rasmiy nomi bor. Lug'at savolga rasmiy nomni qo'shib qo'yadi. Halol izoh: lug'atning bir qismini dev dagi xatolarni ko'rib to'ldirganman. Shuning uchun ko'r to'plamda u 1-bosqichga foyda bermadi (76,7% dan 75,0% ga). Dev dagi +6,4 punktning bir qismi dev ga moslashish ekan. Yakuniy tizim natijasiga bu ta'sir qilmadi.
- **Qolip so'zlarini tozalash olib tashlandi.** Bazadagi savollarning ko'pi «Iltimos, ayting: ...», «... haqida ma'lumot bering» shaklida. Bu so'zlarni olib tashlash mantiqan to'g'ri ko'ringan edi, lekin o'lchov natijani yomonlashtirdi (Hit@1 2,4 punkt pastladi). Shuning uchun savollar bazadagidek indekslanadi.
- **ColBERT (bge-m3 ning uchinchi rejimi) olib tashlandi.** U so'zma-so'z solishtiradi va qo'shimcha model talab qilmaydi. Lekin foydasi 205 ta savoldan bittasiga teng bo'ldi, indeks esa 290 MB ga kattalashadi.
- **Kirill.** Kirillda yozilgan savol lotinga o'giriladi va ikkala variant ham qidiriladi: o'zbekcha kirilni lotin varianti yaxshi topadi, ruscha savolni bge-m3 o'zi tushunadi.
- **Reranker (bge-reranker-v2-m3) qoldi, lekin tejamkor ishlatiladi.** U Hit@1 ni 81,5% dan 86,8% ga ko'tardi, lekin CPU da sekin: bitta nomzodga 0,65 soniya. O'lchovlarda uch narsa chiqdi. Birinchisi: 5 ta emas, 3 ta nomzod berish aniqroq va 40% tezroq. Ikkinchisi: reranker'ga faqat savol matnini berish yaramaydi (Hit@1 79%), javob matni ham kerak. Uchinchisi, kulrang zona: 1-bosqich ishonchli bo'lsa, reranker chaqirilmaydi. Bunda aniqlik o'zgarmadi va bazada yo'q savollardan birortasi ham «ishonchli» deb o'tib ketmadi. GPU bo'lsa, reranker 20-50 ms da ishlaydi va kulrang zonani o'chirish mumkin.
- **«Muddati tugadi» qoidasi.** Sinov paytida «pravamning muddati tugadi» savoliga bot guvohnoma qancha muddatga berilishini aytdi, odam esa uni yangilashni so'rayapti. Lug'atga «muddati tugadi -> muddati tugasa nima qilinadi» qoidasi qo'shildi.

## 4. Sifatni qanday tekshirdim

Uchta to'plam:

| To'plam | Hajmi | Nima uchun |
|---|---|---|
| holdout | 505 | Har javobning bitta savoli indeksdan olib tashlanib, so'rov sifatida beriladi. Oson sinov, bazadagi qoliplar bir-biriga juda o'xshash. |
| dev | 205 savol + 100 ta bazada yo'q savol | Real foydalanuvchi yozadigandek yozilgan. Xatolar shu yerda tahlil qilindi, chegaralar shu yerda tanlandi. |
| final («ko'r») | 120 savol + 60 ta bazada yo'q savol | Tizim sozlab bo'lingach alohida yozildi va faqat bir marta, dev da tanlangan chegaralar bilan o'lchandi. |

Test savollari bazadagi savollarni ko'chirmasdan yozilgan (AI yordamida yozilib, har bir belgi javob matni bilan solishtirib tekshirilgan). Uslublari: so'zlashuv, kalit so'zlar, xatolar bilan, apostrofsiz, kirillda, ruscha, uzun (shaxsiy hikoya bilan). Bir savolga bazada ikki javob ham to'g'ri bo'lsa, ikkinchisi `alt_answer_ids` da ko'rsatilgan.

Metrikalar: **Hit@1** (to'g'ri javob birinchi o'rinda), **Hit@3** (birinchi uchtalikda, ya'ni javob yoki variant tugmalari ichida), **MRR** (to'g'ri javob o'rnining teskarisi bo'yicha o'rtacha).

Natijalar va har bir xato: [eval/results_dev.md](eval/results_dev.md), [eval/results_final.md](eval/results_final.md). Avtomatik testlar: `tests/` (`pytest`).

### Bazadagi ma'lumot sifati bo'yicha topilmalar

- Savollar qolip bilan yasalgan, ba'zilari grammatik jihatdan xato («ID-karta kunda tayyor qanday?»). Real savollarga o'xshamaydi.
- 10 juft javob mazmunan deyarli bir xil (masalan, 380 va 494; 26 va 135; 167 va 490). Ular qidiruvda bir-biri bilan raqobatlashadi. Ro'yxati: [eval/duplicates.md](eval/duplicates.md). Bazani yurituvchi ularni birlashtirishi kerak.

## 5. Tezlik, yuklama va xavfsizlik

Yuklama sinovi (`tools/loadtest.py`, shu server: 12 yadroli protsessor, GPU yo'q, yonida klinika tizimlari ham ishlaydi):

| Holat | So'rov/s | Mediana | p95 | Xato |
|---|---|---|---|---|
| 1 foydalanuvchi, faqat yangi savollar | 0,4 | 2,6 s | 3,6 s | 0 |
| 10 kishi bir vaqtda, to'xtovsiz faqat yangi savollar | 1,3 | 7,8 s | 15 s | 0 |
| 20 kishi, 70% mashhur savollar | 3,5-4 | keshdan 0,1 s | 16 s | 0 |

Chegara protsessorda: ikkita katta model (har biri 568 mln parametr) hisoblanadi. Yangi savollar uchun sig'im sekundiga 1,3 ta, ya'ni soatiga 4 700 ta. Takroriy savollar bunga kirmaydi, ular keshdan chiqadi. Yuklama oshganda tizim yiqilmaydi, sekinlashadi:

- bir vaqtda kelgan savollar paket bo'lib kodlanadi (8 ta savol bitta paketda 3 barobar tejamli);
- reranker band bo'lsa, savol uni kutmaydi va 1-bosqich natijasi bilan javob oladi (10 kishilik sinovda so'rovlarning 72% ida shunday bo'ldi). Bu holatda aniqlik 87% emas 81% bo'ladi, lekin to'g'ri javob baribir variant tugmalarida chiqadi (Hit@3 91%);
- nginx IP bo'yicha, bot esa foydalanuvchi bo'yicha so'rovlar sonini cheklaydi.

Ko'proq yuklama uchun GPU kerak: unda ikkala model 20-50 ms da ishlaydi va sig'im o'nlab barobar oshadi.

Sinov paytidagi topilma: model API ning turli ishchi oqimlarida (thread) ishlaganda 2 barobar sekinlashdi. PyTorch ning protsessor oqimlari guruhi (OpenMP) har bir oqimda alohida yaratilib, bir-biriga xalaqit berar ekan. Barcha hisob bitta doimiy oqimga o'tkazildi, navbatda tez 1-bosqich reranker'dan oldin turadi (`app/embedder.py`).

Xavfsizlik:

- Barcha portlar faqat `127.0.0.1` ga ochiladi. Docker e'lon qilgan portlar firewall qoidalarini chetlab o'tadi, shuning uchun baza va Qdrant tashqi tarmoqqa umuman chiqarilmaydi. Tashqariga faqat nginx orqali HTTPS bilan chiqiladi.
- nginx da so'rovlar soni IP bo'yicha cheklangan. Botda bitta foydalanuvchidan daqiqasiga 15 tadan ortiq xabar qabul qilinmaydi.
- Konteynerlar root huquqida emas, alohida foydalanuvchi nomidan ishlaydi.
- Foydalanuvchi Telegram ID si jurnalda ochiq saqlanmaydi, faqat xeshi.
- Admin sahifasi maxfiy kalit bilan, kalit taqqoslash vaqtga bog'liq hujumga chidamli (`hmac.compare_digest`).
- Savollar va ovozli xabarlar hech qanday tashqi xizmatga yuborilmaydi: modellar serverning o'zida.

## 6. Cheklovlar

- **Tezlik CPU ga bog'liq.** Modellar katta (har biri 568 mln parametr). GPU siz bitta yangi savolga o'rtacha 2,5 soniya ketadi, yuklama ostida undan ko'p (5-bo'lim). GPU bo'lsa, o'n barobardan ko'proq tezlashadi.
- **Reranker ham adashadi.** Masalan, kirillcha «Паспортни қандай алмаштирса бўлади?» savoliga u «chet elda yashovchi fuqaro pasportni qanday almashtiradi» javobini birinchi qo'yadi. To'g'ri javob variant tugmasida chiqadi.
- **Ruscha va uzun savollar** eng zaif joy. Uzun savolda shaxsiy hikoya asosiy savolni «suyultirib» yuboradi.
- **Ovozni tanish** kichik o'zbekcha model bilan, shovqinli yozuvda xato qiladi. Shuning uchun bot nima eshitganini yozib ko'rsatadi.
- **Bazada yo'q, lekin mavzusi yaqin savollar** («ovchilik guvohnomasi» va «tug'ilganlik guvohnomasi») eng qiyin holat. Bunday savollarda tizim ko'pincha variant ko'rsatadi.

## 7. Qanday davom ettirardim

1. **Jurnaldan o'rganish.** Real savollar va «Bu emas» baholari yig'iladi, operator to'g'ri javobni belgilaydi. Shu juftliklar keyingi test to'plami bo'ladi.
2. **Embedding modelini o'qitish.** Real savol va to'g'ri javob juftliklari, qiyin xatolar bilan bge-m3 ni LoRA orqali fine-tuning qilish.
3. **Bazani tozalash.** Takroriy javoblarni birlashtirish, qolip savollar o'rniga real savollar qo'shish, «javobsiz savollar» ro'yxatidan yangi javoblar yozish.
4. **Tezlik.** ONNX Runtime va int8 kvantlash, GPU.

## 8. Ishga tushirish

```bash
cd task1-faq
cp .env.example .env            # BOT_TOKEN, ADMIN_TOKEN, POSTGRES_PASSWORD ni yozing
docker compose up -d postgres qdrant
docker compose run --rm api python -m app.ingest --answers data/answers.csv --questions data/questions.csv
docker compose up -d api bot
# veb-sahifa va API: http://127.0.0.1:8000  (Swagger: /docs), admin: /admin?token=ADMIN_TOKEN
```

Birinchi ishga tushishda bge-m3 modeli yuklab olinadi (2,3 GB). Internetsiz muhitda uni oldindan `HF_CACHE` papkasiga joylab qo'yish kifoya. Ovozli savol uchun o'zbekcha Vosk modelini ([vosk-model-small-uz-0.22](https://alphacephei.com/vosk/models)) yuklab, `VOSK_DIR` da ko'rsating. Indeks qurish CPU da taxminan 15 daqiqa oladi.

Excel fayldan yuklash:

```bash
docker compose run --rm api python -m app.ingest --excel data/faq.xlsx          # "answers" va "questions" varaqlari
docker compose run --rm api python -m app.ingest --excel data/faq.xlsx --flat   # bitta varaq: savol | javob
```

API:

```bash
curl -s http://127.0.0.1:8000/ask -H 'content-type: application/json' \
  -d '{"question": "pravamning muddati tugab qoldi, qayerda almashtiraman"}'
```

```json
{"status": "answered", "answer_id": 54,
 "question": "Haydovchilik guvohnomasi muddati tugasa yoki yo'qolsa nima qilinadi?",
 "answer": "my.gov.uz portali yoki Davlat xizmatlari markazi orqali ...", "score": 0.93,
 "alternatives": [{"answer_id": 109, "question": "Haydovchilik guvohnomasi qancha muddatga beriladi?"}],
 "log_id": 1532, "latency_ms": 2410, "cached": false,
 "timing": {"stage1_ms": 520, "rerank_ms": 1890, "reranked": true, "busy": false}}
```

`status`: `answered` (javob), `unsure` (variantlar `alternatives` da), `not_found` (bazada yo'q), `smalltalk` (salom, rahmat).

Boshqa so'rovlar: `POST /stt` (ovozli fayl -> matn), `POST /feedback`, `GET /answers/{id}`, `GET /categories`, `GET /categories/{id}?page=N`, `GET /health`. Admin: `/admin`, `/admin/data`, `/admin/upload`, `/admin/reindex`.

Baholash: `python -m eval.evaluate --set dev` yoki `--set final` (`RERANK=0` bilan 1-bosqich chegaralari tanlanadi). Reranker variantlarini solishtirish: `python -m eval.dump_scores`, so'ng `python -m eval.analyze`. Testlar: `pytest tests` (13 ta).

## Kod tuzilmasi

| Fayl | Vazifasi |
|---|---|
| `app/ingest.py` | Excel/CSV ni o'qish, tekshirish, PostgreSQL ga yozish, indeksni qurish |
| `app/db.py` | jadvallar sxemasi, so'rovlar jurnali, baholar, statistika |
| `app/normalize.py` | apostroflar, kirill -> lotin, so'zlashuv lug'ati |
| `app/embedder.py`, `app/rerank.py` | bge-m3 va bge-reranker-v2-m3, ularning yagona hisoblash oqimi |
| `app/batching.py` | bir vaqtda kelgan savollarni paketlab kodlash |
| `app/index.py` | Qdrant indeksini qurish |
| `app/search.py` | qidiruv, qaror, qisqa savol qoidasi, kesh |
| `app/api.py`, `app/web.py` | FastAPI, fuqaro va admin sahifalari, ovozni tanish |
| `app/bot.py` | Telegram bot (aiogram): matn, ovoz, tugmalar, mavzular, baho |
| `eval/` | test to'plamlari, baholash va tahlil skriptlari, natijalar |
| `tests/` | avtomatik testlar |
