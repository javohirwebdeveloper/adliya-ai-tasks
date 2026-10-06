"""PDF sahifasidan so'zlar (koordinatalari bilan) va jadval kataklarini olish.

Ikkala turdagi hujjat bitta yo'ldan o'tadi:
  matnli PDF -> so'zlar PDF ning matn qatlamidan olinadi;
  skaner PDF -> rasm tozalanadi (qiyshiqlik, suv belgisi), so'ng Tesseract OCR.
Jadvallar ikkala holatda ham sahifa rasmidagi chiziqlar bo'yicha topiladi, shuning uchun
keyingi bosqichlar (rekvizit, topshiriq) hujjat qaysi turda kelganini bilmaydi ham.
Barcha koordinatalar 300 DPI dagi piksellarda.
"""
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

import cv2
import numpy as np
import pymupdf
import pytesseract

DPI = 300
SCALE = DPI / 72
OCR_LANG = "uzb"
OCR_WORKERS = int(os.getenv("OCR_WORKERS", "4"))   # kataklar parallel o'qiladi (har biri alohida tesseract jarayoni)
os.environ.setdefault("OMP_THREAD_LIMIT", "1")
MIN_TEXT_WORDS = 20          # bundan kam so'z bo'lsa, sahifa skaner deb hisoblanadi
WATERMARK_LEVEL = 185        # bundan och piksellar (kulrang suv belgisi, dog'lar) oq qilinadi


@dataclass
class Word:
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    conf: float = 100.0

    @property
    def cx(self):
        return (self.x0 + self.x1) / 2

    @property
    def cy(self):
        return (self.y0 + self.y1) / 2


@dataclass
class Table:
    bbox: tuple[int, int, int, int]
    rows: list[list[str]]                       # kataklar matni
    row_boxes: list[tuple[int, int]] = field(default_factory=list)


@dataclass
class Page:
    number: int
    width: int
    height: int
    source: str                                 # "text" yoki "ocr"
    words: list[Word]                           # jadvaldan tashqaridagi so'zlar
    tables: list[Table]
    ocr_conf: float | None = None
    skew: float = 0.0
    preview: bytes | None = None                # sahifa rasmi (JPEG, 900 px): natijani hujjat ustida ko'rsatish uchun


# ---------- rasm bilan ishlash ----------

def render(page: pymupdf.Page) -> np.ndarray:
    pix = page.get_pixmap(dpi=DPI, colorspace=pymupdf.csGRAY)
    return np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width).copy()


def estimate_skew(gray: np.ndarray) -> float:
    """Qatorlar gorizontal bo'lganda proyeksiya profili eng "keskin" bo'ladi (-3..3 daraja)."""
    small = cv2.resize(gray, None, fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA)
    ink = (small < 140).astype(np.uint8) * 255
    h, w = ink.shape

    def sharpness(angle):
        m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1)
        prof = cv2.warpAffine(ink, m, (w, h)).sum(1).astype(float)
        return float(((prof[1:] - prof[:-1]) ** 2).sum())

    coarse = max((a / 2 for a in range(-6, 7)), key=sharpness)
    return max((coarse + a / 10 for a in range(-5, 6)), key=sharpness)


def rotate(gray: np.ndarray, angle: float) -> np.ndarray:
    if abs(angle) < 0.05:
        return gray
    h, w = gray.shape
    m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1)
    return cv2.warpAffine(gray, m, (w, h), flags=cv2.INTER_CUBIC, borderValue=255)


def clean_scan(gray: np.ndarray) -> np.ndarray:
    """Suv belgisi va mayda dog'larni olib tashlash: och kulrang -> oq, matn qora qoladi."""
    out = gray.copy()
    out[out > WATERMARK_LEVEL] = 255
    return cv2.medianBlur(out, 3)


# ---------- jadval chiziqlari ----------

def _positions(mask_1d: np.ndarray, min_gap: int) -> list[int]:
    idx = np.where(mask_1d)[0]
    if len(idx) == 0:
        return []
    groups, start, prev = [], idx[0], idx[0]
    for i in idx[1:]:
        if i - prev > min_gap:
            groups.append((start + prev) // 2)
            start = i
        prev = i
    groups.append((start + prev) // 2)
    return groups


def find_tables(gray: np.ndarray) -> list[dict]:
    """Gorizontal va vertikal chiziqlardan jadval to'rini topadi."""
    ink = (gray < 160).astype(np.uint8) * 255
    h, w = ink.shape
    horiz = cv2.morphologyEx(ink, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (w // 25, 1)))
    vert = cv2.morphologyEx(ink, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, h // 60)))
    grid = cv2.dilate(cv2.bitwise_or(horiz, vert), np.ones((5, 5), np.uint8))
    n, _, stats, _ = cv2.connectedComponentsWithStats(grid)
    tables = []
    for i in range(1, n):
        x, y, bw, bh, _ = stats[i]
        if bw < w * 0.3 or bh < 60:
            continue
        hz = horiz[y:y + bh, x:x + bw]
        vt = vert[y:y + bh, x:x + bw]
        ys = _positions(hz.sum(1) > bw * 255 * 0.5, 8)          # to'liq kenglikdagi gorizontal chiziqlar
        xs = _positions(vt.sum(0) > bh * 255 * 0.5, 8)          # to'liq balandlikdagi vertikal chiziqlar
        if len(ys) < 2 or len(xs) < 3:
            continue
        tables.append({"bbox": (x, y, x + bw, y + bh), "ys": [y + v for v in ys], "xs": [x + v for v in xs],
                       "line_mask": (horiz[y:y + bh, x:x + bw] | vert[y:y + bh, x:x + bw])})
    return sorted(tables, key=lambda t: t["bbox"][1])


# ---------- so'zlar ----------

def text_words(page: pymupdf.Page) -> list[Word]:
    return [Word(t, x0 * SCALE, y0 * SCALE, x1 * SCALE, y1 * SCALE)
            for x0, y0, x1, y1, t, *_ in page.get_text("words") if t.strip()]


def ocr_words(img: np.ndarray, psm: int = 3) -> list[Word]:
    d = pytesseract.image_to_data(img, lang=OCR_LANG, config=f"--psm {psm}", output_type=pytesseract.Output.DICT)
    words = []
    for t, c, x, y, bw, bh in zip(d["text"], d["conf"], d["left"], d["top"], d["width"], d["height"]):
        t = t.strip()
        if t and float(c) >= 0:
            words.append(Word(t, x, y, x + bw, y + bh, float(c)))
    return words


def ocr_cell(img: np.ndarray) -> str:
    if img.size == 0 or (img < 128).sum() < 20:
        return ""
    big = cv2.copyMakeBorder(img, 12, 12, 12, 12, cv2.BORDER_CONSTANT, value=255)
    return " ".join(pytesseract.image_to_string(big, lang=OCR_LANG, config="--psm 6").split())


def _inside(wd: Word, box) -> bool:
    x0, y0, x1, y1 = box
    return x0 <= wd.cx <= x1 and y0 <= wd.cy <= y1


def _cell_text(words: list[Word]) -> str:
    """Katak ichidagi so'zlarni qatorma-qator o'qish tartibida birlashtiradi."""
    words = sorted(words, key=lambda w: (round(w.cy / 25), w.x0))
    return " ".join(w.text for w in words)


def extract_page(page: pymupdf.Page, number: int) -> Page:
    gray = render(page)
    words = text_words(page)
    is_text = len(words) >= MIN_TEXT_WORDS
    skew, conf = 0.0, None
    if not is_text:
        skew = estimate_skew(gray)
        gray = clean_scan(rotate(gray, skew))

    tables_raw = find_tables(gray)
    if not is_text:
        masked = gray.copy()
        for t in tables_raw:
            x0, y0, x1, y1 = t["bbox"]
            masked[y0:y1, x0:x1] = 255
        words = ocr_words(masked)
        good = [w.conf for w in words if w.conf > 0]
        conf = round(float(np.mean(good)), 1) if good else None

    tables = []
    for t in tables_raw:
        grid = [[(xa + 4, ya + 4, xb - 4, yb - 4) for xa, xb in zip(t["xs"], t["xs"][1:])]
                for ya, yb in zip(t["ys"], t["ys"][1:]) if yb - ya >= 25]
        if is_text:
            rows = [[_cell_text([w for w in words if _inside(w, b)]) for b in r] for r in grid]
        else:
            with ThreadPoolExecutor(OCR_WORKERS) as pool:
                flat = list(pool.map(lambda b: ocr_cell(gray[b[1]:b[3], b[0]:b[2]]), [b for r in grid for b in r]))
            n = len(grid[0]) if grid else 0
            rows = [flat[i * n:(i + 1) * n] for i in range(len(grid))]
        tables.append(Table(bbox=t["bbox"], rows=rows, row_boxes=[(r[0][1], r[0][3]) for r in grid]))

    outside = [w for w in words if not any(_inside(w, t.bbox) for t in tables)]
    small = cv2.resize(gray, (900, int(900 * gray.shape[0] / gray.shape[1])), interpolation=cv2.INTER_AREA)
    preview = cv2.imencode(".jpg", small, [cv2.IMWRITE_JPEG_QUALITY, 72])[1].tobytes()
    return Page(number, gray.shape[1], gray.shape[0], "text" if is_text else "ocr", outside, tables, conf, skew, preview)


def extract(pdf_bytes: bytes) -> list[Page]:
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    return [extract_page(p, i + 1) for i, p in enumerate(doc)]
