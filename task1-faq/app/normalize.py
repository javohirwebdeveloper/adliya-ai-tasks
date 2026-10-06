"""Matnni bir xil ko'rinishga keltirish.

Foydalanuvchilar o'zbekchani turlicha yozadi: o‘, oʻ, o`, o' yoki umuman belgisiz,
ba'zan kirillda. Bazadagi savollar lotinda va oddiy apostrof (') bilan yozilgan.
"""
import re
import unicodedata

_APOSTROPHES = dict.fromkeys(map(ord, "‘’ʻʼ`´‛′ʹ"), "'")
_SPACES = re.compile(r"\s+")
_CYRILLIC = re.compile(r"[Ѐ-ӿ]")

_CYR2LAT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "ё": "yo", "ж": "j", "з": "z",
    "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p",
    "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "x", "ц": "s", "ч": "ch",
    "ш": "sh", "щ": "sh", "ъ": "'", "ы": "i", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    "ў": "o'", "қ": "q", "ғ": "g'", "ҳ": "h",
}
_VOWELS = set("аеёиоуўэюяы")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text or "").translate(_APOSTROPHES)
    return _SPACES.sub(" ", text).strip()


def has_cyrillic(text: str) -> bool:
    return bool(_CYRILLIC.search(text))


def cyr_to_lat(text: str) -> str:
    """O'zbek kirill yozuvini lotinga o'giradi (е so'z boshida va unlidan keyin "ye")."""
    out, prev = [], ""
    for ch in text:
        low = ch.lower()
        if low == "е":
            starts = not prev or not prev.isalpha() or prev.lower() in _VOWELS or prev.lower() in "ъь"
            lat = "ye" if starts else "e"
        else:
            lat = _CYR2LAT.get(low, ch)
        if ch != low and lat:
            lat = lat[0].upper() + lat[1:]
        out.append(lat)
        prev = ch
    return "".join(out)


# Bazadagi savollar qolip bilan yasalgan: "Iltimos, ayting: ...", "Menga ... haqida ayting",
# "... haqida ma'lumot bering". Bu so'zlar mavzu haqida hech narsa demaydi, lekin vektorni
# foydalanuvchining "Menga ..." deb boshlanadigan har qanday savoliga yaqinlashtirib qo'yadi.
_WRAPPERS = [
    (re.compile(r"^iltimos,?\s*ayting:\s*", re.I), ""),
    (re.compile(r"^menga\s+(.+?)\s+haqida\s+ayting[.?!]*$", re.I), r"\1"),
    (re.compile(r"\s+haqida\s+ma'lumot\s+bering[.?!]*$", re.I), ""),
    (re.compile(r"\s+bo'yicha\s+ma'lumot\s+kerak[.?!]*$", re.I), ""),
    (re.compile(r"\s+haqida\s+ayting[.?!]*$", re.I), ""),
]
_FILLERS = re.compile(r"^(assalomu?\s*alaykum|assalom|salom|iltimos|aytingchi|aytib\s+bering(?:chi)?)\W+|\W+(rahmat|raxmat|oldindan\s+rahmat)\W*$", re.I)


def clean_kb_question(text: str) -> str:
    t = normalize(text)
    for rx, rep in _WRAPPERS:
        t = rx.sub(rep, t).strip()
    return t[:1].upper() + t[1:] if t else normalize(text)


def strip_fillers(query: str) -> str:
    prev = None
    while prev != query:
        prev, query = query, _FILLERS.sub("", query).strip()
    return query or prev


def load_synonyms(path) -> list[tuple[re.Pattern, str]]:
    import csv
    try:
        with open(path, encoding="utf-8") as f:
            return [(re.compile(rf"\b(?:{r['pattern']})", re.I), r["canonical"]) for r in csv.DictReader(f)]
    except FileNotFoundError:
        return []


def expand(query: str, synonyms) -> str:
    """So'zlashuv so'zlarining rasmiy nomini qo'shadi: "prava" -> "+ haydovchilik guvohnomasi"."""
    extra = []
    for rx, canon in synonyms or []:
        if rx.search(query) and canon.lower() not in query.lower() and canon not in extra:
            extra.append(canon)
    return f"{query} ({'; '.join(extra)})" if extra else query


def query_variants(query: str, synonyms=None) -> list[str]:
    """Qidiruvga yuboriladigan variantlar.

    Kirill matn o'zbekcha ham, ruscha ham bo'lishi mumkin. Shuning uchun asl matn ham,
    lotinga o'girilgani ham qidiriladi va eng yaxshi natija olinadi: ruscha savolni
    bge-m3 o'zi tushunadi, o'zbek kirilini esa lotin varianti yaxshiroq topadi.
    """
    base = strip_fillers(normalize(query))
    variants = [base]
    if has_cyrillic(base):
        lat = cyr_to_lat(base)
        if lat != base:
            variants.append(lat)
    return [expand(v, synonyms) for v in variants]
