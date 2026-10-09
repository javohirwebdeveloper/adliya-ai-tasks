"""Qalqon testlari: har tur topiladi, oddiy raqam va sanalar yashirilmaydi, qaytarish aniq."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shield import Shield  # noqa: E402
from shield.rules import luhn, valid_pinfl  # noqa: E402

S = Shield()


def kinds(text):
    return [k for k, _, _ in S.detect(text)]


def test_all_types_latin():
    t = ("Men Karimov Akmal Rustam o'g'li, pasport AB4567123, JSHSHIR 31505901234567, tel +998 90 123 45 67, "
         "karta 8600 1234 5678 9012, email a.karimov@mail.uz, Bunyodkor ko'chasi, 12-uy.")
    assert set(kinds(t)) == {"ISM", "PASPORT", "JSHSHIR", "TELEFON", "KARTA", "EMAIL", "MANZIL"}


def test_cyrillic_and_russian():
    assert set(kinds("Мен Жумабоев Жавохир Акмал ўғли, паспорт AB 7654321")) == {"ISM", "PASPORT"}
    assert set(kinds("Меня зовут Петрова Анна Сергеевна, ИНН 412345678")) == {"ISM", "STIR"}


def test_region_stays_street_hidden():
    masked, key = S.mask("Samarqand viloyati, Urgut tumani, Navbahor mahallasi, 7-uy")
    assert masked.startswith("Samarqand viloyati, Urgut tumani, [MANZIL_1]")


def test_no_false_positives_on_documents():
    t = "Buyruq № 245, 10.02.2026. 2026-yil 1-iyulga qadar 14 ta hudud bo'yicha hisobot. PQ-3666-son qaror, 375 000 so'm."
    assert S.detect(t) == []


def test_same_value_same_tag_and_unmask():
    t = "Karimov Akmal ariza berdi. Karimov Akmal ga javob yuborilsin, tel 901234567."
    masked, key = S.mask(t)
    assert masked.count("[ISM_1]") == 2 and S.unmask(masked, key) == t


def test_validators():
    assert valid_pinfl("31505901234567") and not valid_pinfl("31545901234567")    # 45-oy yo'q
    assert luhn("4532015112830366") and not luhn("4532015112830367")


def test_keyword_then_value():
    """Kalit so'z bilan qiymat orasida so'zlar bo'lsa ham: "STIR raqamim ...", "pasport seriyasi va raqami ..."."""
    t = ("STIR raqamim 784592310, JSHSHIR raqamim: 84592136740215. Pasportim seriyasi va raqami AB459872. "
         "Мой паспорт серии AB789456, ИНН 554433221.")
    assert sorted(kinds(t)) == ["JSHSHIR", "PASPORT", "PASPORT", "STIR", "STIR"]


def test_russian_address_and_birth_date():
    masked, _ = S.mask("Проживаю по адресу: Ташкентский район, улица Амира Темура, дом 45. Дата рождения: 15.05.1988.")
    assert masked == "Проживаю по адресу: Ташкентский район, [MANZIL_1]. Дата рождения: [TUG_SANA_1]."
    masked, _ = S.mask("Я родился 12.05.1958 года, живу: махалля Янгикат, ул. Амир Темур 45.")
    assert masked == "Я родился [TUG_SANA_1] года, живу: [MANZIL_1]."


def test_long_numbers_and_money():
    masked, _ = S.mask("Uzcard 8600 1234567890123456 kartamga 125 000 000 000 so'm qaytarilsin, hisob 2020 8000 9051 2345 6001.")
    assert masked == "Uzcard [KARTA_1] kartamga 125 000 000 000 so'm qaytarilsin, hisob [HISOB_1]."


def test_name_with_suffix():
    masked, key = S.mask("Javob To'hirxon Karimovga yuborilsin. Men Karimov Akmal Rustam o'g'liman.")
    assert masked == "Javob [ISM_1]ga yuborilsin. Men [ISM_2]man." and key["[ISM_1]"] == "To'hirxon Karimov"
    assert kinds("To'lov Humo kartasi orqali, O'zbekiston Milliy universiteti.") == []


def test_blind_set_2_patterns():
    """2-ko'r to'plamda topilgan naqshlar."""
    m = lambda t: S.mask(t)[0]
    assert m("Азиззода Сардорбек Олимбек ўғли (15.05.1992 йил тўғилган)") == "[ISM_1] ([TUG_SANA_1] йил тўғилган)"
    assert m("Men 1990.05.15 yili tug'ilganman.") == "Men [TUG_SANA_1] yili tug'ilganman."
    assert m("Ташкентская область, махалля «Озодлик», ул. Амир Темура, д. 45") == "Ташкентская область, [MANZIL_1]"
    assert m("Chilonzor tumani, 15-tor ko'chasi, 7-uy") == "Chilonzor tumani, [MANZIL_1]"
    assert m("паспорт серии 4512 № 8903412") == "паспорт серии [PASPORT_1]"
    assert m("hal qilish uchun 485920137 STIR raqamim") == "hal qilish uchun [STIR_1] STIR raqamim"
    assert m("Men, Abdullayev Jasurbek O‘tmonovich, harbiy") == "Men, [ISM_1], harbiy"
    assert m("Menbekov Rustambek Omadbekman, STIR") == "[ISM_1]man, STIR"
    assert m("Yunusobodda yashaydigan Nazarovman.") == "Yunusobodda yashaydigan [ISM_1]man."


def test_blind_set_3_patterns():
    """3-ko'r to'plamda topilgan naqshlar."""
    m = lambda t: S.mask(t)[0]
    assert m("Mening soliq raqamim 584921037 bo'lib") == "Mening soliq raqamim [STIR_1] bo'lib"
    assert m("Мой ПИНФЛ 584923017. STIR 88492031 raqamli") == "Мой ПИНФЛ [JSHSHIR_1]. STIR [STIR_1] raqamli"
    assert m("Men Toshkent tumani, Amirxon mahallasida yashayman.") == "Men Toshkent tumani, [MANZIL_1]da yashayman."
    assert m("Jizzax viloyati, Arxa qishloq, 15-uyda") == "Jizzax viloyati, [MANZIL_1]"
    assert m("Живу в Чиланзарском районе, по улице Амира Темура, дом 45.") == "Живу в Чиланзарском районе, по [MANZIL_1]."
    assert m("Я, уроженец 15.05.1988 года.") == "Я, уроженец [TUG_SANA_1] года."
    assert m("tug'ilgan sanam esa 1992-yil 15-may.") == "tug'ilgan sanam esa [TUG_SANA_1]."
