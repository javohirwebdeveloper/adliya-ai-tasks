import datetime as dt

import pytest

from app.dates import deadline

D = dt.date(2026, 9, 8)          # seshanba


@pytest.mark.parametrize("text,cell,want", [
    ("loyihasini bir oy muddatda ishlab chiqsin", False, ("nisbiy", "2026-10-08")),
    ("integratsiyasini 2026-yil 1-iyulga qadar ta'minlasin", False, ("sana", "2026-07-01")),
    ("ishlarini 2026-yil 15-martdan boshlab tashkil etsin", False, ("boshlanish", "2026-03-15")),
    ("har oyda Kengashga ma'lumot berib borsin", False, ("davriy", None)),
    ("takliflarni 01.10.2026 yilgacha ishlab chiqsin", False, ("sana", "2026-10-01")),
    ("takliflarni o'n kun muddatda kiritsin", False, ("nisbiy", "2026-09-18")),
    ("ma'lumotni uch ish kuni ichida taqdim etishingiz so'raladi", False, ("nisbiy", "2026-09-11")),
    ("har oyning 5-sanasiga qadar ma'lumot berib borsin", False, ("davriy", None)),
    ("har chorak yakunidan keyingi oyning 10-sanasiga qadar axborot kiritsin", False, ("davriy", None)),
    ("tizim tayyor bo'lgandan so'ng 2 oy ichida", True, ("shartli", None)),
    ("texnik topshiriq tasdiqlangandan so'ng 3 oy ichida", True, ("shartli", None)),
    ("2026-yil 5-oktabr", True, ("sana", "2026-10-05")),
    ("18.09.2026", True, ("sana", "2026-09-18")),
    ("har haftaning juma kuni", True, ("davriy", None)),
    ("doimiy", True, ("doimiy", None)),
    ("hisobotni 3 oktyabr 2026 yilgacha taqdim etsin", False, ("sana", "2026-10-03")),
    ("2026 yil 15 noyabrgacha tayyorlasin", False, ("sana", "2026-11-15")),
])
def test_deadline(text, cell, want):
    d = deadline(text, D, cell=cell)
    assert (d["type"], d["date"]) == want


def test_signing_date_is_not_deadline():
    # "2-sentabrda imzolangan memorandum" muddat emas
    assert deadline("Korxona va Markaz o'rtasida 2026-yil 2-sentabrda imzolangan memorandum", D) is None
