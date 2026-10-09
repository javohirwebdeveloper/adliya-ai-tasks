# RAG: savol-javob bazasi + qalqon + Gemma 4

1-topshiriqdagi bot bazadagi tayyor javobni o'zini beradi: savol qanday berilsa ham bir xil matn. RAG'da esa til modeli
bazadan topilgan javoblarni o'qib, aynan shu savolga, fuqaro yozgan tilda javob yozadi. Xavfi ham bor: model o'zidan
to'qishi mumkin (qalqon sinovida Gemma murojaatda yo'q idora nomini o'zidan qo'shgan edi). Shuning uchun bu yerda asosiy savol:
**manbaga bog'langan model o'zidan to'qishni qanchalik kamaytiradi?** Bir xil savollarda RAG bilan va RAG'siz Gemma
solishtirildi.

```
fuqaro savoli: "Men Karimov Akmal, pasportim AB1234567. ID karta olish uchun nima kerak?"
  → qalqon:        "Men [ISM_1], pasportim [PASPORT_1]. ID karta olish uchun nima kerak?"
  → qidirish (R):  1-topshiriq API'si, bge-m3 + Qdrant + reranker: bazadan 3 ta eng yaqin javob
  → Gemma 4 (G):   faqat shu 3 manbaga tayanib yozadi, manbani [1] deb ko'rsatadi, javob bo'lmasa "bazada yo'q"
  → qalqon:        [ISM_1] -> Karimov Akmal
  → fuqaro
```

Gemma hech qachon haqiqiy ism, pasport yoki telefonni ko'rmaydi. Qidirish ham yashirilgan matnda ishlaydi.

Demo: [javi.uz/adliya/qalqon/#rag](https://javi.uz/adliya/qalqon/#rag)

## Natija

Savollar: 1-topshiriqning ko'r to'plami (bazada javobi bor 120 ta, yo'q 60 ta), har biriga to'qima ism, pasport,
telefon qo'shilgan. Ikkala tizim ham aynan bir xil savolni oladi, faqat RAG'ga bazadan topilgan 3 ta manba ham beriladi.

| | RAG'siz Gemma | RAG bilan |
|---|---|---|
| Bazada javobi bor savolga javob yozdi | 99.2% | 81.7% |
| Hakam: rasmiy javobga mos (to'g'ri) | 27.5% | **75.0%** |
| Hakam: qisman (muhim qismi yo'q yoki manbada yo'q da'vo qo'shilgan) | 64.2% | 6.7% |
| Hakam: rasmiy javobga zid (noto'g'ri) | 7.5% | **0%** |
| Bazada javobi yo'q savolga "javob yo'q" dedi | 41.7% | **100%** |
| Javob fuqaro yozgan tilda | 95.8% | 89.8% |
| O'zidan belgi ([ISM_2] kabi) to'qidi | 0 | 0 |

- RAG'siz Gemma deyarli hamma savolga ishonch bilan javob beradi, lekin rasmiy javobga to'liq mosi atigi 27.5%.
  Masalan: "bolamiz yo'q, kelishib ajrashmoqchimiz, ZAGSda bo'ladimi?" savoliga "faqat sud orqali" degan, bazada esa
  FHDYO orqali mumkinligi yozilgan. Raqam aytishdan qochadi, lekin tartib va idorani o'zidan aytadi.
- Bazada javobi yo'q 60 ta savolning 35 tasiga RAG'siz Gemma o'zi bilganidan javob yozdi. RAG hammasida "javob yo'q"
  dedi, fuqaroga botning odatiy "bazada topilmadi" xabari boradi.
- RAG javoblarining 96.9% i to'g'ri manbaga havola qilgan. RAG 22 ta savolga "javob yo'q" degan: 21 tasida qidiruv
  to'g'ri javobni umuman topmagan (to'qish o'rniga rad etgan), 1 tasida esa ortiqcha ehtiyotkorlik qilgan.
- Hakamni qo'lda tekshirdim (19 ta baho): 16 tasida roziman, qolgan 3 tasida hakam yumshoq bo'lgan ("qisman" degan,
  men "noto'g'ri" degan bo'lardim; 1 tasi RAG'siz, 2 tasi RAG javobi).

**Qidirish: shaxsiy ma'lumot qidiruvni yomonlashtiradi.** To'g'ri javob topilgan manbalar orasida bo'lishi:

| So'rov | 1-o'rinda | 3 talikda |
|---|---|---|
| Toza savol (1-topshiriqdagi o'lchov) | 87.5% | 91.7% |
| Shaxsiy ma'lumotli savol, yashirilgan matnning o'zi (Gemma'ga shu manbalar berildi) | 75.8% | 81.7% |
| Shaxsiy ma'lumot gaplarini oddiy qoida bilan olib tashlash (rad etildi) | 74.2% | 79.2% |
| Gemma xabardan qayta yozgan qidiruv savoli (query rewriting) | 81.7% | 87.5% |

"Assalomu alaykum, men [ISM_1]... Telefonim [TELEFON_1]" kabi gaplar savol mazmuniga aloqasiz, lekin qidiruvni
chalg'itadi: masalan "ПИНФЛ [JSHSHIR_1]" so'zi tufayli evakuator haqidagi savolga JSHSHIR haqidagi javoblar topilgan.
Toza savollarning o'zida API natijasi 1-topshiriqdagi o'lchov bilan bittama-bitta bir xil (57 ta savolda 47 ta), ya'ni
pasayish faqat qo'shimcha gaplardan.

Oddiy qoida bilan tozalash yordam bermadi: tinish belgisiz savolda gaplar ajralmaydi va "men", "telefonim" so'zlari
qolib ketadi. Gemma'ning o'zi xabardan toza qidiruv savolini yozsa (query rewriting), yo'qotishning yarmidan ko'pi
tiklanadi. Bu sinovda Gemma javoblari xom so'rov bo'yicha topilgan manbalarda yozilgan, ya'ni jadvaldagi RAG natijasi
qidiruvning yomonroq variantida olingan. Qayta yozilgan so'rov bilan RAG'ni to'liq qayta o'lchash keyingi qadam
(yana bitta GPU ishi).

## Qanday o'lchandi

- **Savollar:** 1-topshiriqning ko'r to'plami: bazada javobi bor 120 ta (har xil uslub: so'zlashuv, kirill, rus, kalit
  so'zlar) va bazada javobi yo'q 60 ta. Bu to'plamda tizim hech qachon sozlanmagan.
- **Shaxsiy ma'lumot:** har savolga to'qima ism, pasport, telefon yoki JSHSHIR qo'shildi ([pii.py](pii.py)), chunki
  fuqaro haqiqatda shunday yozadi. Qalqon ularning hammasini yashirdi (180 tadan 0 sizish).
- **RAG'siz Gemma:** xuddi shu savol, manbasiz. Unga ham "aniq bilmasang, javob yo'q de" deyilgan.
- **Hakam:** bazada bor savollarda javob 1-topshiriqdagi rasmiy javob bilan solishtirildi (hakam ham Gemma 4).
  Hakamning 19 ta bahosi qo'lda tekshirildi (natija yuqorida).
- **Tasdiqsiz raqam:** javobdagi summa, muddat, foiz kabi raqam manbada (RAG) yoki rasmiy javobda (RAG'siz) yo'q.
  Bu "o'zidan to'qish"ning hakamga bog'liq bo'lmagan, avtomatik o'lchovi.

## Ishga tushirish

```bash
python rag/prepare.py          # shu serverda, yengil: qalqon + qidirish (1-topshiriq API'si, POST /retrieve)
modal run rag/modal_rag.py     # GPU (Modal): Gemma 4 RAG bilan, RAG'siz va hakam, ~10 daqiqa, ~$0.35
python rag/qayta_qidirish.py   # shu serverda: Gemma qayta yozgan savollar bilan qidiruv
python rag/evaluate.py         # natija/results.md
```

`prepare.py` serverni band qilmaydi: so'rovlar ketma-ket, orasida pauza, server yuki 12 yadrodan 8 tadan oshsa kutadi.

## Cheklovlar

- Gemma bu sinovda Modal GPU'da ishladi; ishlab chiqarishda o'z serverida (internetsiz) ishlaydi. Qalqon tashqi model
  (masalan bulutdagi kuchliroq LLM) ishlatilganda ham fuqaro ma'lumotini himoya qiladi.
- Hakam ham Gemma 4: o'zini o'zi baholash xolis emas. Ikkala tizimni bir xil hakam baholagani uchun solishtirish adolatli,
  qo'lda tekshiruvda hakam ikkalasiga ham biroz yumshoq chiqdi.
- RAG xatolari: to'g'ri manba topilmasa, ba'zan o'xshash, lekin boshqa manbaga tayanadi (yo'qolgan pravani tiklash
  savoliga yangi prava olish tartibi), yoki manbalarni aralashtiradi (rasmiy javobda 1008, javobda boshqa manbadagi 1148).
- Kirilldagi savolga RAG ko'pincha lotinda javob yozdi (8 tadan 6 tasi), chunki manbalar lotinda. Yechim: javobni
  lotinda yozdirib, kirillga dastur bilan o'girish.
- Bazadagi javoblar qisqa (o'rtacha 133 belgi): RAG ularni savolga moslab qayta aytadi, lekin bazada yo'q tafsilotni
  bera olmaydi. Javob sifati bazaning sifatiga bog'liq.
