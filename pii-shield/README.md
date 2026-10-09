# Shaxsiy ma'lumot qalqoni

Matn sun'iy intellektga yuborilishidan oldin undagi shaxsiy ma'lumot yashiriladi, AI javobi qaytgach joyiga qo'yiladi.
AI hech qachon haqiqiy ism, pasport yoki telefon raqamini ko'rmaydi, lekin murojaatning mazmunini to'liq tushunadi.

**Jonli demo:** [javi.uz/adliya/qalqon](https://javi.uz/adliya/qalqon/)

```
"Men Karimov Akmal Rustam o'g'li, pasport AB4567123, tel +998 90 123 45 67. Chilonzor tumani, Bunyodkor ko'chasi, 12-uy."
                                         | qalqon
"Men [ISM_1], pasport [PASPORT_1], tel [TELEFON_1]. Chilonzor tumani, [MANZIL_1]."      -> AI ga shu boradi
                                         | AI javobi: "Hurmatli [ISM_1], arizangiz qabul qilindi..."
"Hurmatli Karimov Akmal Rustam o'g'li, arizangiz qabul qilindi..."                       -> fuqaroga shu boradi
```

## Nima uchun

Test topshirig'idagi hujjatlardan birida shunday vazifa bor edi: «sun'iy intellekt xizmatlariga uzatiladigan ma'lumotlar
tarkibini o'rganib, shaxsga doir va foydalanilishi cheklangan ma'lumotlarni himoya qilish bo'yicha takliflar». Bu prototip
shu vazifaga javob. Undan tashqari, modellarni haqiqiy murojaat va hujjatlarda o'qitish uchun ham shaxsiy ma'lumotni
qonunga muvofiq yashirish kerak: qalqon dataset tayyorlashning birinchi qadami bo'la oladi.

## Nimalarni topadi

| Tur | Misol | Qanday |
|---|---|---|
| ISM | Karimov Akmal Rustam o'g'li, Петрова Анна Сергеевна, A. Yusupov, men Dilshod | otasining ismi, familiya qo'shimchalari, bosh harflar, ismlar ro'yxati va ishora so'zlar |
| PASPORT | AB4567123, AC 2345678, aa 1234567 | 2 harf va 7 raqam; kichik harf faqat "pasport" so'zidan keyin |
| JSHSHIR | 31505901234567 | 14 raqam, ichidagi tug'ilgan sana haqiqiy bo'lishi shart |
| TELEFON | +998 90 123 45 67, 93-555-44-33 | O'zbekiston operator kodlari |
| KARTA | 8600 1234 5678 9012 | 16 raqam, Luhn tekshiruvi yoki Uzcard/Humo boshlanishi |
| HISOB, STIR | 20 xonali hisob raqami, 9 xonali STIR | STIR faqat "STIR/INN" so'zi bilan (aks holda telefon bilan adashadi) |
| RAQAM | 12 xonadan uzun boshqa raqam | qoidaga tushmagan uzun raqam ham yashiriladi; pul summasi va yillar bundan mustasno |
| MANZIL | Bunyodkor ko'chasi, 12-uy, 45-xonadon | ko'cha, mahalla, uy, xonadon |
| TUG_SANA | 1990-yil 15-mayda tug'ilgan, дата рождения 15.05.1988 | faqat "tug'ilgan", "родился" so'zlari yonidagi sana |
| EMAIL, AVTO, HUJJAT | a@mail.uz, 01 A 123 BC, I-TN 0012345 | format bo'yicha |

**Ataylab yashirilmaydiganlar:** viloyat, tuman, shahar (murojaatni yo'naltirish uchun hudud kerak), hujjat sanasi va
raqami, muddatlar, summalar, qaror raqamlari, yolg'iz tug'ilgan yil (pensiya kabi savolda yosh kerak). Bular AI ga
kerak va o'zi yolg'iz hech kimni aniqlab bermaydi.

Kirill matn avval lotinga o'giriladi, har bir harf asl matndagi o'rnini eslab qoladi: bitta qoidalar to'plami lotin,
kirill va rus tilida ishlaydi. Bir xil qiymat har doim bir xil belgi oladi, shuning uchun AI "[ISM_1]" ikki joyda bir
odam ekanini tushunadi.

## Natija

| Sinov | Murojaat | Shaxsiy ma'lumot | Yashirildi |
|---|---|---|---|
| Qo'lda yozilgan (mashq: qoidalar shu yerda yozildi) | 30 | 59 | 100%, ortiqcha 0 |
| Gemma 4, 1-to'plam: birinchi ko'r test | 63 | 191 | 74.9% |
| Gemma 4, 1-to'plam: xatolar tahlilidan keyin (endi ko'rilgan) | 63 | 191 | 99.5% |
| **Gemma 4, 2-to'plam: yangi ko'r test** | V2_N | V2_PII | **V2_PCT** |

Sinov matnlarini qalqon muallifi emas, alohida model (Gemma 4 12B) yozgan: 9 mavzu, 4 uslub (rasmiy ariza, Telegram
xabari, shikoyat, qisqa savol), lotin, kirill va rus tilida. Har murojaat bilan birga Gemma undagi shaxsiy ma'lumotlar
ro'yxatini ham bergan; qalqon shu ro'yxatga qarab tekshirilgan.

**1-to'plamda nima sizib chiqdi va qanday tuzatildi** (aniq qiymat emas, umumiy naqsh tuzatildi):

- "STIR raqamim 784592310": kalit so'z bilan raqam orasida so'z bor edi. Endi 4 tagacha so'z bo'lishi mumkin.
- 6 xonali pasport (AB987654): haqiqiy pasportda 7 raqam, lekin odam xato yozishi mumkin. "pasport" so'zi yonida bo'lsa 6-8 raqam ham yashiriladi.
- Ruscha manzil va sana: "улица Амира Темура, дом 45", "дата рождения", "родился".
- 18-20 xonali karta raqami: endi 12 xonadan uzun har qanday raqam yashiriladi (pul summasi va yillardan tashqari).
- Qo'shimchali familiya: "To'hirxon Karimov**man**", "Karimov**ga**". Qo'shimcha ochiq qoladi: "[ISM_1]ga".

2-to'plam shu tuzatishlardan keyin yaratilgan, men uni oldin ko'rmaganman: asosiy raqam shu.

Baholash qoidalari ([eval/gemma_eval.py](eval/gemma_eval.py)): qiymat matnda necha marta uchrasa, hammasi tekshiriladi;
harf va raqamlarining 90% i yopilgan bo'lsa "yashirildi". Ataylab ochiq qoladiganlar talab qilinmaydi: manzildagi
viloyat, tuman, shahar; karta turi (Humo, Uzcard); yolg'iz tug'ilgan yil. Gemma ro'yxatga kiritib, matnga yozmagan
qiymatlar (V2_ABSENT ta) hisobga olinmaydi.

**Murojaat yordamchisi (Gemma 4, lokal):** murojaat mavzusini, shoshilinchligini aniqlaydi, xulosa va javob loyihasini
yozadi. Asosiy savol: shaxsiy ma'lumot yashirilsa, model murojaatni yomonroq tushunadimi?

ASSISTANT_TABLE

Mavzular ro'yxati sinov matnlari yaratilgan mavzular bilan bir xil, shuning uchun mavzu aniqlash bu yerda oson vazifa.
Muhim natija boshqa: yashirilgan matnda ham javob asl matndagidek, ya'ni maxfiylik tushunishga xalaqit bermaydi.

## Ishga tushirish

```bash
docker compose up -d --build                  # http://127.0.0.1:8095
python -m pytest tests                        # 10 ta test
python -m eval.evaluate --show                # qo'lda yozilgan to'plam
python -m eval.gemma_eval llm/natija/gemma_items_v2.json   # ko'r test
```

Qalqon tashqi kutubxonasiz ishlaydi (faqat Python standart kutubxonasi), bitta matnni 1-3 ms da tekshiradi, GPU kerak emas.

## Cheklovlar

- Qoidalarga asoslangan: ro'yxatda yo'q va ishorasiz yolg'iz ism ("bugun Sanjarbek keldi") topilmasligi mumkin. Keyingi qadam:
  ism va manzil uchun kichik NER modelini haqiqiy (yashirilgan) murojaatlarda o'qitish.
- Matnda raqam bilan yozilmagan, so'z bilan aytilgan ma'lumotni ("pasportim a-be bir ikki uch...") topmaydi.
