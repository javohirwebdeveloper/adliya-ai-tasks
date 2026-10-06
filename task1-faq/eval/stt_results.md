# Ovozli savol: nutqni tanish modellarini solishtirish

Skript: [stt_bench.py](stt_bench.py), raqamlar: [stt_summary.json](stt_summary.json). Hamma model bir xil serverda (12 yadroli protsessor, GPU yo'q), bir xil 6 ta oqim bilan, internetsiz ishladi. Birinchi (isitish) ishga tushirish hisobga olinmagan.

**WER**: 100 ta so'zdan nechtasi xato yozilgani (kam bo'lsa yaxshi). **CER**: xuddi shu, harflar bo'yicha. Solishtirishdan oldin ikkala matn ham kichik harfga o'tkaziladi, apostroflar bir xil qilinadi, tinish belgilari olib tashlanadi, kirill harflari lotinga o'giriladi (qidiruvda ham shunday qilinadi). **3 s ovoz**: botga keladigan odatiy qisqa savol uzunligidagi bo'lakni o'qish vaqti (mediana). **RTF**: o'qish vaqti / ovoz uzunligi.

## Nima uchun

Bot avval Vosk ning kichik o'zbekcha modelini ishlatardi. Sinovda «pravamning muddati tugadi» degan ovozli xabarni u «raqamning muddati tugadi» deb yozdi va bot litsenziya haqidagi javobni berdi.

## 1. Ovozify: haqiqiy Telegram ovozli xabarlari

[OvozifyLabs/asr_evaluate_set](https://huggingface.co/datasets/OvozifyLabs/asr_evaluate_set) (Apache-2.0): ochiq Telegram guruhlaridan olingan 745 ta ovozli xabar, qo'lda yozilgan matni bilan. Shovqin, tez gapirish, ruscha so'zlar aralash. Botga eng yaqin sharoit. Tasodifiy 200 tasi olindi (27 daqiqa, o'rtacha 8,2 s).

| Model | WER % | CER % | 3 s ovoz | RTF | Xotira |
|---|---|---|---|---|---|
| Vosk small uz 0.22 (avvalgi) | 59,1 | 30,0 | 1,02 s | 0,24 | 0,3 GB |
| **GigaAM-Multilingual ctc (tanlandi)** | **25,0** | **8,0** | **0,27 s** | **0,10** | **1,7 GB** |
| GigaAM-Multilingual ctc, int8 | 25,3 | 8,0 | 0,44 s | 0,11 | 0,7 GB |
| GigaAM-Multilingual large_ctc | 23,2 | 7,7 | 0,80 s | 0,22 | 2,6 GB |
| GigaAM-Multilingual large_ctc, int8 | 23,3 | 7,8 | 0,64 s | 0,23 | 1,3 GB |
| NVIDIA FastConformer uz | 54,5 | 29,4 | 0,18 s | 0,04 | 1,3 GB |
| Kotib uzbek_stt_v1 (Whisper-medium) | o'lchanib tugamadi: 27 daqiqalik ovozni 35 daqiqada o'qib tugatolmadi, sinov vaqt chegarasida to'xtatildi | | | > 1 | |

## 2. FLEURS: odamlar o'qigan gaplar

[google/fleurs](https://huggingface.co/datasets/google/fleurs) o'zbekcha test qismi (CC BY 4.0). Har bir gapdan bitta yozuv, tasodifiy 150 tasi (30 daqiqa, o'rtacha 12 s). Toza, tiniq nutq. Matnda 22 ta gapda raqam bor («20 foizi»), GigaAM esa raqamni so'z bilan yozadi («yigirma foizi»), shuning uchun raqamsiz gaplar ustuni ham berilgan.

| Model | WER % | CER % | WER %, raqamsiz gaplar | 3 s ovoz | RTF |
|---|---|---|---|---|---|
| Vosk small uz 0.22 (avvalgi) | 27,4 | 10,0 | 24,1 | 0,87 s | 0,18 |
| **GigaAM-Multilingual ctc (tanlandi)** | **14,5** | **4,3** | **11,7** | **0,26 s** | **0,09** |
| GigaAM-Multilingual ctc, int8 | 14,9 | 4,4 | 12,1 | 0,39 s | 0,10 |
| GigaAM-Multilingual large_ctc | 10,8 | 3,5 | 8,0 | 0,66 s | 0,20 |
| GigaAM-Multilingual large_ctc, int8 | 10,6 | 3,5 | 7,8 | 0,71 s | 0,23 |
| NVIDIA FastConformer uz | 15,1 | 5,2 | 12,8 | 0,17 s | 0,03 |
| Kotib uzbek_stt_v1 (Whisper-medium) | o'lchanmadi: 35 daqiqada 30 daqiqalik ovozni o'qib tugatolmadi, sinov vaqt chegarasida to'xtatildi |

## 3. Botning o'zida: «pravamning muddati tugadi»

Uchta haqiqiy ovozli xabar (shu gap, Telegram'da yozilgan, 7 s dan). Ovozlar shaxsiy bo'lgani uchun repozitoriyga qo'shilmagan.

| Model | So'zma-so'z to'g'ri | Bot to'g'ri javob berdi |
|---|---|---|
| Vosk | 0 / 3 («raqamning...», «radarning...», «prava muddati...») | 2 / 3 |
| GigaAM ctc | 3 / 3 | 3 / 3 |
| GigaAM large_ctc | 3 / 3 | 3 / 3 |
| NVIDIA | 1 / 3 («Pravning...», «Pravaning...») | 2 / 3 |

## Xulosa va tanlov

- **Vosk** haqiqiy Telegram ovozida deyarli har ikki so'zdan birini xato yozadi.
- **NVIDIA** toza nutqda GigaAM bilan teng (15,1 va 14,5), lekin jonli nutqda Vosk darajasiga tushdi (54,5). Faqat FLEURS da o'lchanganda noto'g'ri model tanlangan bo'lardi. Shuning uchun asosiy mezon Ovozify.
- **Kotib** (Whisper asosida) bu protsessorda ikki marta ham real vaqtdan sekin ishladi: 30 daqiqalik ovozni yarim soatdan ko'proq vaqtda ham o'qib tugatolmadi. Whisper har qanday qisqa xabarni ham 30 soniyalik bo'lak sifatida hisoblaydi va matnni so'zma-so'z ketma-ket yasaydi, shuning uchun unga GPU kerak. Mustaqil reytingda uning Ovozify natijasi 22,0 deb e'lon qilingan (biz buni tekshirmadik).
- **GigaAM large** eng aniq, lekin haqiqiy ovozda kichigidan atigi 1,8 punkt yaxshi, 3 barobar sekin va 0,9 GB ko'p xotira oladi.
- **Tanlandi: GigaAM-Multilingual ctc** (220 mln parametr, ONNX, [onnx-asr](https://github.com/istupakov/onnx-asr) orqali, PyTorch kerak emas). Xato Vosk'ka nisbatan 2,4 barobar kam, tezligi 3-4 barobar yuqori.
- int8 ko'rinishi xotirani 2,3 barobar kamaytiradi, aniqlik deyarli o'zgarmaydi, lekin bu protsessorda tezroq emas. Xotira tanqis serverda `STT_QUANT=int8`.

Model `STT_MODEL` sozlamasi bilan almashtiriladi (`app/speech.py`), kod o'zgarmaydi.

## Litsenziyalar

- GigaAM-Multilingual: MIT. Ishlab chiquvchi Sber (Rossiya), u AQSh sanksiya ro'yxatida. Model serverning o'zida ishlaydi va hech qayerga ma'lumot yubormaydi, lekin tashkilot siyosati buni taqiqlasa, muqobil: Kotib (Apache-2.0), lekin u GPU talab qiladi.
- NVIDIA FastConformer: CC BY 4.0. Vosk: Apache-2.0.

## Sinov paytidagi topilmalar

- NVIDIA modelining 8 bitli (int8) fayli bo'sh matn qaytaradi, eksport buzuq.
- Og'irliklari alohida faylda (`.onnx.data`) saqlangan model (GigaAM large) HF keshidan to'g'ridan-to'g'ri ochilmadi: onnxruntime symlink orqali keshning boshqa joyiga ishora qilgan faylni xavfsizlik uchun o'qimaydi. Fayllar bitta papkaga hardlink qilib yig'iladi (`app/speech.py: model_dir`).
- 20 soniyadan uzun ovozli xabar so'z o'rtasidan emas, eng jim joyidan bo'laklarga bo'linadi: modellar 25 soniyagacha bo'lgan gaplarda o'qitilgan.
