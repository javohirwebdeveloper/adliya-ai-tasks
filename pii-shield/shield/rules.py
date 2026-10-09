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
QNAME = r"[«\"“„]?" + NAMEW + r"[»\"”]?"                               # qo'shtirnoqda ham: «Ozodlik»
SURNAME = r"[A-Z][a-z']+(?:ov|ova|ev|eva|yev|yeva|iy|zoda|xonov|xonova)"
FATHER = (r"(?:[A-Z][a-z']+(?:bek|jon|xon|boy|ali|ulla|iddin|murod|qul)|" + "|".join(FIRST_NAMES) + ")")  # otasining ismi
# ism ortidan keladigan qo'shimcha ("Karimovga", "Karimovman", "o'g'liman"; ruscha "Karimovu", "Karimovim") yorliqdan tashqarida qoladi
END_NAME = r"(?=(?:ga|ni|ning|dan|da|man|miz|dir|lar|larga|larni|larning|lardan|niki|dek|day|cha|ka|qa|u|im|e|oy|om)?(?![\w']))"
MONTHS = "yanvar|fevral|mart|aprel|may|iyun|iyul|avgust|sentabr|sentyabr|oktabr|oktyabr|noyabr|dekabr"
# kalit so'z bilan qiymat orasida 4 tagacha so'z: "STIR raqamim: ...", "pasport seriyasi va raqami ...", "паспорт серии ..."
FILL = r"(?:\W{1,4}[a-z']{1,14}){0,4}?\W{1,4}"
KW = lambda words: r"(?i)(?<![\w'])(?:" + words + ")"
NUM_END = r"(?![\w]|[ -]\d)"                                      # raqam shu yerda tugaydi (uzunroq raqamning bo'lagi emas)
NOT_MONEY = r"(?!\s*(?:so'm|sum|uzs|\$|dollar|yevro|evro|rub|mln|mlrd|million|milliard|ming|tiyin))"
DATE = (r"\d{1,2}[./]\d{1,2}[./]\d{4}|\d{4}[./-]\d{1,2}[./-]\d{1,2}|\d{4}-yil \d{1,2}-(?:" + MONTHS + r")\w*|\d{1,2}[ -](?:"
        + MONTHS + r")\w*,? \d{4}")
BIRTH = r"t(?:u|o')g'il\w*|rodil\w*|rojdeni\w*|[dg]\. ?r\."          # "tug'ilgan", "тўғилган", "родился", "дата рождения"


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
    ("JSHSHIR", re.compile(r"(?<!\d[ -])" + W + r"(\d{14})" + NUM_END), 3, lambda m: valid_pinfl(m.group(1))),
    ("JSHSHIR", re.compile(KW(r"jshshir|jshir|pinfl|shaxsiy raqam\w*") + FILL + r"(\d(?:[ -]?\d){12,15})(?![\w])"), 3, None),
    ("KARTA", re.compile(r"(?<!\d[ -])" + W + r"((?:\d{4}[ -]?){3}\d{4})" + NUM_END), 3,
     lambda m: (lambda d: luhn(d) or d[:4] in ("8600", "9860"))(re.sub(r"\D", "", m.group(1)))),
    ("KARTA", re.compile(KW(r"uzcard|humo|visa|mastercard|kart\w*|plastik\w*") + FILL + r"(\d(?:[ -]?\d){12,19})"
                         + NUM_END + NOT_MONEY), 3, None),
    ("HISOB", re.compile(r"(?<!\d[ -])" + W + r"(\d{20})" + NUM_END), 3, None),
    ("STIR", re.compile(KW(r"stir|inn|soliq to'lovchining identifikatsiya raqami") + FILL + r"(\d{3}[ -]?\d{3}[ -]?\d{3})"
                        + NUM_END), 3, None),
    ("PASPORT", re.compile(W + r"([A-Z]{2} ?№? ?\d{7})" + E), 3, None),
    # "pasport" so'zidan keyin: kichik harf va 6-8 raqam ham (yozishda xato bo'lsa ham yashirilsin)
    ("PASPORT", re.compile(KW(r"pasport\w*|passport\w*|id[- ]?karta\w*") + FILL
                           + r"(?!(?:va|bu|da|ga|ni|na|po|za|ot|do|iz|ne|to|on|my|vy|ya)\W)([a-z]{2} ?№? ?\d{6,8}|\d{2} ?\d{2} ?№? ?\d{6,7})(?![\w])"), 3, None),
    # qiymat kalit so'zdan oldin: "485920137 STIR raqamim", "AB123456 raqamli pasport"
    ("STIR", re.compile(W + r"(\d{3}[ -]?\d{3}[ -]?\d{3})(?=\W{1,3}(?:raqamli\W{1,3})?(?i:stir|inn)(?![a-z]))"), 3, None),
    ("PASPORT", re.compile(W + r"([A-Z]{2} ?\d{6,8})(?=\W{1,3}(?:raqamli\W{1,3})?(?i:pasport|passport))"), 3, None),
    ("HUJJAT", re.compile(W + r"([IVX]{1,4}-[A-Z]{2} ?№? ?\d{6,7})" + E), 3, None),
    ("TELEFON", re.compile(r"(?<![\w+])(\+?998[ -]?\(?\d{2}\)?[ -]?\d{3}[ -]?\d{2}[ -]?\d{2})" + E), 3, None),
    ("TELEFON", re.compile(W + r"(\(?(?:20|33|50|55|71|77|88|90|91|93|94|95|97|98|99)\)?[ -]?\d{3}[ -]?\d{2}[ -]?\d{2})" + E), 2, None),
    ("AVTO", re.compile(W + r"(\d{2} ?[A-Z] ?\d{3} ?[A-Z]{2}|\d{2} ?\d{3} ?[A-Z]{3})" + E), 2, None),
    # ism: otasining ismi bilan (eng ishonchli): "Karimov Akmal Rustam o'g'li", "Ivanov Ivan Ivanovich"
    ("ISM", re.compile(r"((?:" + NAMEW + r" ){1,3}(?:o'g'li|og'li|o'gli|ogli|qizi))" + END_NAME), 3, None),
    ("ISM", re.compile(r"(" + NAMEW + " " + NAMEW + " " + r"[A-Z][a-z']+(?:ovich|yevich|evich|ovna|yevna|evna|ichna))" + END_NAME), 3, None),
    # familiya va ism (har ikki tartibda; ortidan ikkinchi familiya ham bo'lishi mumkin), bosh harflar bilan
    ("ISM", re.compile(r"(" + SURNAME + "(?:u|a|im|e|oy|om)? " + NAMEW + "(?: " + SURNAME + "| " + FATHER + ")?|" + NAMEW + " " + SURNAME + ")" + END_NAME), 2, None),
    ("ISM", re.compile(r"((?:[A-Z]\. ?){1,2}" + SURNAME + "|" + SURNAME + r" (?:[A-Z]\. ?){1,2})"), 2, None),
    ("ISM", re.compile(r"(?i)(?:(?<![\w'])(?:men|ismim|mening ismim|ism-sharifim|fuqaro|janob|arizachi|murojaatchi|"
                       r"zovut|ya|hurmatli)\W{1,3})(" + "|".join(FIRST_NAMES) + r")(?![\w'])"), 2, None),
    ("ISM", re.compile(r"(?i)(?<![\w'])(" + "|".join(FIRST_NAMES) + r")(?= (?:aka|opa|xola|amaki|xonim|uka|singlim)(?![\w']))"), 2, None),
    # yolg'iz familiya: ishora so'zdan keyin ("Men Nazarov") yoki "-man" bilan ("Nazarovman")
    ("ISM", re.compile(r"(?<![\w'])(?i:men|ismim|familiyam|fuqaro|janob|arizachi|murojaatchi|ya|hurmatli|grajdanin|gospodin)"
                       r"\W{1,3}(" + SURNAME + ")" + END_NAME), 2, None),
    ("ISM", re.compile(W + "(" + SURNAME + r")(?=man(?![\w']))"), 2, None),
    ("ISM", re.compile(r"(?i)(?<![\w'])([a-z']+(?:ov|ova|ev|eva|yev|yeva) (?:" + "|".join(FIRST_NAMES) + r")|(?:"
                       + "|".join(FIRST_NAMES) + r") [a-z']+(?:ov|ova|ev|eva|yev|yeva))" + END_NAME), 2, None),
    # tug'ilgan sana: faqat "tug'ilgan" / "родился" yonida. Oddiy sanalar (hujjat sanasi, muddat) va yolg'iz tug'ilgan
    # yil yashirilmaydi: AI ga muddat va yosh kerak, ular odamni aniqlab bermaydi.
    ("TUG_SANA", re.compile(r"(?i)(" + DATE + r")(?=\D{0,25}(?:yil\w* |goda? )?(?:" + BIRTH + "))"), 3, None),
    ("TUG_SANA", re.compile(r"(?i)(?:" + BIRTH + r")(?: (?:sana|kun|data)\w*)?\W{0,4}(" + DATE + ")"), 3, None),
]

# Uzun raqam (12+ xona) hech bir qoidaga tushmasa ham yashiriladi: murojaatda bunday raqam deyarli doim
# shaxsiy (karta, JSHSHIR, hisob). Pul summasi va yillar ro'yxati bundan mustasno.
LONG_NUM = re.compile(r"(?<![\w+])(\d(?:[ -]?\d){11,23})" + NUM_END + NOT_MONEY, re.I)
LONG_KIND = {14: "JSHSHIR", 16: "KARTA", 20: "HISOB"}

# Ism bo'lmagan, lekin gap boshida bosh harf bilan yoziladigan so'zlar ("Men Karimov" -> faqat "Karimov")
STOP = set("""men mening menga meni ismim ism familiyam familiya hurmatli assalomu salom biz bizning fuqaro janob
arizachi murojaatchi talabnoma ijrochi notarius otam onam akam opam iltimos rahmat siz sizga sizning va bilan uchun
ya menya moy moya mne uvajayemiy uvajayemaya zdravstvuyte gospodin grajdanin grajdanka dobriy privet
milliy ijtimoiy tibbiy huquqiy moliyaviy iqtisodiy madaniy ilmiy harbiy siyosiy oliy asosiy umumiy rasmiy shaxsiy
xususiy mahalliy ma'muriy jinoiy ma'naviy doimiy qonuniy hududiy idoraviy tarixiy
to'lov so'rov sinov tanlov saylov ishlov""".split())
FIRST_SET = {n.lower() for n in FIRST_NAMES}


def name_like(tok: str) -> bool:
    low = tok.lower()
    return low not in STOP and (low in FIRST_SET or re.fullmatch(SURNAME, tok) is not None
                                or re.search(r"(?:ovich|evich|ovna|evna|o'g'li|qizi)$", low) is not None)


def trim_name(lat: str, h: Hit):
    """Ism chegarasidan "Men", "Hurmatli" kabi so'zlarni olib tashlaydi; ism qolmasa - topilma bekor."""
    toks = [(m.start(), m.end()) for m in re.finditer(r"[\w'.-]+", lat[h.start:h.end])]
    while toks and lat[h.start + toks[0][0]:h.start + toks[0][1]].lower() in STOP:
        toks.pop(0)
    while toks and lat[h.start + toks[-1][0]:h.start + toks[-1][1]].lower() in STOP:
        toks.pop()
    if not any(name_like(lat[h.start + a:h.start + b]) for a, b in toks):
        return None
    return Hit(h.kind, h.start + toks[0][0], h.start + toks[-1][1], h.score)


# Manzil: aniq joy (ko'cha, mahalla, uy) yashiriladi; viloyat, tuman va shahar qoladi, chunki murojaatni
# yo'naltirish uchun hudud kerak, uy raqami esa kerak emas.
STREET = re.compile(
    r"((?:" + QNAME + r" ){1,3}(?:ko'chasi|ko'cha|shoh ko'chasi|tor ko'chasi|berk ko'chasi|mahallasi|MFY|massivi|"
    r"dahasi|kvartali|qishlog'i|ovuli|SFY)(?:,? \d+[a-z]?(?![\w-]))?|"
    # oldindan keladigan shakl, ruscha ham: "mahalla Navbahor", "ulitsa Amira Temura", "ul. Amir Temur 45"
    r"(?i:ko'cha|mahalla|maxalla|maxallya|mahallya|massiv|kvartal|ulitsa|ul\.|prospekt|pr-t|pereulok|per\.|proyezd|"
    r"tupik|bulvar|mikrorayon|mkr\.?)\s*(?:" + QNAME + " ){0,2}" + QNAME + r"(?:,? \d+[a-z]?(?![\w-]))?)" + E)
HOUSE = re.compile(r"(?i)(\d+[a-z]?[-–]?(?:uy|xonadon|kvartira|xona)\w*|(?:uy|xonadon|kvartira|kv\.?|dom|d\.|korpus)\s*№?\s*\d+[a-z]?|"
                   r"(?:" + NAMEW + r" )?\d+[-–]?(?:mavze|daha|kvartal|mikrorayon)|"
                   r"\d+[-–]?(?:tor |berk )?(?:ko'cha\w*|ulitsa|ulichka|proyezd|tupik|liniya))" + E)


def overlapping(rx, text):
    """Ustma-ust tushadigan barcha moslar: "Men Bobojonov Sardorbek" da "Men Bobojonov" ham, "Bobojonov Sardorbek" ham."""
    pos = 0
    while (m := rx.search(text, pos)) is not None:
        yield m
        pos = m.start() + 1


def find(lat: str) -> list[Hit]:
    hits = []
    for kind, rx, score, check in PATTERNS:
        for m in (overlapping(rx, lat) if kind == "ISM" else rx.finditer(lat)):
            if check and not check(m):
                continue
            g = 1 if m.groups() else 0
            h = Hit(kind, m.start(g), m.end(g), score)
            if kind == "ISM":
                h = trim_name(lat, h)
            if h:
                hits.append(h)
    for m in LONG_NUM.finditer(lat):
        groups = re.split(r"[ -]", m.group(1))
        if len(groups) > 1 and all(re.fullmatch(r"(?:19|20)\d\d", g) for g in groups):
            continue                                            # "2024 2025 2026" - yillar
        hits.append(Hit(LONG_KIND.get(len("".join(groups)), "RAQAM"), m.start(1), m.end(1), 1))
    parts = [p for m in STREET.finditer(lat) if (p := street_name(lat, m.start(1), m.end(1)))]
    parts += [(m.start(1), m.end(1)) for m in HOUSE.finditer(lat)]
    parts.sort()
    for s, e in merge_close(parts, lat):
        hits.append(Hit("MANZIL", s, e, 2))
    return hits


def street_name(lat: str, s: int, e: int):
    """Ko'cha nomi o'rnida "Menga", "Bizning" kabi so'z bo'lsa ("Menga ko'cha nomi kerakmi?"), bu manzil emas."""
    while (w := re.match(r"[\w'.-]+\s*", lat[s:e])) and w.group(0).strip().lower() in STOP:
        s += w.end()
    return (s, e) if re.search(r"[A-Z][a-z']", lat[s:e]) else None


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
