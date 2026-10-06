"""Hujjat rekvizitlari: jo'natuvchi, raqam, sana, imzolagan shaxs (+ tur, mavzu, kimga, ijrochi).

Rasmiy hujjat qolipi qat'iy, shuning uchun qoidalar joylashuvga tayanadi:
  - jo'natuvchi: sahifa tepasidagi blanka (qarorda "QARORI" so'zidan oldingi qatorlar,
    xatda manzil va telefon qatorigacha bo'lgan qatorlar);
  - raqam va sana: blankadan keyingi qatordagi "№" va sana;
  - imzo: chapda lavozim, o'ngda "M. Tursunov" ko'rinishidagi ism turgan qator;
  - "Ijrochi:" qatori imzolagan shaxs EMAS, hujjatni tayyorlagan xodim.
"""
import re

from .dates import find_dates
from .layout import Document, Line

RX_TYPE = re.compile(r"^(QARORI|BUYRUG'I|FARMOYISHI|FARMONI|QAROR|BUYRUQ|FARMOYISH)$")
DOC_TYPES = {"QAROR": "Qaror", "BUYRU": "Buyruq", "FARMOYISH": "Farmoyish", "FARMON": "Farmon"}
PROPER = {"o'zbekiston", "respublikasi", "adliya", "toshkent", "prezident", "prezidenti", "vazirlar", "mahkamasi",
          "oliy", "majlis", "majlisi", "qoraqalpog'iston"}
RX_ADDRESS = re.compile(r"\b\d{6}\b|Tel\.|E-?mail|tel\.|faks", re.I)
RX_NUMBER = re.compile(r"(?:№|N[o°º]\.?|Ne|Мо|Nо)\s*([0-9][\w\-/\.]*\w)")
RX_NAME = re.compile(r"^(?:[A-ZЎҚҒҲ][a-z']{0,2}\.\s?){1,2}[A-ZЎҚҒҲ][\w'\-]+$|^[A-ZЎҚҒҲ][\w'\-]+\s+(?:[A-Z][a-z']{0,2}\.\s?){1,2}$")
RX_POSITION = re.compile(r"raisi|direktor|rahbar|vazir|boshlig'i|o'rinbosari|kotib|hokim|prokuror|sudya|rektor|mudir|bosh\s", re.I)
RX_TITLE_END = re.compile(r"(to'g'risida|haqida|yuzasidan)\s*$", re.I)


def signature_index(lines: list[Line]) -> int | None:
    for i, l in enumerate(lines):
        if l.kind != "text" or len(l.segments) < 2:
            continue
        name, pos = l.segments[-1].text, " ".join(s.text for s in l.segments[:-1])
        if RX_NAME.match(name) and RX_POSITION.search(pos):
            return i
    return None


def _smart_case(upper: str, body: str) -> str:
    """BOSH HARFLI blankadagi nomni oddiy yozuvga o'tkazadi. Matnda katta harf bilan
    uchragan so'zlar (Kengashi, FHDYo, Respublika) shu shaklda qoladi."""
    # matnda qisqartma shaklida uchragan so'zlar (FHDYo, DXM) shu holicha qoladi, qolgani kichik harf
    forms = {tok.lower(): tok for tok in re.findall(r"[\w']+", body)
             if sum(c.isupper() for c in tok) >= 2 and len(tok) <= 6}
    out, after_quote = [], True
    for w in upper.split():
        lead = re.match(r'^["\']*', w).group(0)
        core = w[len(lead):].rstrip('"\'.,')
        trail = w[len(lead) + len(core):]
        low = core.lower()
        form = forms.get(low) or (low.capitalize() if (after_quote or lead or low in PROPER) else low)
        out.append(lead + form + trail)
        after_quote = False
    return " ".join(out)


def _nominative(org: str) -> str:
    # "...KENGASHINING QARORI" -> "...Kengashi"
    return re.sub(r"(?i)(\w)ning$", r"\1", org.strip())


def extract(doc: Document) -> dict:
    lines = doc.lines
    first = [l for l in lines if l.page == 1 and l.kind == "text"]
    width = doc.pages[0].width
    sig_i = signature_index(lines)

    res = {"doc_type": None, "sender": None, "number": None, "date": None, "signatory": None,
           "signatory_position": None, "title": None, "addressee": None, "preparer": None, "reply_to": None}

    # --- turi va jo'natuvchi ---
    type_i = next((i for i, l in enumerate(first) if RX_TYPE.match(l.text.replace(" ", "").upper())), None)
    if type_i is not None:
        word = first[type_i].text.replace(" ", "").upper()
        res["doc_type"] = next((v for k, v in DOC_TYPES.items() if word.startswith(k)), word.capitalize())
        org = " ".join(l.text for l in first[:type_i])
        head_end = type_i + 1
        res["sender"] = _smart_case(_nominative(org), " ".join(l.text for l in first[head_end + 1:]))
    else:
        addr_i = next((i for i, l in enumerate(first[:8]) if RX_ADDRESS.search(l.text)), None)
        res["doc_type"] = "Xat"
        org_lines = first[:addr_i] if addr_i is not None else first[:2]
        head_end = (addr_i + 1) if addr_i is not None else len(org_lines)
        res["sender"] = _smart_case(" ".join(l.text for l in org_lines), " ".join(l.text for l in first[head_end + 2:]))

    # --- raqam, sana, kimga ---
    addressee = []
    for l in first[head_end:head_end + 5]:
        if RX_TITLE_END.search(l.text) and len(l.segments) == 1:
            break
        right = [s for s in l.segments if s.x0 > width * 0.45]
        left = [s for s in l.segments if s.x0 <= width * 0.45]
        if right and res["doc_type"] == "Xat":
            addressee.append(" ".join(s.text for s in right))
        lt = " ".join(s.text for s in left)
        if "-son" in lt or "____" in lt or "dagi" in lt.split() or "xatga" in lt:
            if re.search(r"\d", lt.replace("____", "")) and not re.search(r"^\W*$", lt):
                res["reply_to"] = lt
            continue
        text = lt if res["doc_type"] == "Xat" else l.text
        if res["number"] is None:
            m = RX_NUMBER.search(text)
            if m:
                res["number"] = m.group(1)
        if res["date"] is None:
            ds = find_dates(text)
            if ds:
                res["date"] = ds[0][2].isoformat()
    if addressee:
        res["addressee"] = re.sub(r"ga$", "", " ".join(addressee)).strip()

    # --- mavzu: "... to'g'risida" bilan tugaydigan qator(lar) ---
    for i, l in enumerate(first[head_end:head_end + 8], start=head_end):
        if RX_TITLE_END.search(l.text) and len(l.segments) == 1:
            prev = first[i - 1]
            same_block = len(prev.segments) == 1 and not RX_NUMBER.search(prev.text) and l.y0 - prev.y1 < 40 \
                and not RX_ADDRESS.search(prev.text) and prev.segments[0].x0 < width * 0.45
            res["title"] = (prev.text + " " + l.text) if same_block else l.text
            res["_title_line"] = l
            break

    # --- imzo va ijrochi ---
    if sig_i is not None:
        sl = lines[sig_i]
        res["signatory"] = sl.segments[-1].text
        res["signatory_position"] = " ".join(s.text for s in sl.segments[:-1])
        prev = lines[sig_i - 1] if sig_i > 0 else None
        h = sl.y1 - sl.y0
        if (prev is not None and prev.kind == "text" and len(prev.segments) == 1 and prev.page == sl.page
                and abs(prev.x0 - sl.x0) < 60 and sl.y0 - prev.y1 < 1.6 * h and not prev.text.endswith((".", ":", "!"))
                and prev.x1 < width * 0.6):
            res["signatory_position"] = prev.text + " " + res["signatory_position"]   # "Markaz direktorining / birinchi o'rinbosari"
            sig_i -= 1
        for l in lines[sig_i + 1:sig_i + 4]:
            m = re.match(r"^Ijrochi:\s*(.+)$", l.text)
            if m:
                res["preparer"] = m.group(1).strip()
    res["_signature_index"] = sig_i
    box = lambda ls: [(l.page, l.x0, l.y0, l.x1, l.y1) for l in ls]
    num_line = next((l for l in first[head_end:head_end + 4] if RX_NUMBER.search(l.text)), None)
    sig_lines = []
    if sig_i is not None:
        sig_lines = [l for l in lines[sig_i:sig_i + 2] if l.kind == "text"]
        if sig_lines and sig_lines[0].segments[-1].text == res["signatory"]:
            sig_lines = sig_lines[:1]                  # lavozim bir qatorda
    res["_boxes"] = {
        "sender": box(first[:type_i] if type_i is not None else org_lines),
        "number": box([num_line]) if num_line else [],
        "date": box([num_line]) if num_line else [],
        "signatory": box(sig_lines),
    }
    return res
