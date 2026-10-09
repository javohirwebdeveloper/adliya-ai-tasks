"""Gemma yozgan murojaatlar bo'yicha natija: qalqonning ko'r testi va murojaat yordamchisi.

    python -m eval.gemma_eval llm/natija/gemma_items.json

1. Qalqon: Gemma har murojaat uchun undagi shaxsiy ma'lumotlarni ro'yxat qilib bergan. Ularning har biri matnda
   topilib, qalqon yopgan-yopmagani tekshiriladi. Qoidalar bu matnlarni oldin ko'rmagan (ko'r test).
   Manzilda viloyat, tuman va shahar ochiq qolishi to'g'ri hisoblanadi: faqat aniq joy (ko'cha, mahalla, uy) tekshiriladi.
2. Yordamchi: mavzu asl matnda va yashirilgan matnda qanchalik to'g'ri aniqlandi; javob loyihasida belgilar
   ([ISM_1] ...) buzilmay qoldimi; model o'zidan raqam to'qidimi.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from difflib import get_close_matches  # noqa: E402

from llm.prompts import TOPICS, reply_lang  # noqa: E402
from shield import Shield  # noqa: E402

APO = dict.fromkeys(map(ord, "‘’ʻʼ`´"), "'")
norm = lambda s: re.sub(r"\s+", " ", str(s or "")).translate(APO).strip().lower()
KINDS = ("ISM", "PASPORT", "JSHSHIR", "TELEFON", "KARTA", "MANZIL", "TUG_SANA", "EMAIL", "AVTO", "STIR")
# Siyosat bo'yicha ochiq qoladiganlar talab qilinmaydi: hudud (viloyat, tuman, shahar), karta turi (Humo, Uzcard)
REGION = re.compile(r"(?i)[\w'‘’ʻʼ.-]+\s+(?:viloyati|viloyat|tumani|tuman|shahri|shahar|shaxri|respublikasi|vil\.|tum\.|"
                    r"вилояти|вилоят|тумани|туман|шаҳри|шаҳар|шахри|область|обл\.?|район|р-н)(?!\w)|(?:г\.|город)\s*[\w-]+")
CITY = re.compile(r"(?i)\s*(?:toshkent|tashkent|ташкент|тошкент|samarqand|самарқанд|самарканд|buxoro|бухара|andijon|андижан|"
                  r"namangan|наманган|farg'ona|фергана|qarshi|nukus|нукус|xiva|urganch|navoiy|jizzax|guliston|termiz|"
                  r"chirchiq|чирчик|olmaliq|angren)\s*")
BRAND = re.compile(r"(?i)uzcard|humo|visa|mastercard|kart\w*|карт\w*")


def spans(text, value):
    """Qiymat matnning qayerlarida uchraydi. Avval aynan (raqam uzunroq raqamning bo'lagi emas), topilmasa
    bo'sh joy, tire va katta-kichik harfga e'tibor bermasdan."""
    value = value.strip()
    if not value:
        return []
    b0 = r"(?<![^\W_])" if value[0].isalnum() else ""
    b1 = r"(?!\d)" if value[-1].isdigit() else ""            # so'z oxiriga qo'shimcha qo'shilishi mumkin: "12-mayda"
    out = [m.span() for m in re.finditer(b0 + re.escape(value) + b1, text)]
    if not out:
        runs = re.findall(r"[^\W_]+", value)
        if runs:
            rx = r"(?<![^\W_])" + r"[\W_]*".join(map(re.escape, runs)) + (r"(?!\d)" if runs[-1][-1].isdigit() else "")
            out = [m.span() for m in re.finditer(rx, text, re.I)]
    return out


def must_hide(kind, text, s, e):
    """Yashirilishi shart belgilar: qiymatdagi harf va raqamlar, siyosat bo'yicha ochiq qismlardan tashqari."""
    need = [i for i in range(s, e) if text[i].isalnum()]
    free = set()
    seg = text[s:e]
    if kind == "MANZIL":
        for m in REGION.finditer(seg):
            free.update(range(s + m.start(), s + m.end()))
        pos = s
        for chunk in seg.split(","):
            if CITY.fullmatch(chunk):
                free.update(range(pos, pos + len(chunk)))
            pos += len(chunk) + 1
    if kind == "KARTA":
        for m in BRAND.finditer(seg):
            free.update(range(s + m.start(), s + m.end()))
    return [i for i in need if i not in free]


def policy_open(kind, value):
    """Ataylab ochiq qoladigan qiymat: yolg'iz tug'ilgan yil (1992)."""
    return kind == "TUG_SANA" and re.fullmatch(r"\D*(?:19|20)\d\d\D*", value) is not None


def main(path, show=True):
    items = json.load(open(path, encoding="utf-8"))
    sh = Shield()
    st, per, misses, extras = Counter(), Counter(), [], []
    for n, it in enumerate(items):
        text = it["matn"]
        det = sh.detect(text)
        covered = [False] * len(text)
        for _, s, e in det:
            covered[s:e] = [True] * (e - s)
        gold_spans = []
        for p in it.get("shaxsiy") or []:
            kind, value = str(p.get("tur", "")).upper(), str(p.get("qiymat", ""))
            if kind not in KINDS:
                continue
            locs = spans(text, value)
            gold_spans += locs
            if not locs:
                st["matnda_yo'q"] += 1
                continue
            if policy_open(kind, value):
                st["siyosat_ochiq"] += 1
                continue
            for s, e in locs:
                req = must_hide(kind, text, s, e)
                if not req:
                    continue
                hidden = sum(covered[i] for i in req) / len(req) >= 0.9
                per[kind, "jami"] += 1; per[kind, "yashirildi"] += hidden
                st["jami"] += 1; st["yashirildi"] += hidden
                if not hidden:
                    misses.append((n, kind, value, text[max(0, s - 35):e + 10].replace("\n", " ")))
        for kind, s, e in det:
            st["topilgan"] += 1
            if not any(s < ge and gs < e for gs, ge in gold_spans):
                extras.append((n, kind, text[s:e]))
    print(f"Qalqon (ko'r test, {len(items)} murojaat): {st['yashirildi']}/{st['jami']} = "
          f"{st['yashirildi'] / max(1, st['jami']):.1%} yashirildi. Gemma ro'yxatida bor, lekin matnda yo'q: "
          f"{st['matnda_yo\'q']}; siyosat bo'yicha ochiq (yolg'iz tug'ilgan yil): {st['siyosat_ochiq']}")
    print("  " + ", ".join(f"{k} {per[k, 'yashirildi']}/{per[k, 'jami']}" for k in sorted({k for k, _ in per})))
    print(f"  Gemma ro'yxatida yo'q, lekin qalqon yashirgan: {len(extras)} ta (qo'lda ko'rib chiqiladi)")
    if show:
        for m in misses:
            print("  SIZIB CHIQDI:", m)
        for x in extras:
            print("  RO'YXATDA YO'Q:", x)

    # yordamchi
    a = Counter()
    for it in items:
        ja, jy = it.get("javob_asl") or {}, it.get("javob_yashirin") or {}
        a["n"] += 1
        a["json_asl"] += bool(ja); a["json_yashirin"] += bool(jy)
        a["mavzu_asl"] += norm(ja.get("mavzu")) == norm(it["mavzu"])
        a["mavzu_yashirin"] += norm(jy.get("mavzu")) == norm(it["mavzu"])
        a["mavzu_bir_xil"] += norm(ja.get("mavzu")) == norm(jy.get("mavzu"))
        a["shosh_bir_xil"] += ja.get("shoshilinch") == jy.get("shoshilinch")
        # mavzu nomida imlo xatosi bo'lsa ("Tadbbirkorlik"), eng yaqin mavzuga moslanadi (ishlab chiqarishda ham shunday)
        fix = lambda m: (get_close_matches(str(m or ""), TOPICS, n=1, cutoff=0.8) or [str(m or "")])[0]
        a["mavzu_asl_m"] += fix(ja.get("mavzu")) == it["mavzu"]
        a["mavzu_yashirin_m"] += fix(jy.get("mavzu")) == it["mavzu"]
        a["mavzu_bir_xil_m"] += fix(ja.get("mavzu")) == fix(jy.get("mavzu"))
        a["til_mos"] += reply_lang(str(jy.get("javob_loyihasi") or "")) == it["yozuv"]
        reply = str(jy.get("javob_loyihasi") or "")
        used = set(re.findall(r"\[[A-Z_]+_\d+\]", reply))
        a["belgi_ishlatildi"] += bool(used)
        a["toqilgan_belgi"] += bool(used - set(it["key"]))
        src_nums = set(re.findall(r"\d{5,}", it["masked"]))
        a["toqilgan_raqam"] += bool(set(re.findall(r"\d{5,}", reply)) - src_nums)
    n = a["n"]
    print(f"\nYordamchi ({n} ta murojaat):")
    print(f"  mavzu to'g'ri: asl matnda {a['mavzu_asl'] / n:.1%}, yashirilgan matnda {a['mavzu_yashirin'] / n:.1%}; "
          f"ikkala holatda bir xil javob {a['mavzu_bir_xil'] / n:.1%}")
    print(f"  JSON to'g'ri: {a['json_yashirin'] / n:.1%}; javobda belgi ishlatilgan: {a['belgi_ishlatildi']}; "
          f"o'zidan belgi to'qigan: {a['toqilgan_belgi']}; o'zidan raqam to'qigan: {a['toqilgan_raqam']}")
    print(f"  mavzu (imlo xatosi eng yaqin mavzuga moslanganda): asl {a['mavzu_asl_m'] / n:.1%}, yashirilgan "
          f"{a['mavzu_yashirin_m'] / n:.1%}, bir xil {a['mavzu_bir_xil_m'] / n:.1%}")
    print(f"  shoshilinchlik asl va yashirilgan matnda bir xil: {a['shosh_bir_xil'] / n:.1%}")
    print(f"  javob fuqaro yozgan tilda: {a['til_mos'] / n:.1%}")
    return st, per, a, misses, extras


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).resolve().parent.parent / "llm/natija/gemma_items.json"))
