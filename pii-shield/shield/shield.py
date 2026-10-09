"""Shaxsiy ma'lumot qalqoni: matn AI ga ketishidan oldin yashiradi, javob qaytgach joyiga qo'yadi.

    s = Shield()
    masked, key = s.mask("Karimov Akmal Rustam o'g'li, pasport AA1234567, tel +998 90 123 45 67")
    # "[ISM_1], pasport [PASPORT_1], tel [TELEFON_1]"   key -> {"[ISM_1]": "Karimov Akmal Rustam o'g'li", ...}
    answer = llm(masked)                       # AI shaxsiy ma'lumotni ko'rmaydi
    s.unmask(answer, key)                      # javobdagi belgilar asl qiymatga qaytadi

Bir xil qiymat har doim bir xil belgi oladi ("[ISM_1]" ikki joyda bo'lsa, ikkalasi ham o'sha odam).
"""
import re

from .rules import Hit, find, latinize

PRIORITY = {"JSHSHIR": 9, "KARTA": 9, "HISOB": 9, "HUJJAT": 8, "PASPORT": 8, "STIR": 8, "EMAIL": 8, "TELEFON": 7,
            "TUG_SANA": 7, "AVTO": 6, "ISM": 5, "MANZIL": 4}


def resolve(hits: list[Hit]) -> list[Hit]:
    """Ustma-ust tushganlardan ishonchlisi va uzunrog'i qoladi."""
    hits = sorted(hits, key=lambda h: (-h.score, -PRIORITY[h.kind], -(h.end - h.start), h.start))
    taken, out = [], []
    for h in hits:
        if any(h.start < e and s < h.end for s, e in taken):
            continue
        taken.append((h.start, h.end))
        out.append(h)
    return sorted(out, key=lambda h: h.start)


class Shield:
    def __init__(self, model=None):
        self.model = model              # ixtiyoriy: ism va manzilni topuvchi o'qitilgan model (ner.py)

    def detect(self, text: str) -> list[tuple[str, int, int]]:
        lat, idx = latinize(text)
        hits = find(lat)
        if self.model is not None:
            hits += [Hit(k, s, e, 1) for k, s, e in self.model.predict(lat)]
        out = []
        for h in resolve(hits):
            s, e = idx[h.start], idx[h.end - 1] + 1
            while e > s and text[e - 1] in " ,.;:":
                e -= 1
            out.append((h.kind, s, e))
        return out

    def mask(self, text: str) -> tuple[str, dict]:
        key, by_value, counters, parts, last = {}, {}, {}, [], 0
        for kind, s, e in self.detect(text):
            value = text[s:e]
            norm = (kind, re.sub(r"[\s\-()№]", "", value.lower()))
            if norm not in by_value:
                counters[kind] = counters.get(kind, 0) + 1
                by_value[norm] = f"[{kind}_{counters[kind]}]"
                key[by_value[norm]] = value
            parts += [text[last:s], by_value[norm]]
            last = e
        parts.append(text[last:])
        return "".join(parts), key

    @staticmethod
    def unmask(text: str, key: dict) -> str:
        return re.sub(r"\[[A-Z_]+_\d+\]", lambda m: key.get(m.group(0), m.group(0)), text)
