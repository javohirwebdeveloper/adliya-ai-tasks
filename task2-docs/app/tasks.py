"""Topshiriqlarni ajratish: bandlar, oddiy xat matni va jadvallar (shu jumladan ilovadagi).

Har bir band yoki xatboshi avval turkumlanadi:
  topshiriq      buyruq fe'li bor (-sin, -silar) yoki xatdagi iltimos ("so'raymiz", "so'raladi");
  kirish         "quyidagi topshiriqlar belgilansin:", "...qaror qiladi:" (o'zi topshiriq emas);
  tasdiqlash     "reja ilovaga muvofiq tasdiqlansin";
  nazorat        "ijrosini nazorat qilish ... zimmasiga yuklansin" (alohida maydon);
  umumiy qoida   "muddati ko'rsatilmagan topshiriqlar bir oy muddatda ijro etilsin": muddatsiz
                 topshiriqlarga shu muddat qo'llanadi.
Ijrochi gap boshidagi ot birikmasi: "Axborot texnologiyalari boshqarmasi", "Markazning Tizim
tahlili bo'limi". Uning oxirgi so'zi tashkiliy birlik nomi bo'ladi (bo'limi, boshqarmasi, ...).
"X bilan birgalikda" hamkor ijrochi. Iltimos shaklidagi xat gaplarida ijrochi xatni oluvchi.
"""
import datetime as dt
import re

from .dates import deadline
from .layout import Document, Line

HEADS = {
    "bo'limi", "bo'limlari", "bo'linmasi", "bo'linmalari", "bo'linmalar", "boshqarmasi", "boshqarmalari",
    "departamenti", "departamentlari", "laboratoriyasi", "xizmati", "xizmatlari", "kotibiyati", "guruhi",
    "koordinatori", "markazi", "markaz", "agentligi", "agentlik", "inspeksiyasi", "komissiyasi", "vazirligi",
    "qo'mitasi", "hokimligi", "korxonasi", "instituti", "rahbariyati", "devonxonasi", "sektori", "filiali",
    "boshqaruvi", "jamg'armasi", "palatasi", "idorasi", "apparati", "ma'muriyati", "kengashi", "guruh",
    "boshlig'i", "boshliqlari", "rahbari", "rahbarlari", "mudiri", "direktori", "yordamchisi", "mutaxassisi",
    "mutaxassislari", "xodimlari", "a'zolari", "bo'limlar", "boshqarmalar", "tashkilotlar", "muassasalar",
}
RX_IMPERATIVE = re.compile(r"\b[\w']+(?:sin|sinlar)\b")
RX_REQUEST = re.compile(r"so'raymiz|so'raladi|so'rayman|iltimos qilamiz|iltimos qilinadi")
RX_YOU = re.compile(r"\w+(?:ishingiz|shingiz|ingiz)\w*\s+(?:so'ra|iltimos)")   # "taqdim etishingizni so'raymiz": xat oluvchiga
BARE = {"markaz", "agentlik", "korxona"}
CASE_END = ("ga", "ning", "ni", "da", "dan")
RX_ITEM = re.compile(r"^(\d{1,2})\s*[.)]\s+(.*)$", re.S)

COLS = {
    "num": re.compile(r"^(№|t/r|n|#)$", re.I),
    "text": re.compile(r"topshiriq|chora-?tadbir|mazmun|vazifa|tadbir", re.I),
    "executor": re.compile(r"ijrochi|mas'ul", re.I),
    "deadline": re.compile(r"muddat", re.I),
    "result": re.compile(r"natija", re.I),
}


def classify(text: str) -> str:
    t = text.lower()
    if re.search(r"nazorat qilish\w*\b.*\b(zimmasiga yukla|zimmamda qoldiraman|zimmamga olaman)", t):
        return "nazorat"
    if re.search(r"muddati (alohida )?ko'rsatilmagan", t):
        return "umumiy_muddat"
    if t.rstrip().endswith(":") or re.search(r"quyidagi\s+(?:jadvalda\s+)?(?:[\w'-]+\s+)?(topshiriq|vazifa|chora)", t):
        return "kirish"
    if re.search(r"tasdiqlansin", t) and re.search(r"ilova|reja", t):
        return "tasdiqlash"
    if RX_IMPERATIVE.search(t) or RX_REQUEST.search(t):
        return "topshiriq"
    return "boshqa"


def _clean(tok: str) -> str:
    return tok.strip(",.;:()\"").lower()


def executors_from_text(text: str) -> list[str]:
    toks = text.split()
    for i, tok in enumerate(toks[:8]):                  # ega gap boshida turadi
        if _clean(tok) not in HEADS:
            continue
        nxt = _clean(toks[i + 1]) if i + 1 < len(toks) else ""
        if _clean(tok) in BARE and nxt.endswith(CASE_END):
            continue                                    # "Agentlik rahbariyatiga": aniqlovchi, ega emas
        end = i
        while end + 1 < len(toks) and _clean(toks[end + 1]) in HEADS:     # "bo'limi boshlig'i", "guruh a'zolari"
            end += 1
        nxt = _clean(toks[end + 1]) if end + 1 < len(toks) else ""
        if nxt in ("orqali", "tomonidan"):
            # passiv gap: "tizim Axborot texnologiyalari boshqarmasi tomonidan ... o'tkazilsin".
            # Ot birikmasi bosh harfli so'zdan boshlanadi (3 so'z ichida), bo'lmasa bitta oldingi so'z olinadi.
            start = next((j for j in range(i - 1, max(-1, i - 4), -1) if toks[j][:1].isupper()), i - 1)
            return [" ".join(toks[max(0, start):end + 1]).strip(",.")]
        i = end
        found = [" ".join(toks[:i + 1]).strip(",.")]
        rest = " ".join(toks[i + 1:i + 14])
        m = re.match(r"^(.+?)\s+bilan\s+birgalikda\b", rest)
        if m and _clean(m.group(1).split()[-1]) in HEADS:
            found.append(m.group(1).strip(",."))
        m = re.match(r"^va\s+(.+?)$", rest)
        if m:
            words = m.group(1).split()
            for j, w in enumerate(words[:6]):
                if _clean(w) in HEADS:
                    found.append(" ".join(words[:j + 1]).strip(",."))
                    break
        return found
    return []


def split_executors(cell: str) -> list[str]:
    parts = [p.strip(" .") for p in re.split(r"[;,]", cell) if p.strip(" .")]
    out = []
    for p in parts:
        sub = re.split(r"\s+va\s+", p)
        if len(sub) > 1 and all(_clean(s.split()[-1]) in HEADS for s in sub if s.split()):
            out += sub
        else:
            out.append(p)
    return out


def _paragraphs(lines: list[Line], right: float | None = None) -> list[dict]:
    """Matn qatorlarini xatboshilarga yig'adi; jadval alohida element bo'lib qoladi."""
    text_lines = [l for l in lines if l.kind == "text"]
    if not text_lines:
        return [{"kind": "table", "table": l.table, "page": l.page} for l in lines if l.kind == "table"]
    xs = sorted(round(l.x0 / 10) * 10 for l in text_lines)
    margin = max(set(xs), key=xs.count)
    right = right or max(l.x1 for l in text_lines)
    out, cur, prev = [], None, None
    for l in lines:
        if l.kind == "table":
            if cur:
                out.append(cur)
                cur = None
            out.append({"kind": "table", "table": l.table, "page": l.page})
            continue
        ended = prev is not None and prev.x1 < right - 150 and prev.text.endswith((".", "!", "?", ":", ";"))
        starts = (l.x0 > margin + 60 or RX_ITEM.match(l.text) or cur is None or cur["text"].endswith((":", "!"))
                  or ended or re.match(r"^Ilova\s*:", l.text))
        prev = l
        if starts and cur:
            out.append(cur)
            cur = None
        if cur is None:
            cur = {"kind": "text", "text": l.text, "page": l.page, "boxes": [(l.page, l.x0, l.y0, l.x1, l.y1)]}
        else:
            cur["text"] = cur["text"] + l.text if cur["text"].endswith("-") else cur["text"] + " " + l.text
            cur["boxes"].append((l.page, l.x0, l.y0, l.x1, l.y1))
    if cur:
        out.append(cur)
    return out


def _roles(header: list[str]) -> dict:
    roles = {}
    for j, h in enumerate(header):
        for role, rx in COLS.items():
            if role not in roles and rx.search(h):
                roles[role] = j
                break
    return roles


def _table_tasks(table, doc_date, where: str, prev_roles: dict | None = None, page: int = 1):
    """Jadval qatorlari -> topshiriqlar. Sarlavhasiz jadval avvalgi jadvalning davomi deb olinadi
    (ustunlar soni bir xil bo'lsa): ko'p sahifali jadvallar shunday bo'linadi."""
    idx = [i for i, r in enumerate(table.rows) if any(c.strip() for c in r)]
    if not idx:
        return [], prev_roles
    rows = [table.rows[i] for i in idx]
    roles, data = _roles(rows[0]), list(zip(idx[1:], rows[1:]))
    if "text" not in roles:
        if prev_roles and max(prev_roles.values()) < len(rows[0]):
            roles, data = prev_roles, list(zip(idx, rows))
        else:
            return [], prev_roles
    x0, _, x1, _ = table.bbox
    tasks = []
    for k, (ri, r) in enumerate(data, start=1):
        text = r[roles["text"]].strip()
        if not text:
            continue
        ex = r[roles["executor"]].strip() if "executor" in roles else ""
        dl = r[roles["deadline"]].strip() if "deadline" in roles else ""
        num = r[roles["num"]].strip() if "num" in roles else str(k)
        task = {"source": f"{where}, {num or k}-qator", "text": text, "executors": split_executors(ex),
                "deadline": deadline(dl, doc_date, cell=True) if dl else None}
        if "result" in roles and r[roles["result"]].strip():
            task["result"] = r[roles["result"]].strip()
        if ri < len(table.row_boxes):
            ya, yb = table.row_boxes[ri]
            task["_boxes"] = [(page, x0, ya, x1, yb)]
        tasks.append(task)
    return tasks, roles


def extract(doc: Document, req: dict) -> dict:
    lines = doc.lines
    sig = req.get("_signature_index")
    start = lines.index(req["_title_line"]) + 1 if req.get("_title_line") is not None else 0
    body = [l for l in lines[start:sig] if l.kind == "table" or not l.text.endswith("!")] if sig else lines[start:]
    # ilova: imzodan keyingi sahifalardagi "ILOVA" belgisidan keyin
    appendix: list[Line] = []
    if sig is not None:
        after = lines[sig + 1:]
        ilova_i = next((i for i, l in enumerate(after) if l.kind == "text" and l.text.strip().upper() == "ILOVA"), None)
        if ilova_i is not None:
            appendix = after[ilova_i + 1:]

    doc_date = dt.date.fromisoformat(req["date"]) if req.get("date") else None
    addressee = req.get("addressee")
    tasks, other, control, default_deadline, roles = [], [], [], None, None

    for p in _paragraphs(body):
        if p["kind"] == "table":
            found, roles = _table_tasks(p["table"], doc_date, "jadval", roles, p["page"])
            tasks += found
            continue
        m = RX_ITEM.match(p["text"])
        num, text = (m.group(1), m.group(2)) if m else (None, p["text"])
        kind = classify(text)
        where = f"{num}-band" if num else ("xat matni" if req.get("doc_type") == "Xat" else "matn")
        if kind == "nazorat":
            mm = re.search(r"nazorat qilish\s+(.+?)\s+zimmasiga", text)
            if mm:
                control.append(mm.group(1))
            elif re.search(r"zimmamda|zimmamga", text) and req.get("signatory"):
                control.append(f"{req['signatory']} (imzolagan shaxsning o'zi)")
            else:
                control.append(text)
        elif kind == "umumiy_muddat":
            default_deadline = deadline(text, doc_date)
            if default_deadline:
                default_deadline["rule"] = where
        elif kind == "topshiriq":
            if RX_YOU.search(text) and addressee:
                ex = [addressee]                        # iltimos 2-shaxsda: ijrochi xatni oluvchi
            else:
                ex = executors_from_text(text)
            if not ex and RX_REQUEST.search(text) and addressee:
                ex = [addressee]
            if not ex:
                other.append({"source": where, "text": text, "kind": "umumiy ko'rsatma"})
                continue
            tasks.append({"source": where, "text": text, "executors": ex, "deadline": deadline(text, doc_date),
                          "_boxes": p.get("boxes", [])})
        else:
            other.append({"source": where, "text": text, "kind": kind})

    roles = None
    for p in _paragraphs(appendix):
        if p["kind"] == "table":
            found, roles = _table_tasks(p["table"], doc_date, "ilova jadvali", roles, p["page"])
            tasks += found

    if default_deadline:
        for t in tasks:
            if not t["deadline"]:
                t["deadline"] = dict(default_deadline, note=f"muddat {default_deadline['rule']} bo'yicha")
    for i, t in enumerate(tasks, start=1):
        t["n"] = i
    return {"tasks": tasks, "control": control, "other": other, "default_deadline": default_deadline}
