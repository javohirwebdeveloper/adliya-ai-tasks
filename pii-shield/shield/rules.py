"""Shaxsiy ma'lumotni topuvchi qoidalar (o'zbekcha, lotin va kirill).

Matn avval lotinga o'giriladi, har bir lotin harfi asl matnning qaysi belgisidan kelgani eslab qolinadi.
Shunda bitta qoidalar to'plami ikkala yozuvda ishlaydi va topilgan joy asl matnda aniq belgilanadi.

Qat'iy formatlilar (pasport, JSHSHIR, karta...) qo'shimcha tekshiriladi: JSHSHIR ichidagi tug'ilgan sana haqiqiy
sana bo'lishi, karta raqami Luhn tekshiruvidan o'tishi kerak. Bu tasodifiy raqamlarni yashirib yubormaslik uchun.
"""
import re
from dataclasses import dataclass
from datetime import date

from .names import FIRST_NAMES

CYR = {"а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "ё": "yo", "ж": "j", "з": "z", "и": "i", "й": "y", "к": "k",
       "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "x",
       "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sh", "ъ": "'", "ы": "i", "ь": "", "э": "e", "ю": "yu", "я": "ya",
       "ў": "o'", "қ": "q", "ғ": "g'", "ҳ": "h", "е": "e"}
VOWELS = set("аеёиоуўэюяы")
APO = "'ʻʼ‘’`´"


def latinize(text: str) -> tuple[str, list[int]]:
    """Kirill -> lotin, apostroflar bir xil. Qaytaradi: (lotin matn, har lotin belgining asl matndagi o'rni)."""
    out, idx, prev = [], [], ""
    for i, ch in enumerate(text):
        low = ch.lower()
        if low in CYR:
            lat = CYR[low]
            if low == "е" and (not prev or not prev.isalpha() or prev.lower() in VOWELS):
                lat = "ye"
            if ch != low and lat:
                lat = lat[0].upper() + lat[1:]
        elif ch in APO:
            lat = "'"
        else:
            lat = ch
        out.append(lat)
        idx.extend([i] * len(lat))
        prev = ch
    return "".join(out), idx


@dataclass
class Hit:
    kind: str
    start: int          # lotin matndagi o'rni
    end: int
    score: int = 2      # 3: qat'iy format, 2: ishonchli qoida, 1: taxmin


W = r"(?<![\w])"         # so'z boshlanishi
E = r"(?![\w])"          # so'z tugashi
UP = "A-ZЀ-Я"            # bosh harf (lotinga o'girilgandan keyin faqat lotin qoladi)
NAMEW = r"[A-Z][a-z']+(?:-[A-Z][a-z']+)?"                            # Bosh harfli so'z: Javohir, Ma'ruf, Sayfi-Do'st
SURNAME = r"[A-Z][a-z']+(?:ov|ova|ev|eva|yev|yeva|iy|zoda|xonov|xonova)"
MONTHS = "yanvar|fevral|mart|aprel|may|iyun|iyul|avgust|sentabr|sentyabr|oktabr|oktyabr|noyabr|dekabr"


def luhn(digits: str) -> bool:
    s, alt = 0, False
    for d in reversed(digits):
        n = int(d)
        if alt:
            n = n * 2 - 9 if n * 2 > 9 else n * 2
        s += n
        alt = not alt
    return s % 10 == 0


def valid_pinfl(d: str) -> bool:
    if len(d) != 14 or d[0] not in "123456":
        return False
    century = {"1": 1800, "2": 1800, "3": 1900, "4": 1900, "5": 2000, "6": 2000}[d[0]]
    try:
        date(century + int(d[5:7]), int(d[3:5]), int(d[1:3]))
        return True
    except ValueError:
        return False


PATTERNS = [
    # (tur, regex, ishonch, tekshiruv)
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), 3, None),
    ("JSHSHIR", re.compile(W + r"(\d{14})" + E), 3, lambda m: valid_pinfl(m.group(1))),
    ("JSHSHIR", re.compile(r"(?i)(?:jshshir|pinfl|jshir)\D{0,6}(\d{14})"), 3, None),
    ("KARTA", re.compile(W + r"((?:\d{4}[ -]?){3}\d{4})" + E), 3,
     lambda m: (lambda d: luhn(d) or d[:4] in ("8600", "9860"))(re.sub(r"\D", "", m.group(1)))),
    ("HISOB", re.compile(W + r"(\d{20})" + E), 3, None),
    ("STIR", re.compile(r"(?i)(?:stir|inn|soliq to'lovchining identifikatsiya raqami)\D{0,6}(\d{9})" + E), 3, None),
    ("PASPORT", re.compile(W + r"([A-Z]{2} ?№? ?\d{7})" + E), 3, None),
    ("PASPORT", re.compile(r"(?i)(?:pasport|passport|id[- ]?karta|pasportim)\W{0,12}(?:\w+ ){0,2}?([a-z]{2} ?№? ?\d{7})" + E), 3, None),
    ("HUJJAT", re.compile(W + r"([IVX]{1,4}-[A-Z]{2} ?№? ?\d{6,7})" + E), 3, None),
    ("TELEFON", re.compile(r"(?<![\w+])(\+?998[ -]?\(?\d{2}\)?[ -]?\d{3}[ -]?\d{2}[ -]?\d{2})" + E), 3, None),
    ("TELEFON", re.compile(W + r"(\(?(?:20|33|50|55|71|77|88|90|91|93|94|95|97|98|99)\)?[ -]?\d{3}[ -]?\d{2}[ -]?\d{2})" + E), 2, None),
    ("AVTO", re.compile(W + r"(\d{2} ?[A-Z] ?\d{3} ?[A-Z]{2}|\d{2} ?\d{3} ?[A-Z]{3})" + E), 2, None),
    # ism: otasining ismi bilan (eng ishonchli): "Karimov Akmal Rustam o'g'li", "Ivanov Ivan Ivanovich"
    ("ISM", re.compile(r"((?:" + NAMEW + r" ){1,3}(?:o'g'li|og'li|o'gli|ogli|qizi)" + E + ")"), 3, None),
    ("ISM", re.compile(r"(" + NAMEW + " " + NAMEW + " " + r"[A-Z][a-z]+(?:ovich|yevich|evich|ovna|yevna|evna|ichna))" + E), 3, None),
    # familiya va ism (har ikki tartibda), bosh harflar bilan
    ("ISM", re.compile(r"(" + SURNAME + " " + NAMEW + "|" + NAMEW + " " + SURNAME + ")" + E), 2, None),
    ("ISM", re.compile(r"((?:[A-Z]\. ?){1,2}" + SURNAME + "|" + SURNAME + r" (?:[A-Z]\. ?){1,2})"), 2, None),
    ("ISM", re.compile(r"(?i)(?:(?<![\w'])(?:men|ismim|mening ismim|ism-sharifim|fuqaro|janob|arizachi|murojaatchi|"
                       r"zovut|ya|hurmatli)\W{1,3})(" + "|".join(FIRST_NAMES) + r")(?![\w'])"), 2, None),
    ("ISM", re.compile(r"(?i)(?<![\w'])(" + "|".join(FIRST_NAMES) + r")(?= (?:aka|opa|xola|amaki|xonim|uka|singlim)(?![\w']))"), 2, None),
    ("ISM", re.compile(r"(?i)(?<![\w'])([a-z']+(?:ov|ova|ev|eva|yev|yeva) (?:" + "|".join(FIRST_NAMES) + r")|(?:"
                       + "|".join(FIRST_NAMES) + r") [a-z']+(?:ov|ova|ev|eva|yev|yeva))(?![\w'])"), 2, None),
    # tug'ilgan sana (oddiy sanalar, masalan hujjat sanasi, yashirilmaydi: AI ga kerak)
    ("TUG_SANA", re.compile(r"(?i)(\d{1,2}[./]\d{1,2}[./]\d{4}|\d{4}-yil \d{1,2}-(?:" + MONTHS + r")\w*)(?=\D{0,25}(?:yil\w* )?tug'il)"), 3, None),
    ("TUG_SANA", re.compile(r"(?i)tug'il\w*(?: sana\w*)?\W{0,4}(\d{1,2}[./]\d{1,2}[./]\d{4}|\d{4}-yil \d{1,2}-(?:" + MONTHS + r")\w*)"), 3, None),
]

# Manzil: aniq joy (ko'cha, mahalla, uy) yashiriladi; viloyat, tuman va shahar qoladi, chunki murojaatni
# yo'naltirish uchun hudud kerak, uy raqami esa kerak emas.
STREET = re.compile(
    r"((?:" + NAMEW + r" ){1,3}(?:ko'chasi|ko'cha|shoh ko'chasi|tor ko'chasi|berk ko'chasi|mahallasi|MFY|massivi|"
    r"dahasi|kvartali|qishlog'i|ovuli|SFY)(?:,? \d+[a-z]?(?![\w-]))?|(?:ko'cha|mahalla|massiv|kvartal)\s+" + NAMEW + ")" + E)
HOUSE = re.compile(r"(?i)(\d+[a-z]?[-–]?(?:uy|xonadon|kvartira|xona)\w*|(?:uy|xonadon|kvartira|kv\.?)\s*№?\s*\d+[a-z]?|"
                   r"(?:" + NAMEW + r" )?\d+[-–]?(?:mavze|daha|kvartal|mikrorayon))" + E)


def find(lat: str) -> list[Hit]:
    hits = []
    for kind, rx, score, check in PATTERNS:
        for m in rx.finditer(lat):
            if check and not check(m):
                continue
            g = 1 if m.groups() else 0
            hits.append(Hit(kind, m.start(g), m.end(g), score))
    parts = [(m.start(1), m.end(1)) for m in STREET.finditer(lat)] + [(m.start(1), m.end(1)) for m in HOUSE.finditer(lat)]
    parts.sort()
    for s, e in merge_close(parts, lat):
        hits.append(Hit("MANZIL", s, e, 2))
    return hits


def merge_close(spans, text, gap=r"[\s,;.]*"):
    """Yonma-yon turgan ko'cha, uy, xonadon bo'laklarini bitta manzilga birlashtiradi."""
    out = []
    for s, e in spans:
        if out and re.fullmatch(gap, text[out[-1][1]:s] or ""):
            out[-1] = (out[-1][0], max(e, out[-1][1]))
        elif out and s < out[-1][1]:
            out[-1] = (out[-1][0], max(e, out[-1][1]))
        else:
            out.append((s, e))
    return out
