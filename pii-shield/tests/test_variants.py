"""Yozilish shakllari matritsasi (eval/stress.py): har bir shakl to'liq yashirilishi, oddiy matn esa tegilmasligi shart."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from eval.stress import SHAXSIY, run  # noqa: E402


def test_all_variants_hidden_and_plain_text_untouched():
    leaks, extras = run(show=False)
    assert len(SHAXSIY) > 300
    assert leaks == [], leaks
    assert extras == [], extras
