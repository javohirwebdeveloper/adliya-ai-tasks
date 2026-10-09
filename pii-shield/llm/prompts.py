"""Gemma uchun so'rovlar va javobni o'qish."""
import json
import random
import re

TOPICS = ["Pasport, propiska va FHDYo", "Notarius va meros", "Avtomobil va haydovchilik guvohnomasi",
          "Tadbirkorlik va soliq", "Mehnat, pensiya va nafaqa", "Sog'liq va ta'lim", "Sud, harbiy xizmat va huquq",
          "Kommunal xizmatlar, pochta va boshqa hujjatlar", "Onlayn davlat xizmatlari"]
PII = {"ISM": "to'liq ism-sharif (familiya, ism, otasining ismi)", "PASPORT": "pasport seriyasi va raqami (masalan AB1234567)",
       "JSHSHIR": "JSHSHIR (14 xonali raqam)", "TELEFON": "telefon raqami (+998 bilan yoki 90 123 45 67 shaklida)",
       "KARTA": "bank kartasi raqami (Uzcard 8600 yoki Humo 9860, 16 xonali)",
       "MANZIL": "yashash manzili (viloyat, tuman, mahalla yoki ko'cha, uy raqami)",
       "TUG_SANA": "tug'ilgan sana", "EMAIL": "elektron pochta", "AVTO": "avtomobil davlat raqami (masalan 01 A 123 BC)",
       "STIR": "STIR (9 xonali soliq raqami)"}
STYLES = ["rasmiy ariza", "Telegram'dagi qisqa xabar, so'zlashuv tilida", "shikoyat xati, hissiyot bilan",
          "oddiy savol, bir-ikki gap"]
SCRIPTS = ["o'zbek lotin", "o'zbek lotin", "o'zbek kirill", "rus tili"]


def generation_jobs(n_per_topic: int, seed: int = 11):
    r = random.Random(seed)
    jobs = []
    for t in TOPICS:
        for _ in range(n_per_topic):
            kinds = r.sample(list(PII), r.randint(2, 5))
            style, script = r.choice(STYLES), r.choice(SCRIPTS)
            prompt = (
                f"Sen O'zbekiston fuqarosisan va davlat idorasiga murojaat yozyapsan. Mavzu: «{t}».\n"
                f"Uslub: {style}. Til va yozuv: {script}.\n"
                "Murojaatda o'zing haqingda quyidagi shaxsiy ma'lumotlar bo'lsin (to'qib chiqarilgan, lekin haqiqiyga o'xshash): "
                + "; ".join(PII[k] for k in kinds) + ".\n"
                "Murojaat tabiiy bo'lsin, bir xil qolipda bo'lmasin, 2-6 gap. Faqat JSON qaytar, boshqa hech narsa yozma:\n"
                '{"matn": "murojaat matni", "shaxsiy": [{"tur": "' + "|".join(kinds) + '", "qiymat": "matndagi aynan o\'sha qiymat"}]}')
            jobs.append({"topic": t, "style": style, "script": script, "kinds": kinds, "prompt": prompt})
    return jobs


def assistant_prompt(text: str) -> str:
    return ("Sen davlat idorasida murojaatlarni saralovchi yordamchisan. Quyidagi murojaatni o'qib, faqat JSON qaytar.\n"
            "Matnda [ISM_1], [TELEFON_1] kabi belgilar bo'lishi mumkin: bu yashirilgan shaxsiy ma'lumot. Ularni javobda "
            "o'zgartirmasdan ishlat, o'zingdan ism, raqam yoki manzil to'qima.\n"
            "mavzu: quyidagilardan biri, aynan shu yozilishda: " + "; ".join(TOPICS) + ".\n"
            "xulosa xodim uchun, o'zbek tilida lotin yozuvida. javob_loyihasi esa fuqaro yozgan tilda va yozuvda: "
            "ruscha murojaatga rus tilida, o'zbek kirillida yozilganga kirillda, lotinda yozilganga lotinda.\n"
            '{"mavzu": "...", "shoshilinch": true yoki false, "xulosa": "1-2 gapli qisqa mazmun", '
            '"javob_loyihasi": "fuqaroga 2-3 gapli xushmuomala javob"}\n\nMurojaat:\n' + text)


def reply_lang(s: str) -> str:
    """Javob qaysi tilda: lotin harflari ko'p bo'lsa o'zbek lotin, kirillda ў/қ/ғ/ҳ bo'lsa o'zbek kirill, aks holda rus."""
    cyr = len(re.findall(r"[А-Яа-яЁёЎўҚқҒғҲҳ]", s))
    if cyr <= len(re.findall(r"[A-Za-z]", s)):
        return "o'zbek lotin"
    return "o'zbek kirill" if re.search(r"[ЎўҚқҒғҲҳ]", s) else "rus tili"


def parse_json(s: str):
    if not s:
        return None
    s = re.sub(r"^```(?:json)?|```$", "", s.strip(), flags=re.M).strip()
    m = re.search(r"\{.*\}", s, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
