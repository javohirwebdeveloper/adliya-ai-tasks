"""O'zbekcha sana va muddat iboralarini tushunish.

Muddat turlari:
  sana        aniq sana: "2026-yil 1-iyulga qadar", "01.10.2026 yilgacha", jadvalda "18.09.2026"
  boshlanish  "2026-yil 15-martdan boshlab" (tugash sanasi emas, boshlanish sanasi)
  nisbiy      "bir oy muddatda", "uch ish kuni ichida": hujjat sanasidan hisoblanadi
  shartli     "prototip tayyor bo'lgandan so'ng 15 kun ichida": boshlanish hodisasi noma'lum
  davriy      "har oyda", "har oyning 5-sanasiga qadar", "har haftaning juma kuni"
  doimiy      "doimiy"
  matn        jadval katagida tushunilmagan matn (o'zgarishsiz ko'rsatiladi)
"""
import datetime as dt
import re

from dateutil.relativedelta import relativedelta

MONTHS = {"yanvar": 1, "fevral": 2, "mart": 3, "aprel": 4, "may": 5, "iyun": 6, "iyul": 7, "avgust": 8,
          "sentabr": 9, "sentyabr": 9, "oktabr": 10, "oktyabr": 10, "noyabr": 11, "dekabr": 12}
MONTH = "(" + "|".join(sorted(MONTHS, key=len, reverse=True)) + ")"
DIGITS = {"bir": 1, "ikki": 2, "uch": 3, "to'rt": 4, "besh": 5, "olti": 6, "yetti": 7, "sakkiz": 8, "to'qqiz": 9}
TENS = {"o'n": 10, "yigirma": 20, "o'ttiz": 30, "qirq": 40, "ellik": 50, "oltmish": 60}
NUM = (r"(\d+|(?:o'n|yigirma|o'ttiz|qirq|ellik|oltmish)(?:\s+(?:bir|ikki|uch|to'rt|besh|olti|yetti|sakkiz|to'qqiz))?"
       r"|bir|ikki|uch|to'rt|besh|olti|yetti|sakkiz|to'qqiz|yarim)")
UNIT = r"(ish\s+kuni|kun|hafta|oy|yil)"

RX_DMY = re.compile(r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})(?:\s*-?\s*yil\w*)?")
RX_WORDS = re.compile(rf"\b(\d{{4}})\s*-?\s*yil\w*\s+(\d{{1,2}})\s*-?\s*{MONTH}(\w*)", re.I)
RX_WORDS_DMY = re.compile(rf"\b(\d{{1,2}})\s*-?\s*{MONTH}(\w*)\s+(\d{{4}})(?:\s*-?\s*yil\w*)?", re.I)   # "3 oktyabr 2026 yil"
RX_AFTER = re.compile(r"^\s*(?:ga\s+)?(qadar|gacha|dan\s+boshlab|boshlab)", re.I)

RX_PERIODIC = re.compile(
    r"\bhar\s+(?:chorak\s+yakunidan\s+keyingi\s+oyning\s+\d+\s*-\s*sanasiga\s+qadar"
    r"|oyning\s+\d+\s*-\s*sanasiga\s+qadar|oyning\s+\d+\s*-\s*sanasi\w*"
    r"|haftaning\s+\w+\s+kuni|kuni|haftada|hafta|oyda|oy|chorakda|chorak|yarim\s+yilda|yilda|yil)\b", re.I)
RX_CONDITIONAL = re.compile(
    rf"((?:[\w'\-]+\s+){{0,3}}[\w'\-]+(?:gandan|ngandan|ilgandan)\s+(?:so'ng|keyin)\s+{NUM}\s+{UNIT}\w*\s+(?:ichida|muddatda|davomida))",
    re.I)
RX_RELATIVE = re.compile(rf"\b({NUM}\s+{UNIT}\w*\s+(?:muddatda|ichida|davomida))", re.I)
RX_PERMANENT = re.compile(r"\b(doimiy(?:\s+ravishda)?|muntazam(?:\s+ravishda)?)\b", re.I)


def parse_number(s: str) -> float:
    s = s.lower().strip()
    if s.isdigit():
        return int(s)
    if s == "yarim":
        return 0.5
    total = 0
    for part in s.split():
        total += TENS.get(part, 0) + DIGITS.get(part, 0)
    return total


def find_dates(text: str) -> list[tuple[int, int, dt.date, str]]:
    """(boshi, oxiri, sana, keyingi so'z: qadar/boshlab/...)"""
    out = []
    for m in RX_DMY.finditer(text):
        d, mo, y = map(int, m.groups())
        try:
            out.append((m.start(), m.end(), dt.date(y, mo, d)))
        except ValueError:
            pass
    for m in RX_WORDS.finditer(text):
        y, d, mon = int(m.group(1)), int(m.group(2)), MONTHS[m.group(3).lower()]
        try:
            out.append((m.start(), m.end(), dt.date(y, mon, d)))
        except ValueError:
            pass
    for m in RX_WORDS_DMY.finditer(text):
        d, mon, y = int(m.group(1)), MONTHS[m.group(2).lower()], int(m.group(4))
        if any(a <= m.start() < b for a, b, _ in out):
            continue
        try:
            out.append((m.start(), m.end(), dt.date(y, mon, d)))
        except ValueError:
            pass
    res = []
    for s, e, d in sorted(out):
        tail = text[e:e + 20]
        suffix = text[s:e].lower()
        m = RX_AFTER.match(tail)
        rel = m.group(1).lower() if m else ""
        if suffix.endswith(("gacha", "yilgacha")):
            rel = "gacha"
        elif re.search(r"dan$", suffix) and "boshlab" in tail.lower()[:12]:
            rel = "boshlab"
        res.append((s, e + (m.end() if m else 0), d, rel))
    return res


def add_business_days(d: dt.date, n: int) -> dt.date:
    while n > 0:
        d += dt.timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


def add_period(d: dt.date, n: float, unit: str) -> dt.date:
    unit = re.sub(r"\s+", " ", unit.lower())
    if unit == "ish kuni":
        return add_business_days(d, int(n))
    if unit == "kun":
        return d + dt.timedelta(days=int(n))
    if unit == "hafta":
        return d + dt.timedelta(weeks=n)
    if unit == "oy":
        return d + relativedelta(months=int(n)) if n >= 1 else d + dt.timedelta(days=15)
    return d + relativedelta(years=int(n))


def deadline(text: str, doc_date: dt.date | None = None, cell: bool = False) -> dict | None:
    """Matndan muddatni ajratadi. cell=True: jadval katagi, butun katak muddat deb olinadi."""
    t = re.sub(r"\s+", " ", text).strip()
    if not t:
        return None

    m = RX_CONDITIONAL.search(t)
    if m:
        return {"text": m.group(1), "type": "shartli", "date": None}

    dates = find_dates(t)
    for s, e, d, rel in dates:
        if rel == "boshlab":
            return {"text": t[s:e], "type": "boshlanish", "date": d.isoformat()}
        if rel in ("qadar", "gacha") or cell:
            return {"text": t[s:e].rstrip(" ."), "type": "sana", "date": d.isoformat()}

    m = RX_PERIODIC.search(t)
    if m:
        return {"text": m.group(0), "type": "davriy", "date": None}

    m = RX_RELATIVE.search(t)
    if m:
        n, unit = parse_number(m.group(2)), m.group(3)
        when = add_period(doc_date, n, unit).isoformat() if doc_date else None
        return {"text": m.group(1), "type": "nisbiy", "date": when}

    m = RX_PERMANENT.search(t)
    if m:
        return {"text": m.group(1), "type": "doimiy", "date": None}

    if cell:
        return {"text": t, "type": "matn", "date": None}
    return None


def doc_date_from(text: str) -> dt.date | None:
    ds = find_dates(text)
    return ds[0][2] if ds else None
