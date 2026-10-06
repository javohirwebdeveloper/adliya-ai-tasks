# Qidiruv sifati: dev to'plam (tahlil va sozlash uchun)

Real so'rovlar: 205 ta, bazada javobi yo'q so'rovlar: 100 ta.

## Qadamma-qadam

| Qadam | Hit@1 | Hit@3 | MRR |
|---|---|---|---|
| Dense qidiruv (bge-m3) | 74.6% | 86.8% | 0.813 |
| + sparse (leksik) og'irliklar | 74.6% | 87.3% | 0.816 |
| + so'zlashuv so'zlari lug'ati (prava, propiska, ZAGS ...) | 81.0% | 90.7% | 0.861 |
| Yakuniy tizim (reranker'siz) | 81.0% | 90.7% | 0.855 |

Holdout (bazadagi savolning o'zi, indeksdan olib tashlangan holda): Hit@1 99.6%, Hit@3 100.0%. Bazadagi savollar bir-biriga juda o'xshash qolip, shuning uchun bu sinov oson.

## Yozilish uslubi bo'yicha (yakuniy tizim)

| Uslub | Soni | Hit@1 | Hit@3 |
|---|---|---|---|
| colloquial | 83 | 86.7% | 94.0% |
| cyrillic | 25 | 84.0% | 92.0% |
| keywords | 26 | 76.9% | 92.3% |
| long | 15 | 73.3% | 80.0% |
| no_apostrophe | 21 | 76.2% | 90.5% |
| russian | 15 | 66.7% | 86.7% |
| typo | 20 | 80.0% | 85.0% |

## Tizim foydalanuvchiga nima qaytaradi

Chegaralar (1-bosqich bali): javob >= 0.81, variantlar >= 0.65 (dev to'plamida tanlangan).

| Natija | Real so'rovlar | Bazada yo'q so'rovlar |
|---|---|---|
| to'g'ri javob berildi | 61 (29.8%) | 0 (0.0%) |
| variantlar ko'rsatildi, to'g'risi ichida | 113 (55.1%) | 0 (0.0%) |
| variantlar ko'rsatildi, to'g'risi yo'q | 18 (8.8%) | 16 (16.0%) |
| noto'g'ri javob berildi | 3 (1.5%) | 1 (1.0%) |
| "topilmadi" deyildi | 10 (4.9%) | 76 (76.0%) |
| salom/rahmat deb javob berildi | 0 (0.0%) | 7 (7.0%) |

### Chegara tanlash jadvali (reranker ishlagan so'rovlar)

| Chegara | Javoblar aniqligi | Darhol to'g'ri javob | Bazada yo'q savollar chegaradan yuqori |
|---|---|---|---|
| 0.005 | 81.0% | 81.0% | 100.0% |
| 0.01 | 81.0% | 81.0% | 100.0% |
| 0.02 | 81.0% | 81.0% | 100.0% |
| 0.05 | 81.0% | 81.0% | 100.0% |
| 0.1 | 81.0% | 81.0% | 100.0% |
| 0.2 | 81.0% | 81.0% | 100.0% |
| 0.3 | 81.0% | 81.0% | 100.0% |
| 0.4 | 81.0% | 81.0% | 100.0% |
| 0.5 | 81.0% | 81.0% | 80.9% |
| 0.6 | 81.3% | 80.5% | 42.7% |
| 0.65 | 81.5% | 77.6% | 19.1% |
| 0.7 | 84.7% | 70.2% | 11.2% |
| 0.8 | 94.5% | 33.7% | 1.1% |
| 0.81 | 95.3% | 29.8% | 1.1% |
| 0.9 | 100.0% | 7.3% | 0.0% |

Tezlik (CPU, kesh siz, bitta so'rov): mediana 586 ms, o'rtacha 633 ms, p90 851 ms.

## Birinchi o'rinda noto'g'ri javob chiqqan so'rovlar

| So'rov | Uslub | To'g'ri javob | Tizim topgani | To'g'risi nechanchi |
|---|---|---|---|---|
| ID kartada millatim yozilmagan ekan, bu xato emasmi? | colloquial | 82: ID-kartaga qanday ma'lumotlar yoziladi? | 4: ID-kartada xatolik chiqsa nima qilinadi? | 3 |
| Qizimni uzatyapmiz, ZAGSda nikohdan o'tishlari uchun nimalarni olib borishlari kerak? | colloquial | 7: Nikohni qayd qilish uchun nima kerak? | 13: Ajrashish uchun FHDYOga qanday hujjatlar kerak? | - |
| Opam eri bilan kelishib ajrashmoqchi, bolalari yo'q. Sudga bormasdan ZAGSning o'zida ajrashsa bo'ladimi? | colloquial | 12: Ajrashish (nikohni bekor qilish) qanday amalga oshiriladi? | 291: Nikohdan ajralganlik (ajrim) guvohnomasi qanday olinadi? | 3 |
| Uyimga Turkiyadan do'stim mehmon bo'lib keladi, uni ro'yxatdan o'tkazishim kerakmi? | colloquial | 200: O'zbekistonga tashrif buyurgan chet ellik qancha muddatda ro'yxatga olinishi kerak? | 299: Chet elga uzoq muddatga chiqishda ro'yxatdan chiqish kerakmi? | 3 |
| yo'qolgan tug'ilganlik guvohnomasi dublikat | keywords | 16: Guvohnoma yo'qolsa dublikat qanday olinadi? | 493: Yo'qolgan guvohnoma o'rniga dublikat qancha muddatda beriladi? | 3 |
| bolaga ism qo`yishda taqiqlangan ismlar bormi | no_apostrophe | 39: Chaqaloqqa ism qo'yishda cheklovlar bormi? | 174: Ismni voyaga yetgach mustaqil o'zgartirish mumkinmi? | 2 |
| tugilganlik guvohnomasidagi sana notogri yozilgan, togrilatsa boladimi | no_apostrophe | 392: Guvohnomadagi sana yoki ma'lumotni tuzatish mumkinmi? | 290: Farzandlikka olingan bolaning tug'ilganlik yozuvi o'zgaradimi? | 2 |
| Как восстановить утерянное свидетельство о браке? | russian | 36: Nikoh guvohnomasi yo'qolsa dublikat qanday olinadi? | 165: Yo'qolgan hujjat yoki buyum bo'yicha qayerga murojaat qilinadi? | 3 |
| Men 5 yildan beri Koreyada ishlayman, ID kartamning muddati tugab qolyapti. Hozir O'zbekistonga borishga imkonim yo'q. Shu yerdan turib almashtirsam bo'ladimi? | long | 87: Chet elda yashovchi fuqaro pasport/ID-kartani qanday almashtiradi? | 282: ID-karta amal muddati tugaganini qanday bilaman? | 2 |
| Biz faqat nikoh o'qitganmiz, ZAGSda ro'yxatdan o'tmaganmiz. Yaqinda o'g'limiz tug'ildi, turmush o'rtog'im otalikni rasman tan olmoqchi. Buni qanday rasmiylashtirsak bo'ladi? | long | 37: Otalikni belgilash (aniqlash) tartibi qanday? | 17: Farzandlikka olishni rasmiylashtirish uchun nima kerak? | - |
| Toshkentdagi ishlarimni ukam yuritishi uchun unga ishonch qog'ozi yozib bermoqchiman, buni qayerda tasdiqlataman? | colloquial | 45: Ishonchnoma (ishonch xati) qanday rasmiylashtiriladi? | 409: Ishonchnoma muddati qancha bo'lishi mumkin? | - |
| Uyimni o'g'limning nomiga sovg'a qilib o'tkazmoqchiman, notariusda nima qilinadi? | colloquial | 100: Ko'chmas mulkni hadya (sovg'a) shartnomasi qanday tuziladi? | 306: Notarius kasal yoki keksa shaxsga uyga chiqib xizmat ko'rsatadimi? | - |
| uy hujjatlarim qolmagan, kadastr nomerini internetdan topsa boladimi | no_apostrophe | 210: Ko'chmas mulkning kadastr raqamini qayerdan bilib olish mumkin? | 49: Ko'chmas mulk bo'yicha kadastr ko'chirmasi (ma'lumotnoma) qanday olinadi? | 2 |
| Отамдан қолган ҳовли ҳали ҳам унинг номида турибди, энди уни менга қандай расмийлаштирса бўлади? | cyrillic | 212: Merosga o'tgan uyni o'z nomiga qanday o'tkaziladi? | 170: Vasiylik yoki homiylik qanday rasmiylashtiriladi? | - |
| Как зарегистрировать право собственности на квартиру? | russian | 48: Uy-joyga (ko'chmas mulkka) bo'lgan huquqni davlat ro'yxatidan qanday o'tkaziladi? | 107: Bino yoki xonadonni ijaraga berish shartnomasini ro'yxatdan o'tkazish kerakmi? | - |
| 2019-yilda uy sotib olganman, oldi-sotdi shartnomasi notariusda tuzilgan edi. Ko'chib yurganimizda o'sha shartnoma yo'qolib qoldi. Uni qayta tiklab olsam bo'ladimi? | long | 46: Notarial hujjat yo'qolsa nusxasi (dublikat) qanday olinadi? | 499: Uy sotilgach kommunal shartnomalar yangi egaga o'tadimi? | - |
| prava testida nechta xato qilsa yiqilad | typo | 113: Nazariy imtihonda nechta savolga to'g'ri javob berish kerak? | 314: Yo'l qoidasi buzilganda haydovchilik guvohnomasi olib qo'yiladimi? | - |
| mashinani ukamga sovga qilmoqchiman, notariusda nima qilinadi | no_apostrophe | 500: Transport vositasini sovg'a (hadya) qilish qanday rasmiylashtiriladi? | 306: Notarius kasal yoki keksa shaxsga uyga chiqib xizmat ko'rsatadimi? | - |
| Как оформить ОСАГО на машину? | russian | 315: Majburiy avtosug'urta (fuqarolik javobgarligi) qanday rasmiylashtiriladi? | 53: Avtomobil oldi-sotdi shartnomasini rasmiylashtirish tartibi qanday? | 3 |
| Uy solig'i bo'yicha xabarnoma keldi, summasi qanday hisoblanganini tushunmadim | colloquial | 117: Mol-mulk (uy, yer) solig'i qanday hisoblanadi va to'lanadi? | 411: Uy-joyni sovg'a (hadya) qilishda soliq yoki boj bormi? | 3 |
| instagramda kiyim sotaman, soliq to'lashim shartmi | colloquial | 221: Onlayn (marketpleys orqali) savdo qiluvchi soliqni qanday to'laydi? | 56: Yakka tartibdagi tadbirkor (YaTT) soliqlarni qanday to'laydi? | 4 |
| firma ochish boji qancha | keywords | 60: Biznesni ro'yxatdan o'tkazish qancha vaqt va boj oladi? | 326: Chet el investori O'zbekistonda firma ocha oladimi? | - |
| my.soliq ga kirolmayapmn, eri kaliti yoq faqat id karta bor shunga krsa boladimi | typo | 223: Soliq to'lovchining shaxsiy kabinetiga qanday kiriladi? | 184: ID-karta sinsa yoki buzilib qolsa nima qilinadi? | - |
| tug'ruq ta'tili puli | keywords | 232: Homiladorlik va tug'ruq ta'tili qanday rasmiylashtiriladi? | 243: Tug'ruqxonani tanlash mumkinmi? | 2 |
| nogironlik guruhi olish uchun komissiya | keywords | 237: Nogironlik guruhini qanday rasmiylashtiriladi? | 405: Nogironlik guruhini tasdiqlovchi ma'lumotnoma qayerdan olinadi? | 2 |
| ishsizlik nafaqasi olish uchun qayrga borish kerak | typo | 68: Ishsizlik holatida qanday yordam olish mumkin? | 25: Nafaqa (pensiya) tayinlash uchun qayerga murojaat qilinadi? | 3 |
| da'vo muddati o'tib ketsa | keywords | 466: Da'vo muddati (iskovaya davnost) nima? | 195: Vaqtincha ro'yxatga olish muddati tugasa nima qilinadi? | 5 |
| menga notogri jarima yozishgan, bekor qildirsa boladimi | no_apostrophe | 156: Ma'muriy jarimaga qanday e'tiroz bildiriladi? | 94: Xorijga chiqishga qo'yilgan taqiqni qanday tekshirish va bekor qilish mumkin? | - |
| Что будет, если уклоняться от призыва в армию? | russian | 353: Harbiy majburiyatni bajarmaslik uchun javobgarlik qanday? | 167: Davlat xizmati rad etilsa nima qilinadi? | 4 |
| Qo'shnim 2 yil oldin 15 million so'm qarz olgan, tilxati bor. Qaytarmayapti, telefonni ham ko'tarmaydi. Sudga bersam, qancha boj to'lashim kerak bo'ladi? | long | 261: Sud xarajatlari (davlat boji) qanday belgilanadi? | 161: Xizmat uchun to'langan boj qaytariladimi? | - |
| Chiqindi mashinasi 2 haftadan beri kelmayapti, kimga shikoyat qilsam bo'ladi? | colloquial | 260: Chiqindini olib chiqish (maishiy chiqindi) xizmatidan norozi bo'lsam qayerga? | 369: Yo'qolgan yoki shikastlangan pochta jo'natmasi bo'yicha shikoyat qayerga? | 2 |
| svet bilan gaz pulini telefondan tolasa boladimi qaysi ilovda | typo | 149: Kommunal to'lovlarni qanday onlayn to'lash mumkin? | 151: Elektr, gaz yoki suv uzilishida qayerga qo'ng'iroq qilinadi? | - |
| Уйни сотдим, газ ва свет ҳисобини янги эгасига қандай ўтказамиз? | cyrillic | 499: Uy sotilgach kommunal shartnomalar yangi egaga o'tadimi? | 258: Uyni gazlashtirish (yangi ulanish) qanday rasmiylashtiriladi? | 2 |
| Биз Германияда турмуш қурганмиз, ўша ердаги никоҳ ҳужжатимиз бу ерда ўтадими? | cyrillic | 267: Chet elda ro'yxatga olingan nikohni O'zbekistonda tan oldirish kerakmi? | 38: Chet el fuqarosi bilan nikoh qanday qayd etiladi? | - |
| my.gov.uz ga qanday kiraman, menda ERI yo'q | colloquial | 72: my.gov.uz portaliga qanday ro'yxatdan o'tiladi yoki kiriladi? | 503: Elektron raqamli imzo (ERI) kalitini yo'qotsam nima qilaman? | 3 |
| telegramda birov aldab pulimni oldi, qayerga yozsam bo'ladi | colloquial | 173: Onlayn firibgarlik (kiber jinoyat)ni qayerga xabar qilinadi? | 378: Yo'qolgan yoki o'g'irlangan telefon (IMEI) bo'yicha qayerga murojaat? | - |
| elektron imzo olish | keywords | 73: Elektron raqamli imzo (ERI) qanday olinadi? | 375: Elektron imzo bilan hujjatni qanday imzolayman? | 2 |
| Электрон справкадаги QR кодни қандай текширса бўлади, ҳақиқийлигини билмоқчиман | cyrillic | 274: Elektron hujjatning (PDF) haqiqiyligini qanday tekshiriladi? | 426: Kassa cheki (QR-kod) haqiqiyligini qanday tekshiriladi? | 2 |
| Как узнать статус моей заявки на my.gov.uz? | russian | 75: Ariza (davlat xizmati) holatini qanday kuzatish mumkin? | 72: my.gov.uz portaliga qanday ro'yxatdan o'tiladi yoki kiriladi? | 2 |

## Bazada yo'q, lekin javob berilgan savollar

| So'rov | Tizim topgani |
|---|---|
| Ovchilik guvohnomasini qayerdan olsam bo'ladi? | Tug'ilganlik guvohnomasi qanday olinadi? |
