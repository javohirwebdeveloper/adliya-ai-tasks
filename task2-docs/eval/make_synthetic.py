"""Boshqacha formatdagi sinov hujjati: buyruq, so'z bilan yozilgan sana, "tomonidan" gap, ikki qatorli
lavozim, boshqacha jadval sarlavhasi. Matnli PDF va undan "skaner" (150 dpi, qiyshiq, shovqinli) yasaladi.

  python eval/make_synthetic.py
"""
from pathlib import Path

import numpy as np
import pymupdf

OUT = Path(__file__).parent / "synthetic"
HTML = """
<div style="font-family: serif; font-size: 12.5pt; line-height: 1.45">
<p style="text-align:center; font-weight:bold; margin:0">O'ZBEKISTON RESPUBLIKASI ADLIYA VAZIRLIGI<br>HUZURIDAGI HUQUQIY AXBOROT MARKAZINING</p>
<p style="text-align:center; font-weight:bold; letter-spacing:4pt; margin:6pt 0">B U Y R U G' I</p>
<table style="width:100%; margin:6pt 0"><tr><td>3 oktyabr 2026 yil</td><td style="text-align:center">Toshkent shahri</td><td style="text-align:right">№ 245</td></tr></table>
<p style="text-align:center; font-weight:bold">Huquqiy axborot portalini yangilash ishlarini tashkil etish to'g'risida</p>
<p style="text-indent:36pt; text-align:justify">Huquqiy axborot portalining ishonchliligini oshirish maqsadida buyuraman:</p>
<p style="text-indent:36pt; text-align:justify">1. Moliya bo'limi boshlig'i portal yangilanishi uchun zarur xarajatlar smetasini 2026 yil 15 noyabrgacha tayyorlasin.</p>
<p style="text-indent:36pt; text-align:justify">2. Yangi qidiruv tizimi Axborot texnologiyalari boshqarmasi tomonidan 2026-yil 1-dekabrga qadar sinovdan o'tkazilsin.</p>
<p style="text-indent:36pt; text-align:justify">3. Ishchi guruh a'zolari portal foydalanuvchilari murojaatlarini har haftada tahlil qilib borsin.</p>
<p style="text-indent:36pt; text-align:justify">4. Quyidagi tadbirlar ijrosi ta'minlansin:</p>
<table style="width:100%; border-collapse:collapse; font-size:11.5pt">
<tr><th style="border:1px solid #000; padding:4pt">T/r</th><th style="border:1px solid #000; padding:4pt">Tadbir nomi</th><th style="border:1px solid #000; padding:4pt">Ijrochi</th><th style="border:1px solid #000; padding:4pt">Bajarish muddati</th></tr>
<tr><td style="border:1px solid #000; padding:4pt">1</td><td style="border:1px solid #000; padding:4pt">Portal ma'lumotlar bazasining zaxira nusxasini olish</td><td style="border:1px solid #000; padding:4pt">Ma'lumotlar bazasi bo'limi</td><td style="border:1px solid #000; padding:4pt">har kuni</td></tr>
<tr><td style="border:1px solid #000; padding:4pt">2</td><td style="border:1px solid #000; padding:4pt">Foydalanuvchilar uchun video qo'llanma tayyorlash</td><td style="border:1px solid #000; padding:4pt">Matbuot xizmati; Dizayn sektori</td><td style="border:1px solid #000; padding:4pt">20.12.2026</td></tr>
<tr><td style="border:1px solid #000; padding:4pt">3</td><td style="border:1px solid #000; padding:4pt">Yangilangan portalni rasmiy ishga tushirish</td><td style="border:1px solid #000; padding:4pt">Axborot texnologiyalari boshqarmasi</td><td style="border:1px solid #000; padding:4pt">sinov yakunlangandan so'ng 10 kun ichida</td></tr>
</table>
<p style="text-indent:36pt; text-align:justify">5. Mazkur buyruq ijrosini nazorat qilishni o'z zimmamda qoldiraman.</p>
<table style="width:100%; margin-top:30pt"><tr><td>Markaz direktorining<br>birinchi o'rinbosari</td><td style="text-align:right; vertical-align:bottom">F. Rahimova</td></tr></table>
</div>
"""
GOLD = {
    "requisites": {"sender": "O'zbekiston Respublikasi Adliya vazirligi huzuridagi huquqiy axborot markazi", "number": "245",
                   "date": "2026-10-03", "signatory": "F. Rahimova"},
    "tasks": [
        {"text": "Moliya bo'limi boshlig'i portal yangilanishi uchun zarur xarajatlar smetasini 2026 yil 15 noyabrgacha tayyorlasin.",
         "executors": ["Moliya bo'limi boshlig'i"], "deadline": {"text": "2026 yil 15 noyabrgacha", "type": "sana", "date": "2026-11-15"}},
        {"text": "Yangi qidiruv tizimi Axborot texnologiyalari boshqarmasi tomonidan 2026-yil 1-dekabrga qadar sinovdan o'tkazilsin.",
         "executors": ["Axborot texnologiyalari boshqarmasi"], "deadline": {"text": "2026-yil 1-dekabrga qadar", "type": "sana", "date": "2026-12-01"}},
        {"text": "Ishchi guruh a'zolari portal foydalanuvchilari murojaatlarini har haftada tahlil qilib borsin.",
         "executors": ["Ishchi guruh a'zolari"], "deadline": {"text": "har haftada", "type": "davriy", "date": None}},
        {"text": "Portal ma'lumotlar bazasining zaxira nusxasini olish", "executors": ["Ma'lumotlar bazasi bo'limi"],
         "deadline": {"text": "har kuni", "type": "davriy", "date": None}},
        {"text": "Foydalanuvchilar uchun video qo'llanma tayyorlash", "executors": ["Matbuot xizmati", "Dizayn sektori"],
         "deadline": {"text": "20.12.2026", "type": "sana", "date": "2026-12-20"}},
        {"text": "Yangilangan portalni rasmiy ishga tushirish", "executors": ["Axborot texnologiyalari boshqarmasi"],
         "deadline": {"text": "sinov yakunlangandan so'ng 10 kun ichida", "type": "shartli", "date": None}},
    ],
}


def main():
    OUT.mkdir(exist_ok=True)
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_htmlbox(pymupdf.Rect(60, 50, 540, 800), HTML)
    doc.save(OUT / "buyruq_245.pdf")
    # "skaner": 150 dpi, 0.6 daraja qiyshiq, shovqin
    pix = doc[0].get_pixmap(dpi=150, colorspace=pymupdf.csGRAY)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width).astype(np.int16)
    import cv2
    m = cv2.getRotationMatrix2D((pix.width / 2, pix.height / 2), 0.6, 1)
    img = cv2.warpAffine(img.astype(np.uint8), m, (pix.width, pix.height), borderValue=255).astype(np.int16)
    rng = np.random.default_rng(7)
    img = np.clip(img + rng.normal(0, 12, img.shape), 0, 255).astype(np.uint8)
    ok, png = cv2.imencode(".png", img)
    scan = pymupdf.open()
    sp = scan.new_page(width=595, height=842)
    sp.insert_image(sp.rect, stream=png.tobytes())
    scan.save(OUT / "buyruq_245_skaner.pdf")
    import json
    (OUT / "gold.json").write_text(json.dumps({"buyruq_245": GOLD}, ensure_ascii=False, indent=1))
    print("tayyor:", sorted(p.name for p in OUT.iterdir()))


if __name__ == "__main__":
    main()
