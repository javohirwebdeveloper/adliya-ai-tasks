# Qidiruv sifati: yakuniy ko'r to'plam (bir marta o'lchandi)

Real so'rovlar: 120 ta, bazada javobi yo'q so'rovlar: 60 ta.

## Qadamma-qadam

| Qadam | Hit@1 | Hit@3 | MRR |
|---|---|---|---|
| Dense qidiruv (bge-m3) | 77.5% | 91.7% | 0.850 |
| + sparse (leksik) og'irliklar | 76.7% | 93.3% | 0.848 |
| + so'zlashuv so'zlari lug'ati (prava, propiska, ZAGS ...) | 75.0% | 91.7% | 0.839 |
| (sinov, rad etildi) lug'at + qolip so'zlari tozalangan indeks | 72.5% | 92.5% | 0.831 |
| Yakuniy tizim (reranker so'rovlarning 87% ida ishladi) | 87.5% | 91.7% | 0.894 |

## Yozilish uslubi bo'yicha (yakuniy tizim)

| Uslub | Soni | Hit@1 | Hit@3 |
|---|---|---|---|
| colloquial | 45 | 84.4% | 91.1% |
| cyrillic | 15 | 86.7% | 93.3% |
| keywords | 15 | 93.3% | 93.3% |
| long | 7 | 100.0% | 100.0% |
| no_apostrophe | 15 | 73.3% | 80.0% |
| russian | 8 | 87.5% | 87.5% |
| typo | 15 | 100.0% | 100.0% |

## Tizim foydalanuvchiga nima qaytaradi

Reranker chegaralari: javob >= 0.25, variantlar >= 0.002 (dev to'plamida tanlangan).

| Natija | Real so'rovlar | Bazada yo'q so'rovlar |
|---|---|---|
| to'g'ri javob berildi | 76 (63.3%) | 0 (0.0%) |
| variantlar ko'rsatildi, to'g'risi ichida | 28 (23.3%) | 0 (0.0%) |
| variantlar ko'rsatildi, to'g'risi yo'q | 8 (6.7%) | 14 (23.3%) |
| noto'g'ri javob berildi | 2 (1.7%) | 0 (0.0%) |
| "topilmadi" deyildi | 6 (5.0%) | 45 (75.0%) |
| salom/rahmat deb javob berildi | 0 (0.0%) | 1 (1.7%) |

Tezlik (CPU, kesh siz, bitta so'rov): mediana 2439 ms, o'rtacha 2502 ms, p90 3440 ms.

## Birinchi o'rinda noto'g'ri javob chiqqan so'rovlar

| So'rov | Uslub | To'g'ri javob | Tizim topgani | To'g'risi nechanchi |
|---|---|---|---|---|
| Хочу купить квартиру на имя сына, ему 10 лет. Как правильно оформить такую сделку? | russian | 305: Voyaga yetmagan bola nomiga bitim qanday tuziladi? | 107: Bino yoki xonadonni ijaraga berish shartnomasini ro'yxatdan o'tkazish kerakmi? | - |
| Akamning mashinasini u yo'qligida minib yursam, yonimda qanday hujjat bo'lishi kerak? | colloquial | 317: Avtomobilni boshqarish uchun ishonchnoma kerakmi? | 422: Transport vositasini xorijga olib chiqish uchun nima kerak? | - |
| Sobiq erim bilan ajrashganmiz. Bolani o'zimning uyimga propiska qilmoqchiman, lekin u rozilik bermayapti. Usiz qilsa bo'ladimi? | colloquial | 395: Bolani ikkinchi ota-ona roziligisiz ro'yxatga olish mumkinmi? | 295: Uy egasi ro'yxatga olishga rozilik bermasa nima qilinadi? | 2 |
| har safar bir xil spravkalarni yigib yurishim kerakmi yoki idoralar ozlari bir birlaridan olishadimi | no_apostrophe | 373: Bir arizada kerakli ma'lumotni idoralar o'zi olib beradimi? | 137: Tibbiy ma'lumotnoma (spravka) qanday olinadi? | 2 |
| Bolam tugilganiga 2 oy boldi, hali ZAGSda royxatdan otkazmadik. Muddati otib ketmadimi? | no_apostrophe | 11: Tug'ilishni qayd etish muddati qancha? | 190: Egizaklar tug'ilganda ro'yxatga olish qanday amalga oshiriladi? | - |
| Erim vafot etdi, ikki kichkina farzandim bor. Bolalarga otasi uchun pensiya tayinlanadimi? | colloquial | 132: Boquvchisini yo'qotganlik pensiyasi kimga beriladi? | 131: Nogironlik pensiyasi qanday tayinlanadi? | - |
| Otamdan qolgan hovli hali ham uning nomida turibdi. Uni o'zimga qanday qilib rasmiylashtirsam bo'ladi? | colloquial | 212: Merosga o'tgan uyni o'z nomiga qanday o'tkaziladi? | 391: Ota-ona vafot etgach bolaning hujjatlarini kim rasmiylashtiradi? | - |
| Oyligim haqida spravka kerak edi, buni faqat ishxonadan olamanmi yoki mygovdan ham chiqarsa boladimi | no_apostrophe | 201: Daromad yoki ish haqi haqidagi ma'lumotnoma qanday olinadi? | 137: Tibbiy ma'lumotnoma (spravka) qanday olinadi? | - |
| YaTT faoliyatimni butunlay yopmoqchiman, nimadan boshlashim kerak? | colloquial | 122: Tadbirkorlik faoliyatini tugatish (yopish) tartibi qanday? | 120: Yakka tartibdagi tadbirkor (YaTT) qanday ro'yxatdan o'tadi? | - |
| Eski mashinamni utilizatsiyaga topshirib, uchyotdan butunlay chiqarmoqchiman. Qayerga murojaat qilaman? | colloquial | 177: Transport vositasini hisobdan chiqarish (utilizatsiya) tartibi qanday? | 260: Chiqindini olib chiqish (maishiy chiqindi) xizmatidan norozi bo'lsam qayerga? | 2 |
| ikkinchi nikoh ZAGS hujjatlar ajrim guvohnomasi | keywords | 388: Takroriy (ikkinchi marta) nikoh qanday qayd etiladi? | 291: Nikohdan ajralganlik (ajrim) guvohnomasi qanday olinadi? | - |
| pravam yoqolib qoldi, qanday qilib tiklasam boladi | no_apostrophe | 54: Haydovchilik guvohnomasi muddati tugasa yoki yo'qolsa nima qilinadi? | 23: Haydovchilik guvohnomasini qanday rasmiylashtirish mumkin? | - |
| Uch oydan beri oylik berishmayapti. Qayerga arz qilsam bo'ladi? | colloquial | 126: Ish haqi kechiktirilsa yoki berilmasa qayerga murojaat qilinadi? | 443: Nafaqa to'lovi to'xtab qolsa qayerga murojaat qilaman? | 3 |
| Ҳокимиятдан келган жавоб мени қониқтирмади. Яна қаерга ёзсам бўлади? | cyrillic | 484: Murojaat javobini qayta ko'rib chiqishni so'rash mumkinmi? | 31: Murojaat yoki shikoyatni qayerga topshirish mumkin? | - |
| Ҳокимликка интернет орқали ариза ёзиб юборса бўладими? | cyrillic | 483: Davlat organiga elektron murojaat qanday yuboriladi? | 153: Sudga da'vo arizasi qanday topshiriladi? | 2 |
