# Hujjat tahlili: natijalar

Berilgan 6 ta hujjat, har biri matnli va skaner ko'rinishida (12 ta PDF). To'g'ri javoblar `eval/gold.json`.
Qo'shimcha: boshqacha formatdagi buyruq (`eval/synthetic`, `make_synthetic.py` yasaydi): so'z bilan yozilgan sana,
passiv gap, ikki qatorli lavozim, boshqacha jadval sarlavhasi. Birinchi urinishda 6 topshiriqdan 3 tasining ijrochisi
chala chiqqan edi, qoidalar umumlashtirilgach hammasi to'g'ri.

| Turi | Rekvizitlar | Topshiriq topildi (recall) | Ortiqcha (precision) | Ijrochi to'g'ri | Muddat to'g'ri |
|---|---|---|---|---|---|
| Matnli PDF | 100.0% (24/24) | 100.0% (39/39) | 100.0% (39/39) | 100.0% (39/39) | 100.0% (39/39) |
| Skaner (OCR) | 100.0% (24/24) | 100.0% (39/39) | 100.0% (39/39) | 100.0% (39/39) | 100.0% (39/39) |
| Qo'shimcha: boshqa formatdagi buyruq, matnli | 100.0% (4/4) | 100.0% (6/6) | 100.0% (6/6) | 100.0% (6/6) | 100.0% (6/6) |
| Qo'shimcha: boshqa formatdagi buyruq, skaner | 100.0% (4/4) | 100.0% (6/6) | 100.0% (6/6) | 100.0% (6/6) | 100.0% (6/6) |

## Har bir fayl

| Fayl | Rekvizit | Topshiriq | Ortiqcha | Ijrochi | Muddat | OCR ishonchi | Vaqt, s |
|---|---|---|---|---|---|---|---|
| NAMUNA_1_abzats.pdf | 4/4 | 5/5 | 0 | 5/5 | 5/5 | - | 0.7 |
| NAMUNA_1_abzats_skaner.pdf | 4/4 | 5/5 | 0 | 5/5 | 5/5 | 93.9 | 5.5 |
| NAMUNA_2_jadval.pdf | 4/4 | 6/6 | 0 | 6/6 | 6/6 | - | 0.5 |
| NAMUNA_2_jadval_skaner.pdf | 4/4 | 6/6 | 0 | 6/6 | 6/6 | 95.0 | 4.8 |
| NAMUNA_3_ilova.pdf | 4/4 | 6/6 | 0 | 6/6 | 6/6 | - | 0.6 |
| NAMUNA_3_ilova_skaner.pdf | 4/4 | 6/6 | 0 | 6/6 | 6/6 | 94.7, 94.7 | 7.2 |
| xat_1_abzatsdagi_topshiriqlar.pdf | 4/4 | 7/7 | 0 | 7/7 | 7/7 | - | 0.5 |
| xat_1_abzatsdagi_topshiriqlar_skaner.pdf | 4/4 | 7/7 | 0 | 7/7 | 7/7 | 93.5 | 6.1 |
| xat_2_jadvaldagi_topshiriqlar.pdf | 4/4 | 7/7 | 0 | 7/7 | 7/7 | - | 0.4 |
| xat_2_jadvaldagi_topshiriqlar_skaner.pdf | 4/4 | 7/7 | 0 | 7/7 | 7/7 | 92.7 | 6.8 |
| xat_3_ilovadagi_topshiriqlar.pdf | 4/4 | 8/8 | 0 | 8/8 | 8/8 | - | 0.7 |
| xat_3_ilovadagi_topshiriqlar_skaner.pdf | 4/4 | 8/8 | 0 | 8/8 | 8/8 | 81.7, 93.5 | 13.4 |
| buyruq_245.pdf | 4/4 | 6/6 | 0 | 6/6 | 6/6 | - | 2.3 |
| buyruq_245_skaner.pdf | 4/4 | 6/6 | 0 | 6/6 | 6/6 | 95.6 | 8.5 |

## OCR sifati

Skaner matni matnli PDF dagi asl matn bilan solishtirildi (belgilar bo'yicha xato ulushi, CER):

| Hujjat | CER |
|---|---|
| NAMUNA_1_abzats | 0.47% |
| NAMUNA_2_jadval | 0.66% |
| NAMUNA_3_ilova | 0.59% |
| xat_1_abzatsdagi_topshiriqlar | 1.69% |
| xat_2_jadvaldagi_topshiriqlar | 2.04% |
| xat_3_ilovadagi_topshiriqlar | 5.99% |
| buyruq_245 | 0.71% |

## Xatolar

Xato topilmadi.
