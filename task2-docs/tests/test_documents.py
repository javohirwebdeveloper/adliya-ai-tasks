"""Berilgan 12 ta PDF va boshqacha formatdagi buyruq: rekvizitlar, topshiriqlar, ijrochi va muddat to'liq mos bo'lishi kerak."""
import json
from pathlib import Path

import pytest

from app.pipeline import analyze
from eval.evaluate import deadline_ok, executors_ok, match_tasks, same

ROOT = Path(__file__).resolve().parent.parent
GOLD = json.loads((ROOT / "eval/gold.json").read_text())
SYNTH = json.loads((ROOT / "eval/synthetic/gold.json").read_text())
CASES = [(f"samples/matnli/{n}.pdf", g) for n, g in GOLD.items()] + [(f"samples/skaner/{n}_skaner.pdf", g) for n, g in GOLD.items()]
CASES += [(f"eval/synthetic/{n}.pdf", g) for n, g in SYNTH.items()] + [(f"eval/synthetic/{n}_skaner.pdf", g) for n, g in SYNTH.items()]


@pytest.mark.parametrize("path,gold", CASES, ids=[c[0].split("/")[-1] for c in CASES])
def test_document(path, gold):
    res = analyze((ROOT / path).read_bytes())
    for field in ("sender", "number", "date", "signatory"):
        assert same(res["requisites"][field], gold["requisites"][field], 95), field
    pairs, extra = match_tasks(res["tasks"], gold["tasks"])
    assert len(pairs) == len(gold["tasks"]) and not extra
    for gi, pi in pairs:
        assert executors_ok(res["tasks"][pi]["executors"], gold["tasks"][gi]["executors"]), res["tasks"][pi]["source"]
        assert deadline_ok(res["tasks"][pi]["deadline"], gold["tasks"][gi]["deadline"]), res["tasks"][pi]["source"]
        assert res["tasks"][pi]["boxes"], "manba qutisi bo'lishi kerak"


def test_rejects_non_pdf():
    from fastapi.testclient import TestClient
    from app.web import app
    c = TestClient(app)
    assert c.post("/api/analyze", files={"file": ("x.pdf", b"hello", "application/pdf")}).status_code == 400
