"""Yozilish shakllari bo'yicha qattiq sinov: har bir tur uchun odamlar yozadigan barcha ko'rinishlar.

    python -m eval.stress            # sizib chiqqan va ortiqcha yashirilganlarni ko'rsatadi

SHAXSIY: matnda {..} ichidagi qiymat to'liq yashirilishi shart.
ODDIY:   shaxsiy ma'lumoti yo'q matn, hech narsa yashirilmasligi shart.
"""
import itertools
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shield import Shield  # noqa: E402

DOC = [a + s + d for a, s, d in itertools.product(
    ["AA", "aa", "Ad", "АА"], ["", " ", "-", ".", "/", " № ", "№"], ["1234567", "123 45 67", "123-45-67"])]
SHAXSIY = (
    # hujjat raqami: pasport, ID karta, prava (turli kontekst bilan)
    [f"pasportim {{{d}}}" for d in DOC] + [f"prava muddati o'tdi, {{{d}}}" for d in DOC]
    + [t.format(d) for t in ("ID karta: {{{}}}", "паспорт серии {{{}}}") for d in ("AB1234567", "ab 1234567", "АВ 1234567")]
    + ["Мой паспорт {AC 2345678}", "{AD1234567} raqamli ID karta", "texpasport {AAF 1234567}"]
    # JSHSHIR
    + [f"{k} {{{v}}}" for k, v in itertools.product(
        ["JSHSHIR", "jshshir:", "ЖШШИР", "ПИНФЛ", "PINFL", "shaxsiy raqamim"],
        ["31505901234567", "3 150590 1234567", "315 059 012 34567", "315-059-012-34567"])]
    + ["{31505901234567} bu mening raqamim"]
    # telefon
    + [f"tel {{{p}}}" for p in ("+998 90 123 45 67", "+998(90)1234567", "998901234567", "90 123 45 67", "901234567",
                                 "90-123-45-67", "(90) 123-45-67", "+998 90 123-45-67", "+99890 1234567",
                                 "93 555 44 33", "33 555 44 33", "88 555 44 33", "71 200 00 00", "+7 916 123 45 67",
                                 "+998 66 233 45 67", "66 233 45 67", "+998-90-123-45-67")]
    + ["Телефон: {+998 (90) 765-43-21}", "мой номер {90 765 43 21}", "telefonim {+998901234567}, shu raqamga",
       "tel {901 234 567}", "tel {90 1234567}", "tel {90 12 345 67}", "tel {+998 90 12 34 567}", "nomer {+998 99 8887766}",
       "telefon raqamim {+44 20 7946 0958}", "{+998 90 123 45 67} ga qo'ng'iroq qiling"]
    # karta, hisob
    + [f"karta {{{c}}}" for c in ("8600 1234 5678 9012", "8600123456789012", "8600-1234-5678-9012", "9860 1601 0123 4567",
                                    "4278 3100 1234 5678", "5614 6812 3456 7890")]
    + ["hisob raqam {20208000900123456001}", "x/r {2020 8000 9001 2345 6001}"]
    # STIR
    + [f"{k} {{{v}}}" for k, v in itertools.product(["STIR", "stir:", "INN", "ИНН", "СТИР", "soliq raqamim"],
                                                     ["305123987", "305 123 987"])]
    + ["{305123987} STIR raqamim"]
    # email
    + ["email {a.karimov@mail.uz}", "почта {ivanov_88@gmail.com}", "{karimov.akmal@umail.uz} ga yozing"]
    # avtomobil
    + [f"mashinam {{{a}}}" for a in ("01 A 123 BC", "01A123BC", "01 123 ABC", "01a123bc", "01 a 123 bc", "10 777 AAA",
                                      "01 А 123 ВС")]
    # ism
    + ["Men {Karimov Akmal Rustam o'g'li}", "Men {Karimov Akmal Rustam ugli}", "{Yusupova Malika Anvar qizi}",
       "{KARIMOV AKMAL RUSTAMOVICH}", "{КАРИМОВ АКМАЛ}", "fuqaro {KARIMOV AKMAL}", "{karimov akmal} ariza berdi",
       "{Каримов Акмал Рустамович}", "{Петрова Анна Сергеевна}", "{Karimov A.R.}", "{A.R. Karimov}", "{Каримов А.Р.}",
       "men {Dilshod}", "{Dilshod} aka", "ismim {Malika}", "Меня зовут {Анна Петрова}", "{To'xtasinov Bahodir}",
       "{Karimova-Yusupova Malika}", "Hurmatli {Ziyodulla Mamatqulov}!", "{Abdullayev Sherzod} bilan gaplashdim",
       "ijrochi: {N. Sobirov}", "{Rahimov Javohir}ga javob yuborilsin"]
    # tug'ilgan sana
    + ["tug'ilgan sanam {12.04.1991}", "{12/04/1991} da tug'ilganman", "{1991-yil 12-aprel}da tug'ilganman",
       "{12 aprel 1991} yilda tug'ilgan", "Дата рождения: {12.04.1991}", "родился {12 апреля 1991} года",
       "д.р. {12.04.1991}", "туғилган санаси: {12.04.1991}", "tug'ilgan kunim {1991.04.12}"]
    # manzil
    + ["{Navoiy ko'chasi 12-uy}", "{Navoiy ko'chasi, 12 uy}", "{Navoiy ko'chasi, 12-uy, 5-xonadon}",
       "Chilonzor tumani, {9-kvartal, 15-uy}", "{4-mavze, 23-uy}", "{ul. Navoi 12, kv. 5}", "{улица Навои, дом 12, кв. 5}",
       "{Navbahor MFY}", "{Navbahor mahallasi}da yashayman", "{Бунёдкор кўчаси, 12-уй}", "{Amir Temur shoh ko'chasi 45}",
       "{Navoiy k., 12-uy}", "{пр. Мустакиллик, 5}", "Qoraqamish {2/1-mavze, 15-uy}", "{Bog'ishamol ko'chasi 7-a uy}",
       "{12-uy, 45-xonadon}", "manzil: {Navoiy 12-uy}"]
    + ["{КАРИМОВ АКМАЛ РУСТАМОВИЧ}", "{KARIMOV JASURBEK}", "{Karimov A.}", "{Akmal Karimov}", "{АКМАЛ КАРИМОВ}",
       "{Karimov Akmal Rustam o‘g‘li}", "{Karimov Akmal Rustamovich}ga", "{Tursunova Dilnoza Bahodirovna}",
       "{Akmal Rustamovich}, assalomu alaykum", "{Алишер Олимович}, здравствуйте", "Уважаемая {Анна Сергеевна}!",
       "{karimov jasurbek} ariza berdi", "{jasurbek karimov} ariza berdi", "{Kim Viktor}", "{Pak Elena}",
       "{Tsoy Sergey} bilan", "men {Jasurbek}", "{Sardorbek} aka", "{Toshmatov Islombek}"]
    + ["email {akmal(at)mail.uz}", "pochtam {akmal [at] mail.uz}", "telegram {@akmal_karimov}", "tg: {@Malika_2001}",
       "{Navoiy ko'chasi 12/5}", "{Navoiy ko'chasi, 12-uy 5-xonadon}"]
)
ODDIY = [
    "Buyruq № 245, 10.02.2026. Ijrochi: Moliya bo'limi. Muddat: 15 kun.",
    "PQ-3666-son qarorning 2-bandiga ko'ra, 2026-yil 1-iyulga qadar 14 ta hudud bo'yicha hisobot taqdim etilsin.",
    "Davlat boji 375 000 so'm, ijara 3 oy va 1250000 so'm, jami 5 mln so'm, $500.",
    "Sud qarori 2-1234/2026, O'RQ-547-son Qonun, PF-60 farmon, VMQ 123-son qaror.",
    "Toshkent shahri, Chilonzor tumani, Adliya vazirligi, Davlat xizmatlari markazi, Oliy Majlis.",
    "Ipoteka bank va Xalq banki orqali to'lov qilsa bo'ladi. Cobalt 2020 va Nexia 3 mashinalari.",
    "Ish vaqti 09:00-18:00, call-markaz 1008, ishonch telefoni 1148.",
    "Kartaning faqat oxirgi 4 raqami: **** 4521. To'lov ID: 7781234.",
    "Ariza 2026-yil 15-sentabrda qabul qilingan, 10 ish kunida ko'rib chiqiladi.",
    "Mahallada ko'chaga sahna qurib konsert o'tkazmoqchimiz. Yaqinda o'g'li tug'ildi.",
    "Yangi tahrirdagi Mehnat kodeksining 120-moddasi. 2024-2025 yillar uchun 15% chegirma.",
    "To'lov Humo kartasi orqali amalga oshirildi. O'zbekiston Milliy universiteti.",
    "Здравствуйте, подскажите порядок регистрации ООО и сроки, госпошлина 340 000 сум.",
    "Ассалому алайкум, ID карта олиш учун қандай ҳужжатлар керак?",
    "1-sinf o'quvchilari 2026-yil 2-sentabrdan o'qiydi, 3-4 oy ichida natija.",
    "Mahallada 3 uy buzildi, 10 000 som yig'ildi. FHDYO, DXM, MFY, YHXB, IIV, JSHSHIR va STIR nima?",
    "Narxi 750 000 000 so'm, 120 000 dollar. Oylik 5 500 000 so'm, ishchilar soni 1 234 567 ta.",
    "TOSHKENT SHAHRI ADLIYA BOSHQARMASI. O'ZBEKISTON RESPUBLIKASI VAZIRLAR MAHKAMASI QARORI.",
    "Davlat raqami belgilarini olish tartibi, prava olish uchun 10 ta dars va 2 ta imtihon.",
]


def run(show=True):
    sh = Shield()
    leaks, extras = [], []
    for case in SHAXSIY:
        text = re.sub(r"[{}]", "", case)
        m = re.search(r"\{(.+?)\}", case)
        s = m.start()
        e = s + len(m.group(1))
        cov = [False] * len(text)
        for _, a, b in sh.detect(text):
            cov[a:b] = [True] * (b - a)
        need = [i for i in range(s, e) if text[i].isalnum()]
        if sum(cov[i] for i in need) / len(need) < 1.0:
            leaks.append((case, sh.mask(text)[0]))
    for text in ODDIY:
        found = [(k, text[a:b]) for k, a, b in sh.detect(text)]
        if found:
            extras.append((text[:70], found))
    if show:
        print(f"Shaxsiy: {len(SHAXSIY) - len(leaks)}/{len(SHAXSIY)} to'liq yashirildi; oddiy matn: "
              f"{len(ODDIY) - len(extras)}/{len(ODDIY)} toza")
        for c, m in leaks:
            print("  SIZDI:", c, " ->", m)
        for t, f in extras:
            print("  ORTIQCHA:", t, f)
    return leaks, extras


if __name__ == "__main__":
    run()
