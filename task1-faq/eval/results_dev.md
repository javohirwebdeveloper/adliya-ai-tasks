# Qidiruv sifati: dev to'plam (tahlil va sozlash uchun)

Real so'rovlar: 205 ta, bazada javobi yo'q so'rovlar: 100 ta.

## Qadamma-qadam

| Qadam | Hit@1 | Hit@3 | MRR |
|---|---|---|---|
| Dense qidiruv (bge-m3) | 74.6% | 86.8% | 0.813 |
| + sparse (leksik) og'irliklar | 74.6% | 87.3% | 0.816 |
| + so'zlashuv so'zlari lug'ati (prava, propiska, ZAGS ...) | 81.0% | 90.7% | 0.861 |
| (sinov, rad etildi) lug'at + qolip so'zlari tozalangan indeks | 78.5% | 87.8% | 0.840 |
| Yakuniy tizim (reranker so'rovlarning 83% ida ishladi) | 86.8% | 90.7% | 0.884 |

Rad etilgan tajriba qatori birinchi o'lchovdan olingan: tajriba indeksi (faq_clean) rad etilgach o'chirilgan, bu qator qaror qoidalariga bog'liq emas.

Holdout (bazadagi savolning o'zi, indeksdan olib tashlangan holda): Hit@1 99.6%, Hit@3 100.0%. Bazadagi savollar bir-biriga juda o'xshash qolip, shuning uchun bu sinov oson.

## Yozilish uslubi bo'yicha (yakuniy tizim)

| Uslub | Soni | Hit@1 | Hit@3 |
|---|---|---|---|
| colloquial | 83 | 91.6% | 94.0% |
| cyrillic | 25 | 92.0% | 92.0% |
| keywords | 26 | 84.6% | 92.3% |
| long | 15 | 73.3% | 80.0% |
| no_apostrophe | 21 | 90.5% | 90.5% |
| russian | 15 | 80.0% | 86.7% |
| typo | 20 | 75.0% | 85.0% |

## Tizim foydalanuvchiga nima qaytaradi

Chegaralar (reranker bali): javob >= 0.25, variantlar >= 0.002 (dev to'plamida tanlangan).

| Natija | Real so'rovlar | Bazada yo'q so'rovlar |
|---|---|---|
| to'g'ri javob berildi | 138 (67.3%) | 0 (0.0%) |
| variantlar ko'rsatildi, to'g'risi ichida | 43 (21.0%) | 0 (0.0%) |
| variantlar ko'rsatildi, to'g'risi yo'q | 12 (5.9%) | 15 (15.0%) |
| noto'g'ri javob berildi | 5 (2.4%) | 0 (0.0%) |
| "topilmadi" deyildi | 7 (3.4%) | 78 (78.0%) |
| salom/rahmat deb javob berildi | 0 (0.0%) | 7 (7.0%) |

### Chegara tanlash jadvali (reranker ishlagan so'rovlar)

| Chegara | Javoblar aniqligi | Darhol to'g'ri javob | Bazada yo'q savollar chegaradan yuqori |
|---|---|---|---|
| 0.002 | 86.5% | 82.8% | 19.1% |
| 0.005 | 88.2% | 82.2% | 14.6% |
| 0.01 | 90.3% | 80.4% | 13.5% |
| 0.02 | 92.0% | 77.9% | 12.4% |
| 0.05 | 93.1% | 74.2% | 5.6% |
| 0.1 | 92.7% | 69.9% | 1.1% |
| 0.2 | 92.7% | 62.6% | 0.0% |
| 0.25 | 95.1% | 59.5% | 0.0% |
| 0.3 | 95.9% | 57.7% | 0.0% |
| 0.4 | 96.6% | 52.8% | 0.0% |
| 0.5 | 96.4% | 49.1% | 0.0% |
| 0.6 | 96.1% | 45.4% | 0.0% |
| 0.7 | 97.1% | 40.5% | 0.0% |
| 0.8 | 96.8% | 36.8% | 0.0% |
| 0.9 | 95.7% | 27.6% | 0.0% |

Tezlik (CPU, kesh siz, bitta so'rov): mediana 2739 ms, o'rtacha 2668 ms, p90 3774 ms.

## Birinchi o'rinda noto'g'ri javob chiqqan so'rovlar

| So'rov | Uslub | To'g'ri javob | Tizim topgani | To'g'risi nechanchi |
|---|---|---|---|---|
| ID karta qildiraman deb DXMga bormoqchiman, o'zim bilan nimalarni olib boray? | colloquial | 2: ID-karta olish uchun qanday hujjatlar kerak? | 287: ID-kartani boshqa shaxs (ishonchnoma bilan) olib bera oladimi? | 2 |
| Qizimni uzatyapmiz, ZAGSda nikohdan o'tishlari uchun nimalarni olib borishlari kerak? | colloquial | 7: Nikohni qayd qilish uchun nima kerak? | 13: Ajrashish uchun FHDYOga qanday hujjatlar kerak? | - |
| Tug'ruqxonadan chiqdik, chaqaloqning guvohnomasini qayerdan olamiz? | colloquial | 10: Tug'ilganlik guvohnomasi qanday olinadi? | 166: Chaqaloq tug'ilgach qanday hujjatlar ketma-ket rasmiylashtiriladi? | 2 |
| id karta almashtirish narxi | keywords | 1: Pasportni (ID-karta) almashtirish tartibi qanday? | 84: Ism yoki familiya o'zgargach ID-kartani almashtirish kerakmi? | 3 |
| Как восстановить утерянное свидетельство о браке? | russian | 36: Nikoh guvohnomasi yo'qolsa dublikat qanday olinadi? | 165: Yo'qolgan hujjat yoki buyum bo'yicha qayerga murojaat qilinadi? | 3 |
| Men 5 yildan beri Koreyada ishlayman, ID kartamning muddati tugab qolyapti. Hozir O'zbekistonga borishga imkonim yo'q. Shu yerdan turib almashtirsam bo'ladimi? | long | 87: Chet elda yashovchi fuqaro pasport/ID-kartani qanday almashtiradi? | 282: ID-karta amal muddati tugaganini qanday bilaman? | 3 |
| Biz faqat nikoh o'qitganmiz, ZAGSda ro'yxatdan o'tmaganmiz. Yaqinda o'g'limiz tug'ildi, turmush o'rtog'im otalikni rasman tan olmoqchi. Buni qanday rasmiylashtirsak bo'ladi? | long | 37: Otalikni belgilash (aniqlash) tartibi qanday? | 17: Farzandlikka olishni rasmiylashtirish uchun nima kerak? | - |
| Toshkentdagi ishlarimni ukam yuritishi uchun unga ishonch qog'ozi yozib bermoqchiman, buni qayerda tasdiqlataman? | colloquial | 45: Ishonchnoma (ishonch xati) qanday rasmiylashtiriladi? | 304: Pul qarzi (tilxat) notarial tasdiqlanadimi? | - |
| Uyimni o'g'limning nomiga sovg'a qilib o'tkazmoqchiman, notariusda nima qilinadi? | colloquial | 100: Ko'chmas mulkni hadya (sovg'a) shartnomasi qanday tuziladi? | 306: Notarius kasal yoki keksa shaxsga uyga chiqib xizmat ko'rsatadimi? | - |
| notarusda bitta hujjat tasdiqlatish necha pul turadi | typo | 205: Notarial harakat uchun qancha to'lov olinadi? | 304: Pul qarzi (tilxat) notarial tasdiqlanadimi? | 3 |
| Отамдан қолган ҳовли ҳали ҳам унинг номида турибди, энди уни менга қандай расмийлаштирса бўлади? | cyrillic | 212: Merosga o'tgan uyni o'z nomiga qanday o'tkaziladi? | 391: Ota-ona vafot etgach bolaning hujjatlarini kim rasmiylashtiradi? | - |
| Как зарегистрировать право собственности на квартиру? | russian | 48: Uy-joyga (ko'chmas mulkka) bo'lgan huquqni davlat ro'yxatidan qanday o'tkaziladi? | 50: Uy oldi-sotdisi (shartnoma) qanday rasmiylashtiriladi? | - |
| 2019-yilda uy sotib olganman, oldi-sotdi shartnomasi notariusda tuzilgan edi. Ko'chib yurganimizda o'sha shartnoma yo'qolib qoldi. Uni qayta tiklab olsam bo'ladimi? | long | 46: Notarial hujjat yo'qolsa nusxasi (dublikat) qanday olinadi? | 499: Uy sotilgach kommunal shartnomalar yangi egaga o'tadimi? | - |
| prava testida nechta xato qilsa yiqilad | typo | 113: Nazariy imtihonda nechta savolga to'g'ri javob berish kerak? | 314: Yo'l qoidasi buzilganda haydovchilik guvohnomasi olib qo'yiladimi? | - |
| mashinani ukamga sovga qilmoqchiman, notariusda nima qilinadi | no_apostrophe | 500: Transport vositasini sovg'a (hadya) qilish qanday rasmiylashtiriladi? | 410: Notarius harakatni rad etsa nima qilinadi? | - |
| instagramda kiyim sotaman, soliq to'lashim shartmi | colloquial | 221: Onlayn (marketpleys orqali) savdo qiluvchi soliqni qanday to'laydi? | 56: Yakka tartibdagi tadbirkor (YaTT) soliqlarni qanday to'laydi? | - |
| firma ochish boji qancha | keywords | 60: Biznesni ro'yxatdan o'tkazish qancha vaqt va boj oladi? | 326: Chet el investori O'zbekistonda firma ocha oladimi? | - |
| my.soliq ga kirolmayapmn, eri kaliti yoq faqat id karta bor shunga krsa boladimi | typo | 223: Soliq to'lovchining shaxsiy kabinetiga qanday kiriladi? | 184: ID-karta sinsa yoki buzilib qolsa nima qilinadi? | - |
| ishsizlik nafaqasi olish uchun qayrga borish kerak | typo | 68: Ishsizlik holatida qanday yordam olish mumkin? | 25: Nafaqa (pensiya) tayinlash uchun qayerga murojaat qilinadi? | 3 |
| da'vo muddati o'tib ketsa | keywords | 466: Da'vo muddati (iskovaya davnost) nima? | 54: Haydovchilik guvohnomasi muddati tugasa yoki yo'qolsa nima qilinadi? | - |
| menga notogri jarima yozishgan, bekor qildirsa boladimi | no_apostrophe | 156: Ma'muriy jarimaga qanday e'tiroz bildiriladi? | 206: Berilgan ishonchnomani bekor qilish mumkinmi? | - |
| Что будет, если уклоняться от призыва в армию? | russian | 353: Harbiy majburiyatni bajarmaslik uchun javobgarlik qanday? | 167: Davlat xizmati rad etilsa nima qilinadi? | - |
| Qo'shnim 2 yil oldin 15 million so'm qarz olgan, tilxati bor. Qaytarmayapti, telefonni ham ko'tarmaydi. Sudga bersam, qancha boj to'lashim kerak bo'ladi? | long | 261: Sud xarajatlari (davlat boji) qanday belgilanadi? | 161: Xizmat uchun to'langan boj qaytariladimi? | - |
| svet bilan gaz pulini telefondan tolasa boladimi qaysi ilovda | typo | 149: Kommunal to'lovlarni qanday onlayn to'lash mumkin? | 151: Elektr, gaz yoki suv uzilishida qayerga qo'ng'iroq qilinadi? | - |
| Биз Германияда турмуш қурганмиз, ўша ердаги никоҳ ҳужжатимиз бу ерда ўтадими? | cyrillic | 267: Chet elda ro'yxatga olingan nikohni O'zbekistonda tan oldirish kerakmi? | 38: Chet el fuqarosi bilan nikoh qanday qayd etiladi? | - |
| telegramda birov aldab pulimni oldi, qayerga yozsam bo'ladi | colloquial | 173: Onlayn firibgarlik (kiber jinoyat)ni qayerga xabar qilinadi? | 163: Korrupsiya yoki pora holatini qayerga xabar berish mumkin? | - |
| elektron imzo olish | keywords | 73: Elektron raqamli imzo (ERI) qanday olinadi? | 375: Elektron imzo bilan hujjatni qanday imzolayman? | 2 |
