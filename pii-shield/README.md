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
| PASPORT | AB4567123, ad-2808399, AA № 123 45 67, AAF 1234567 (texpasport) | 2 harf va 7 raqam, istalgan ajratgich va registrda ("va 1250000 so'm" kabi so'z va summa bundan mustasno) |
| JSHSHIR | 31505901234567 | 14 raqam, ichidagi tug'ilgan sana haqiqiy bo'lishi shart |
| TELEFON | +998 90 123 45 67, 901 234 567, 66 233 45 67, +7 916 123 45 67 | operator va viloyat kodlari, istalgan guruhlash; chet el raqamlari |
| KARTA | 8600 1234 5678 9012 | 16 raqam, Luhn tekshiruvi yoki Uzcard/Humo boshlanishi |
| HISOB, STIR | 20 xonali hisob raqami, 9 xonali STIR | STIR faqat "STIR/INN" so'zi bilan (aks holda telefon bilan adashadi) |
| RAQAM | 12 xonadan uzun boshqa raqam | qoidaga tushmagan uzun raqam ham yashiriladi; pul summasi va yillar bundan mustasno |
| MANZIL | Bunyodkor ko'chasi, 12-uy, 45-xonadon | ko'cha, mahalla, uy, xonadon |
| TUG_SANA | 1990-yil 15-mayda tug'ilgan, дата рождения 15.05.1988 | faqat "tug'ilgan", "родился" so'zlari yonidagi sana |
| EMAIL, TELEGRAM, AVTO, HUJJAT | a@mail.uz, akmal(at)mail.uz, @akmal_k, 01 A 123 BC, 01a123bc, I-TN 0012345 | format bo'yicha |

**Ataylab yashirilmaydiganlar:** viloyat, tuman, shahar (murojaatni yo'naltirish uchun hudud kerak), hujjat sanasi va
raqami, muddatlar, summalar, qaror raqamlari, yolg'iz tug'ilgan yil (pensiya kabi savolda yosh kerak). Bular AI ga
kerak va o'zi yolg'iz hech kimni aniqlab bermaydi.

Kirill matn avval lotinga o'giriladi, har bir harf asl matndagi o'rnini eslab qoladi: bitta qoidalar to'plami lotin,
kirill va rus tilida ishlaydi. Bir xil qiymat har doim bir xil belgi oladi, shuning uchun AI "[ISM_1]" ikki joyda bir
odam ekanini tushunadi.

## Natija

| Sinov | Murojaat | Shaxsiy ma'lumot | Yashirildi |
|---|---|---|---|
| Qo'lda yozilgan (mashq: qoidalar shu yerda yozildi) | 30 | 59 | 100% |
| 1-ko'r test | 63 | 191 | 74.9% |
| 2-ko'r test (1-test xatolari tuzatilgandan keyin yaratilgan) | 89 | 269 | 95.5% |
| **3-ko'r test (2-test xatolari tuzatilgandan keyin yaratilgan)** | 89 | 295 | **95.3%** |

**Yozilish shakllari sinovi** ([eval/stress.py](eval/stress.py), doimiy test): bir xil ma'lumotning odamlar yozadigan
333 ta shakli (katta-kichik harf, defis, nuqta, "№", guruhlangan raqam, kirill, rus, KATTA HARFLI ism, "ugli", qo'shimchalar,
"(at)" bilan email) hammasi yashiriladi; 19 ta murakkab oddiy matnda (summa, qaror raqami, qisqartmalar) ortiqcha 0. Bu
sinov demo'ni sinab ko'rgan odam topgan xatolardan keyin qo'shildi ("ad 4803829", "ad-2808399" ochiq qolgan edi).

**Ortiqcha yashirish** (AI uchun foydali ma'lumot yo'qolmasligi): 1-topshiriqdagi FAQ bazasi va uning barcha sinov
savollarida (4038 ta matn, shaxsiy ma'lumot yo'q) qalqon hech narsa yashirmadi. Bu tekshiruv ikki xatoni topdi va ular
tuzatildi: "Mahallada ko'chaga sahna qurib..." manzil deb, "Yaqinda o'g'li tug'ildi" ism deb olingan edi. Rasmiy xatlarda (2-topshiriq namunalari)
faqat imzo qo'ygan va ijrochining ismi, telefon, email yashirildi: sana, hujjat raqami, muddat va topshiriq matni ochiq.

**Ko'r test qanday qilingan.** Sinov murojaatlarini alohida model (Gemma 4 12B) yozgan: 9 mavzu, 4 uslub (rasmiy ariza,
Telegram xabari, shikoyat, qisqa savol), lotin, kirill va rus tilida. Har murojaat bilan birga Gemma undagi shaxsiy
ma'lumotlar ro'yxatini ham bergan, qalqon shu ro'yxatga qarab tekshirilgan. Har testdan keyin sizib chiqqanlar tahlil
qilindi va **umumiy naqsh** tuzatildi (aniq qiymat emas), keyingi test esa yangi, oldin ko'rilmagan murojaatlarda o'tdi.
Har versiya git tarixida bor: 1-versiya `a7f94f8`, 3-test o'tgan versiya `2023653`. Sinov murojaatlari va Gemma
javoblari: [llm/natija/](llm/natija/).

| Test | Nima sizib chiqdi | Tuzatish |
|---|---|---|
| 1 | "STIR raqamim 784592310" | kalit so'z bilan qiymat orasida 4 tagacha so'z bo'lishi mumkin |
| 1 | 6 xonali pasport (AB987654) | "pasport" so'zi yonida 6-8 raqam ham (odam xato yozishi mumkin) |
| 1 | "улица Амира Темура, дом 45", "дата рождения" | ruscha manzil va tug'ilgan sana |
| 1 | 18-20 xonali karta raqami | 12 xonadan uzun har qanday raqam (pul summasi va yillardan tashqari) |
| 1 | "To'hirxon Karimov**man**" | familiyadan keyingi qo'shimcha: "[ISM_1]man" |
| 2 | "485920137 STIR raqamim", "паспорт серии 4512 № 8903412" | qiymat kalit so'zdan oldin; raqamli pasport seriyasi |
| 2 | "O‘tmonovich", "Menbekov Rustam Omadbek" | apostrofli otasining ismi; o'g'lisiz otasining ismi |
| 2 | "1990.05.15 yili", "тўғилган" | sana shakli; у/ў adashishi |
| 2 | махалля «Озодлик», "15-tor ko'chasi" | qo'shtirnoqdagi nom, raqamli ko'cha |

Qalqonni baholash ([eval/gemma_eval.py](eval/gemma_eval.py)) 1-testdan keyin qotirilgan, keyin o'zgartirilmagan: qiymat matnda
necha marta uchrasa, hammasi tekshiriladi; harf va raqamlarining 90% i yopilgan bo'lsa "yashirildi". Ataylab ochiq
qoladiganlar talab qilinmaydi: manzildagi viloyat, tuman, shahar; karta turi (Humo, Uzcard); yolg'iz tug'ilgan yil.
Gemma ro'yxatga kiritib, matnga yozmagan qiymatlar hisobga olinmaydi. O'lchov qattiq: Gemma qiymatga "15.05.1955 йил"
deb ortiqcha so'z qo'shsa, raqam yashirilgan bo'lsa ham "sizdi" deb hisoblanadi. Shuning uchun har sizish qo'lda ham
ko'rib chiqildi. 2-testdagi 12 sizishdan 2 tasi, 3-testdagi 14 tadan 5 tasi shunday edi: raqam, ko'cha va uy
yashirilgan, ochiq qolgani "йил", "raqami", kelishikdagi hudud nomi ("Ташкенте", "Чиланзарского района") yoki Gemma'ning
"elektron pochta" degan noto'g'ri qiymati. Qo'lda tekshiruv bo'yicha haqiqatan yashirilgani: **2-testda 96.3%, 3-testda 96.9%**.

**Xulosa: qoidalar qayerda to'xtaydi.** Tuzatishlar ishlaydi: 3-testdagi sizishlar orasida 1- va 2-testda tuzatilgan
naqshlar yo'q. Lekin har yangi to'plam yangi noyob naqsh olib keladi ("soliq raqamim", "mahallasida", "по улице",
"уроженец"), shuning uchun qoidalar 96-97% atrofida to'xtaydi. Qolgan uzun dum uchun keyingi qadam: kichik NER modeli
(masalan XLM-R), qalqon va Gemma yordamida avtomatik belgilangan murojaatlarda o'qitiladi va qoidalar bilan birga
ishlaydi (`Shield(model=...)` shu uchun qoldirilgan). 3-testdan keyin topilgan 7 naqsh ham tuzatildi, ular yangi ko'r
test bilan o'lchanmagan.

**Murojaat yordamchisi (Gemma 4, lokal):** murojaat mavzusini, shoshilinchligini aniqlaydi, xodim uchun xulosa va
fuqaroga javob loyihasini yozadi. Asosiy savol: shaxsiy ma'lumot yashirilsa, model murojaatni yomonroq tushunadimi?

| | 2-test | 3-test |
|---|---|---|
| Mavzu to'g'ri: asl matnda | 98.9% | 97.8% |
| Mavzu to'g'ri: yashirilgan matnda | 98.9% | 97.8% |
| Asl va yashirilgan matnda mavzu bir xil | 100% | 100% |
| Shoshilinchlik bir xil | 93.3% | 95.5% |
| Javob fuqaro yozgan tilda | 56.2% | 78.7% |
| O'zidan ism, raqam yoki belgi to'qigan | 0 | 0 |

Mavzu nomida imlo xatosi bo'lsa ("Tadbbirkorlik"), eng yaqin mavzuga moslangan (ishlab chiqarishda ham shunday qilinadi).
Bu va javob tili o'lchovi 2-testdan keyin qo'shilgan.
Mavzular ro'yxati sinov matnlari yaratilgan mavzular bilan bir xil, shuning uchun mavzu aniqlash bu yerda oson vazifa.
Muhim natija boshqa: yashirilgan matnda ham javob asl matndagidek, ya'ni maxfiylik tushunishga xalaqit bermaydi.

2-testda topilgan kamchilik: ruscha murojaatlarning hammasiga o'zbekcha javob yozilgan edi (so'rovda til ko'rsatilmagan).
3-test uchun so'rovga "fuqaro yozgan tilda javob ber" sharti qo'shildi. Natija: ruscha murojaatlarning hammasiga (18/18)
ruscha javob. O'zbek kirilldagilarning esa faqat 8/25 tasiga kirillda javob yozildi (13 tasiga lotinda, 4 tasiga
ruscha). Yechim: javobni lotinda yozdirib, kirillga dastur bilan o'girish (o'girish qat'iy qoida, xato qilmaydi).

Shoshilinchlik farqlari kam (ikki testda jami 10 ta), lekin 8 tasida yashirilgan matn kamroq shoshilinch deb
baholangan: buni ko'proq ma'lumotda tekshirish kerak.

Javob loyihasi xodim ko'rib chiqqandan keyin yuborilishi kerak: ba'zi javoblarda model o'zidan talab yoki idora nomini
qo'shgan ("ГСБДД"), bir marta fuqaroning telefonini qo'llab-quvvatlash xizmati raqami deb yozgan.

Jonli demo'ning «Gemma 4» bo'limida 3-testdagi haqiqiy javoblar bor (lotin, kirill, rus): fuqaro yozgan matn, Gemma
ko'rgan matn, javob va fuqaroga boradigan javob. Namunalar qo'lda tanlangan (til xatosisiz), o'lchovlar esa hamma
murojaat bo'yicha.

## Ishga tushirish

```bash
docker compose up -d --build                  # http://127.0.0.1:8095
python -m pytest tests                        # 14 ta test
python -m eval.evaluate --show                # qo'lda yozilgan to'plam
python -m eval.gemma_eval llm/natija/gemma_items_v3.json   # 3-ko'r test
```

Qalqon tashqi kutubxonasiz ishlaydi (faqat Python standart kutubxonasi), bitta matnni 1-3 ms da tekshiradi, GPU kerak emas.

## Cheklovlar

- Qoidalarga asoslangan va ~97% da to'xtaydi (yuqoriga qarang): ro'yxatda yo'q va ishorasiz yolg'iz ism ("bugun
  Sanjarbek keldi") yoki nostandart tartib ("Fuad Alisher Omonov") to'liq topilmasligi mumkin. Keyingi qadam: ism va
  manzil uchun kichik NER modeli.
- Matnda raqam bilan yozilmagan, so'z bilan aytilgan ma'lumotni ("pasportim a-be bir ikki uch...") topmaydi.
