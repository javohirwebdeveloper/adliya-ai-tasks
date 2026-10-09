# Model o'qitish (fine-tuning)

Tayyor model hamma narsani biladi, lekin bizning vazifamizni aniq bajarishni bilmaydi. Fine-tuning: modelga o'z
misollarimizni ko'rsatib, aynan shu vazifaga o'rgatish. Bu yerda ikki mashq bor, ikkalasi ham bir xil tartibda
qilingan: avval o'qitishdan **oldin** o'lchanadi, keyin o'qitiladi, keyin **o'sha** testda qayta o'lchanadi.

**Jonli demo:** [javi.uz/adliya/trening](https://javi.uz/adliya/trening/). Bitta gapga o'qitishdan oldingi va keyingi
model yonma-yon javob beradi.

## 2. QLoRA: topshiriq gapidan ijrochi va muddat ([2-qlora](2-qlora))

2-topshiriqdagi vazifaning bir qismi: rasmiy xatdagi topshiriq gapidan kim bajarishini va qachongacha ekanini ajratish.

```
Gap:    "Hududiy adliya boshqarmalari ushbu buyruq ijrosini 2026-yil 25-dekabrgacha Ijro nazorati bo'limiga taqdim etsin."
Javob:  {"ijrochi": ["Hududiy adliya boshqarmalari"], "muddat": "2026-yil 25-dekabrgacha", "muddat_turi": "sana"}
```

| Test | O'qitishdan oldin | O'qitishdan keyin |
|---|---|---|
| Haqiqiy hujjatlardagi 13 ta gap (2-topshiriq namunalari) | 31% | **100%** |
| 150 ta sun'iy gap, o'qitishda bo'lmagan yangi nomlar bilan | 21% | **94%** |

"To'g'ri" degani: ijrochi, muddat va muddat turi uchalasi ham to'g'ri. O'qitilmagan model ko'pincha ijrochini topmaydi
yoki hujjat kimga yuborilishini ("Ijro nazorati bo'limiga") ijrochi deb oladi.

- **Model:** Qwen3-4B-Instruct (4 mlrd parametr), ochiq model.
- **QLoRA:** model 4 bitga siqib yuklanadi (xotirada ~3 GB) va muzlatiladi; unga kichik qo'shimcha qatlamlar (LoRA,
  33 mln parametr, jami 1.5%) qo'shilib, faqat ular o'qitiladi. Natija 126 MB lik "adapter" fayli.
- **Ma'lumot:** 1600 ta sun'iy misol ([make_data.py](2-qlora/make_data.py)): idora nomlari, muddat shakllari va gap
  qoliplari aralashtirib yasalgan. Xato faqat javob qismida hisoblanadi: model savolni yodlamaydi, javob yozishni o'rganadi.
- **O'qitish:** 1 epoch, bitta L4 GPU'da (Modal) 10.4 daqiqa, ~$0.24. Birinchi urinish xotiraga sig'madi (OOM);
  gradient checkpointing va kichikroq batch bilan hal qilindi.

**Halol cheklovlar:** haqiqiy test kichik (13 ta gap). Sun'iy ma'lumot haqiqiy gaplarning tuzilishini ko'rib yozilgan
(nomlar boshqa), shuning uchun 100% optimistik raqam; ishonchli baho uchun ko'proq haqiqiy hujjat kerak. Model faqat
lotin yozuvidagi gaplarda o'qitilgan.

## 1. LoRA: savolni mavzuga ajratish ([1-tasniflagich](1-tasniflagich))

1-topshiriq bazasidagi savollar bilan XLM-RoBERTa modeli 9 ta mavzuga ajratishga o'rgatildi.

| Ko'r test (alohida yozilgan 325 ta savol) | Aniqlik |
|---|---|
| Eng ko'p uchraydigan mavzuni aytish | 24.3% |
| Model muzlatilgan, ustiga oddiy tasniflagich | 41.8% |
| LoRA bilan o'qitilgan (1 mln parametr, 0.4%) | **70.2%** |

Saboq: tekshirish to'plamida 98% chiqdi, ko'r testda esa 70%. Bazadagi savollar qolip bilan ko'paytirilgani uchun
model qolipga moslashib qolgan. O'qitish ma'lumoti haqiqiy savollarga o'xshash bo'lishi kerak.

## Ishga tushirish

```bash
cd 2-qlora
python make_data.py                      # sun'iy ma'lumot -> data/
modal run modal_qlora.py                 # o'qitish (Modal L4 GPU) -> natija/, natija/adapter/
TRENING_TOKEN=... modal deploy modal_demo.py   # demo uchun GPU endpoint (5 daqiqa ishlatilmasa o'chadi)
cd ../demo && docker compose up -d --build     # sahifa: http://127.0.0.1:8097 (.env: MODAL_URL, TRENING_TOKEN)
```

Adapter fayli (126 MB) git'da yo'q: `modal run modal_qlora.py` uni `natija/adapter/` ga yozadi.
