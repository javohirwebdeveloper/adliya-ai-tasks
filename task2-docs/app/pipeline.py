"""PDF -> rekvizitlar va topshiriqlar. Hamma narsa shu serverda, tashqi xizmatlarsiz bajariladi."""
import base64
import time

from . import requisites, tasks
from .extract import extract as extract_pages
from .layout import build_document

def _boxes(boxes, pages) -> list[dict]:
    """Qatorlar qutilarini har sahifa uchun bitta umumiy qutiga birlashtiradi va 0..1 oralig'iga keltiradi."""
    by_page: dict[int, list] = {}
    for pg, x0, y0, x1, y1 in boxes:
        b = by_page.setdefault(pg, [x0, y0, x1, y1])
        b[:] = [min(b[0], x0), min(b[1], y0), max(b[2], x1), max(b[3], y1)]
    out = []
    for pg, (x0, y0, x1, y1) in sorted(by_page.items()):
        w, h = pages[pg - 1].width, pages[pg - 1].height
        out.append({"page": int(pg), "x0": round(float(x0) / w, 4), "y0": round(float(y0) / h, 4),
                    "x1": round(float(x1) / w, 4), "y1": round(float(y1) / h, 4)})
    return out


REQUIRED = {"sender": "jo'natuvchi", "number": "hujjat raqami", "date": "sana", "signatory": "imzolagan shaxs"}


def analyze(pdf_bytes: bytes) -> dict:
    t0 = time.time()
    pages = extract_pages(pdf_bytes)
    doc = build_document(pages)
    req = requisites.extract(doc)
    tk = tasks.extract(doc, req)

    warnings = [f"{name} topilmadi" for key, name in REQUIRED.items() if not req.get(key)]
    for t in tk["tasks"]:
        t["boxes"] = _boxes(t.pop("_boxes", []), pages)
        t["executors"] = [e[:1].upper() + e[1:] for e in t["executors"]]
        if not t["executors"]:
            warnings.append(f"{t['n']}-topshiriq: ijrochi aniqlanmadi")
        if not t["deadline"]:
            t["deadline"] = {"text": "ko'rsatilmagan", "type": "yo'q", "date": None}
    low = [p.number for p in pages if p.ocr_conf is not None and p.ocr_conf < 80]
    if low:
        warnings.append(f"skaner sifati past (sahifa {', '.join(map(str, low))}): natijani tekshiring")

    return {
        "requisites": {k: v for k, v in req.items() if not k.startswith("_")},
        "requisite_boxes": {k: _boxes(v, pages) for k, v in req.get("_boxes", {}).items()},
        "tasks": tk["tasks"],
        "control": tk["control"],
        "other": tk["other"],
        "warnings": warnings,
        "meta": {
            "pages": len(pages),
            "source": doc.source,
            "ocr_confidence": [p.ocr_conf for p in pages if p.ocr_conf is not None],
            "seconds": round(time.time() - t0, 2),
        },
        "previews": ["data:image/jpeg;base64," + base64.b64encode(p.preview).decode() for p in pages[:10] if p.preview],
    }
