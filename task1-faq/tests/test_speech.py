"""Ovoz moduli: uzun xabarni bo'lish va qisqa (tasodifiy) yozuvni o'tkazib yuborish. Model kerak emas."""
import threading

import numpy as np

from app.speech import SR, Speech, split_long


def test_short_message_is_not_split():
    a = np.zeros(15 * SR, dtype=np.float32)
    assert len(split_long(a)) == 1


def test_long_message_is_split_at_pause():
    a = np.random.default_rng(0).normal(0, 0.3, 50 * SR).astype(np.float32)
    a[17 * SR:int(17.3 * SR)] = 0                                 # gaplar orasidagi jimlik
    parts = split_long(a)
    assert sum(len(p) for p in parts) == len(a)                 # hech narsa yo'qolmaydi
    assert all(len(p) <= 20 * SR for p in parts)
    assert 17 * SR <= len(parts[0]) <= int(17.3 * SR)           # birinchi kesim aynan jimlik ichida


def test_accidental_tap_returns_empty():
    sp = Speech.__new__(Speech)                                  # modelni yuklamasdan
    sp._run = lambda a: "xato"
    sp._lock = threading.Lock()
    assert sp.recognize(np.zeros(SR // 10, dtype=np.float32)) == ""
    assert sp.recognize(np.zeros(SR, dtype=np.float32)) == "Xato"
