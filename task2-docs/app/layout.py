"""So'zlardan qatorlar, qatorlardan hujjat bloklari.

Qator ichida katta bo'shliq bo'lsa, u alohida "segment"larga bo'linadi. Rasmiy hujjatlarda
bu muhim: sarlavhada chapda sana va raqam, o'ngda kimga yozilgani; imzoda chapda lavozim,
o'ngda F.I.Sh. turadi. Ularni bitta qatorga qo'shib yuborish xatoga olib keladi.
"""
import re
import unicodedata
from dataclasses import dataclass, field

from .extract import Page, Table, Word

APOS = dict.fromkeys(map(ord, "‘’ʻʼ`´‛′ʹ"), "'")
# OCR ba'zan lotin harfi o'rniga ko'rinishi o'xshash kirill harfini qo'yadi ("Ко"р" -> "Ko'p")
LOOKALIKE = str.maketrans("АВЕКМНОРСТХУаеорсухкмпитвьгш", "ABEKMHOPCTXYaeopcyxkmnutvbrw")
FOOTER = re.compile(r"test uchun example|AI tizimini sinash uchun", re.I)


def norm(text: str) -> str:
    text = unicodedata.normalize("NFC", text).translate(APOS)
    text = re.sub(r"(?<=\w)[“”„\"](?=\w)", "'", text)       # harflar orasidagi qo'shtirnoq: OCR dagi o' / g'
    text = re.sub(r"[“”„«»]", '"', text).replace("''", "'")
    return re.sub(r"\s+", " ", text).strip()


def fix_mixed_script(word: str, latin_doc: bool = True) -> str:
    """Lotin yozuvidagi hujjatda kirill harfi faqat OCR xatosi bo'lishi mumkin."""
    if latin_doc and re.search(r"[Ѐ-ӿ]", word):
        return word.translate(LOOKALIKE)
    return word


@dataclass
class Segment:
    text: str
    x0: float
    x1: float


@dataclass
class Line:
    page: int
    y0: float
    y1: float
    segments: list[Segment]
    kind: str = "text"                      # "text" yoki "table"
    table: Table | None = None

    @property
    def text(self) -> str:
        return " ".join(s.text for s in self.segments)

    @property
    def x0(self) -> float:
        return self.segments[0].x0 if self.segments else 0

    @property
    def x1(self) -> float:
        return self.segments[-1].x1 if self.segments else 0


@dataclass
class Document:
    pages: list[Page]
    lines: list[Line] = field(default_factory=list)  # o'qish tartibida, jadvallar ham shu ro'yxatda
    source: str = "text"

    def text(self) -> str:
        return "\n".join(l.text for l in self.lines if l.kind == "text")


def is_latin(pages: list[Page]) -> bool:
    text = " ".join(w.text for p in pages for w in p.words)
    lat, cyr = len(re.findall(r"[A-Za-z]", text)), len(re.findall(r"[\u0400-\u04FF]", text))
    return lat >= 9 * cyr


def build_lines(words: list[Word], page: int, latin_doc: bool = True) -> list[Line]:
    if not words:
        return []
    heights = sorted(w.y1 - w.y0 for w in words)
    h = heights[len(heights) // 2] or 30
    rows: list[list[Word]] = []
    for w in sorted(words, key=lambda w: (w.cy, w.x0)):
        if rows and abs(w.cy - sum(x.cy for x in rows[-1]) / len(rows[-1])) < h * 0.45:
            rows[-1].append(w)
        else:
            rows.append([w])
    lines = []
    gap_limit = h * 3.2
    for row in rows:
        row.sort(key=lambda w: w.x0)
        segs: list[list[Word]] = [[row[0]]]
        for w in row[1:]:
            if w.x0 - segs[-1][-1].x1 > gap_limit:
                segs.append([w])
            else:
                segs[-1].append(w)
        segments = [Segment(norm(" ".join(fix_mixed_script(w.text, latin_doc) for w in s)), s[0].x0, s[-1].x1)
                    for s in segs]
        lines.append(Line(page, min(w.y0 for w in row), max(w.y1 for w in row), segments))
    return lines


def build_document(pages: list[Page]) -> Document:
    doc = Document(pages, source="ocr" if any(p.source == "ocr" for p in pages) else "text")
    latin_doc = is_latin(pages)
    for p in pages:
        items = [l for l in build_lines(p.words, p.number, latin_doc) if not FOOTER.search(l.text)]
        items = [l for l in items if not re.fullmatch(r"\d{1,2}", l.text)]          # sahifa raqami
        for t in p.tables:
            t.rows = [[norm(" ".join(fix_mixed_script(x, latin_doc) for x in c.split())) for c in r] for r in t.rows]
            items.append(Line(p.number, t.bbox[1], t.bbox[3], [Segment("[JADVAL]", t.bbox[0], t.bbox[2])], "table", t))
        doc.lines.extend(sorted(items, key=lambda l: l.y0))
    return doc
