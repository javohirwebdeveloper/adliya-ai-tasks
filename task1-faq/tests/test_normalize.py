from app.normalize import clean_kb_question, cyr_to_lat, expand, load_synonyms, normalize, query_variants, strip_fillers
from app.search import content_words, smalltalk_kind

SYN = load_synonyms("data/synonyms.csv")


def test_apostrophes():
    assert normalize("O‘zbekiston  boʻyicha  ma`lumot") == "O'zbekiston bo'yicha ma'lumot"


def test_cyrillic_to_latin():
    assert cyr_to_lat("Паспортни қандай алмаштирса бўлади?") == "Pasportni qanday almashtirsa bo'ladi?"
    assert cyr_to_lat("Ер, еланг, ёки юз") == "Yer, yelang, yoki yuz"


def test_variants_keep_russian_original():
    v = query_variants("как получить загранпаспорт", SYN)
    assert v[0].startswith("как получить") and len(v) == 2


def test_slang_expansion():
    assert "haydovchilik guvohnomasi" in expand("pravamning muddati tugadi", SYN)
    assert "doimiy ro'yxatga olish" in expand("propiskaga qo'yish", SYN)
    assert expand("pasport almashtirish", SYN) == "pasport almashtirish"


def test_fillers_and_templates():
    assert strip_fillers("Assalomu alaykum, pasport qancha turadi? Rahmat") == "pasport qancha turadi"
    assert clean_kb_question("Iltimos, ayting: pasport qanday olinadi?") == "Pasport qanday olinadi?"


def test_short_and_smalltalk():
    assert content_words("prava") == 1 and content_words("muddat") == 1
    assert content_words("pravamning muddati tugadi, qayerda almashtiraman") >= 3
    assert smalltalk_kind("Salom!") == "greeting" and smalltalk_kind("katta rahmat") == "thanks"
    assert smalltalk_kind("salom, pasport qancha turadi") is None
