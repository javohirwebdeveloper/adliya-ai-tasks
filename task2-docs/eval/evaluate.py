"""Berilgan 6 hujjat (matnli va skaner, jami 12 PDF) bo'yicha aniqlikni o'lchash.

To'g'ri javoblar eval/gold.json da qo'lda belgilangan. Taqqoslash:
  rekvizitlar   jo'natuvchi (kichik-katta harf farqsiz), raqam, sana, imzolagan shaxs;
  topshiriqlar  har bir topshiriq matn o'xshashligi bo'yicha juftlanadi (>= 80%), so'ng
                ijrochilar to'plami va muddat (sana yoki matn) alohida tekshiriladi;
  OCR           skaner matni matnli PDF dagi asl matn bilan solishtiriladi (belgi xatosi, CER).

  python -m eval.evaluate
"""
import json
import re
import sys
import time
from pathlib import Path

from rapidfuzz import fuzz
from rapidfuzz.distance import Levenshtein

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app.layout import norm  # noqa: E402
from app.pipeline import analyze  # noqa: E402

GOLD = json.loads((ROOT / "eval" / "gold.json").read_text())
SYNTH = json.loads((ROOT / "eval" / "synthetic" / "gold.json").read_text())   # boshqacha formatdagi qo'shimcha hujjat


def key(s: str | None) -> str:
    s = norm(s or "").lower().replace('"', "")
    return re.sub(r"\s+", " ", s).strip(" .")


def same(a, b, cutoff=92) -> bool:
    return fuzz.ratio(key(a), key(b)) >= cutoff


def match_tasks(pred: list[dict], gold: list[dict]):
    pairs, used = [], set()
    for gi, g in enumerate(gold):
        best, best_s = None, 0
        for pi, p in enumerate(pred):
            if pi in used:
                continue
            s = fuzz.token_set_ratio(key(g["text"]), key(p["text"]))
            if s > best_s:
                best, best_s = pi, s
        if best is not None and best_s >= 80:
            used.add(best)
            pairs.append((gi, best))
    return pairs, [i for i in range(len(pred)) if i not in used]


def executors_ok(p: list[str], g: list[str]) -> bool:
    return len(p) == len(g) and all(any(same(x, y, 90) for x in p) for y in g)


def deadline_ok(p: dict, g: dict) -> bool:
    if g.get("date"):
        return p.get("date") == g["date"]
    return p.get("type") == g["type"] and same(p.get("text"), g["text"], 90)


def doc_text(pages) -> str:
    """Hujjat matni o'qish tartibida (qatorlar, so'ng jadval kataklari), ikkala yo'l uchun bir xil."""
    from app.layout import build_document
    parts = []
    for line in build_document(pages).lines:
        parts += [line.text] if line.kind == "text" else [" ".join(r) for r in line.table.rows]
    return key(" ".join(parts))


def main():
    rows, totals = [], {"req": [0, 0], "tp": 0, "fp": 0, "fn": 0, "ex": [0, 0], "dl": [0, 0]}
    fails, ocr = [], []
    def new():
        return dict(totals, req=[0, 0], ex=[0, 0], dl=[0, 0])
    by_kind = {"text": new(), "ocr": new(), "synth_text": new(), "synth_ocr": new()}
    docs = [(n, g, ROOT / "samples" / "matnli" / f"{n}.pdf", ROOT / "samples" / "skaner" / f"{n}_skaner.pdf", "")
            for n, g in GOLD.items()]
    docs += [(n, g, ROOT / "eval" / "synthetic" / f"{n}.pdf", ROOT / "eval" / "synthetic" / f"{n}_skaner.pdf", "synth_")
             for n, g in SYNTH.items()]
    for name, gold, text_path, scan_path, group in docs:
        for kind, path in ((group + "text", text_path), (group + "ocr", scan_path)):
            t0 = time.time()
            res = analyze(path.read_bytes())
            sec = time.time() - t0
            agg = by_kind[kind]
            req_ok = {}
            for f in ("sender", "number", "date", "signatory"):
                ok = same(res["requisites"].get(f), gold["requisites"][f], 95)
                req_ok[f] = ok
                agg["req"][0] += ok
                agg["req"][1] += 1
                if not ok:
                    fails.append(f"{path.name}: {f} = {res['requisites'].get(f)!r}, kutilgan {gold['requisites'][f]!r}")
            pairs, extra = match_tasks(res["tasks"], gold["tasks"])
            tp, fn = len(pairs), len(gold["tasks"]) - len(pairs)
            agg["tp"] += tp
            agg["fp"] += len(extra)
            agg["fn"] += fn
            ex_ok = dl_ok = 0
            for gi, pi in pairs:
                g, p = gold["tasks"][gi], res["tasks"][pi]
                e, d = executors_ok(p["executors"], g["executors"]), deadline_ok(p["deadline"], g["deadline"])
                ex_ok += e
                dl_ok += d
                if not e:
                    fails.append(f"{path.name}: {p['source']} ijrochi {p['executors']} != {g['executors']}")
                if not d:
                    fails.append(f"{path.name}: {p['source']} muddat {p['deadline']} != {g['deadline']}")
            for pi in extra:
                fails.append(f"{path.name}: ortiqcha topshiriq [{res['tasks'][pi]['source']}] {res['tasks'][pi]['text'][:60]}")
            for gi in set(range(len(gold["tasks"]))) - {g for g, _ in pairs}:
                fails.append(f"{path.name}: topilmagan topshiriq: {gold['tasks'][gi]['text'][:60]}")
            agg["ex"][0] += ex_ok
            agg["ex"][1] += tp
            agg["dl"][0] += dl_ok
            agg["dl"][1] += tp
            rows.append({"file": path.name, "kind": kind, "seconds": round(sec, 1), "requisites": f"{sum(req_ok.values())}/4",
                         "tasks": f"{tp}/{len(gold['tasks'])}", "extra": len(extra), "executors": f"{ex_ok}/{tp}",
                         "deadlines": f"{dl_ok}/{tp}", "ocr_conf": res["meta"]["ocr_confidence"]})
            print(rows[-1])

    # OCR sifati: skaner matni va matnli PDF matni orasidagi belgi xatosi (CER)
    from app.extract import extract
    for name, _, text_path, scan_path, _ in docs:
        a = doc_text(extract(text_path.read_bytes()))
        b = doc_text(extract(scan_path.read_bytes()))
        ocr.append({"doc": name, "cer": round(Levenshtein.distance(a, b) / max(len(a), 1), 4)})

    report = {"rows": rows, "by_kind": by_kind, "fails": fails, "ocr": ocr}
    (ROOT / "eval" / "results.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
    write_md(report)
    for k, a in by_kind.items():
        p = a["tp"] / max(a["tp"] + a["fp"], 1)
        r = a["tp"] / max(a["tp"] + a["fn"], 1)
        print(k, "rekvizit", a["req"], "topshiriq P/R", round(p, 3), round(r, 3), "ijrochi", a["ex"], "muddat", a["dl"])
    print("\n".join(fails) or "xato yo'q")


def pct(a, b):
    return f"{100 * a / b:.1f}% ({a}/{b})" if b else "-"


def write_md(rep):
    L = ["# Hujjat tahlili: natijalar", "",
         "Berilgan 6 ta hujjat, har biri matnli va skaner ko'rinishida (12 ta PDF). To'g'ri javoblar `eval/gold.json`.",
         "Qo'shimcha: boshqacha formatdagi buyruq (`eval/synthetic`, `make_synthetic.py` yasaydi): so'z bilan yozilgan sana,",
         "passiv gap, ikki qatorli lavozim, boshqacha jadval sarlavhasi. Birinchi urinishda 6 topshiriqdan 3 tasining ijrochisi",
         "chala chiqqan edi, qoidalar umumlashtirilgach hammasi to'g'ri.", "",
         "| Turi | Rekvizitlar | Topshiriq topildi (recall) | Ortiqcha (precision) | Ijrochi to'g'ri | Muddat to'g'ri |",
         "|---|---|---|---|---|---|"]
    names = {"text": "Matnli PDF", "ocr": "Skaner (OCR)", "synth_text": "Qo'shimcha: boshqa formatdagi buyruq, matnli",
             "synth_ocr": "Qo'shimcha: boshqa formatdagi buyruq, skaner"}
    for k, a in rep["by_kind"].items():
        name = names[k]
        L.append(f"| {name} | {pct(*a['req'])} | {pct(a['tp'], a['tp'] + a['fn'])} | {pct(a['tp'], a['tp'] + a['fp'])} | "
                 f"{pct(*a['ex'])} | {pct(*a['dl'])} |")
    L += ["", "## Har bir fayl", "", "| Fayl | Rekvizit | Topshiriq | Ortiqcha | Ijrochi | Muddat | OCR ishonchi | Vaqt, s |",
          "|---|---|---|---|---|---|---|---|"]
    for r in rep["rows"]:
        L.append(f"| {r['file']} | {r['requisites']} | {r['tasks']} | {r['extra']} | {r['executors']} | {r['deadlines']} | "
                 f"{', '.join(map(str, r['ocr_conf'])) or '-'} | {r['seconds']} |")
    L += ["", "## OCR sifati", "", "Skaner matni matnli PDF dagi asl matn bilan solishtirildi (belgilar bo'yicha xato ulushi, CER):", "",
          "| Hujjat | CER |", "|---|---|"]
    for o in rep["ocr"]:
        L.append(f"| {o['doc']} | {100 * o['cer']:.2f}% |")
    L += ["", "## Xatolar", ""] + ([f"- {f}" for f in rep["fails"]] or ["Xato topilmadi."])
    (ROOT / "eval" / "results.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
