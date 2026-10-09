"""QLoRA mashqi uchun ma'lumot: rasmiy topshiriq gapi -> {"ijrochi", "muddat", "muddat_turi"} (JSON).

train.jsonl       sun'iy gaplar (o'qitish uchun)
test_synth.jsonl  sun'iy gaplar, lekin o'qitishda UMUMAN uchramagan bo'lim nomlari va ishlar bilan
test_real.jsonl   ish beruvchi bergan 6 ta haqiqiy hujjatdagi 13 ta topshiriq gapi (ijrochisi gap ichida bo'lganlari)
Haqiqiy hujjatlardagi nomlar ("Ro'yxatga olish", "Sun'iy intellekt" ...) o'qitish lug'atiga ataylab kiritilmagan.
"""
import json
import random
import re
import unicodedata
from pathlib import Path

OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)
R = random.Random(42)

MONTHS = ["yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr"]
NUM = ["bir", "ikki", "uch", "besh", "o'n", "o'n besh", "yigirma", "o'ttiz", "3", "5", "7", "10", "15", "20", "30"]

TRAIN = dict(
    domains=["Moliya-iqtisodiyot", "Inson resurslarini boshqarish", "Jamoatchilik bilan aloqalar", "Xalqaro hamkorlik",
             "Ijro nazorati", "Statistika va tahlil", "Litsenziyalash", "Notariat faoliyatini muvofiqlashtirish",
             "Ichki audit", "Davlat xizmatlarini rivojlantirish", "Kadrlar tayyorlash", "Buxgalteriya hisobi",
             "Texnik ta'minot", "Tarmoq infratuzilmasi", "Elektron hukumat loyihalari", "Ma'muriy-xo'jalik",
             "Shartnomalar va xaridlar", "Metodologiya", "Tashqi aloqalar", "Ichki nazorat", "Mehnatni muhofaza qilish",
             "Arxiv", "Kommunikatsiya", "Monitoring va baholash", "Hujjatlar bilan ishlash"],
    single=["Hududiy boshqarmalar", "Viloyat adliya boshqarmalari", "Tuman (shahar) adliya bo'limlari", "Agentlik",
            "Inspeksiya", "Ishchi guruh", "Respublika komissiyasi", "Vazirlik", "Departament", "Loyiha ofisi"],
    roles=["mas'ul kotib", "bosh hisobchi", "yuriskonsult", "matbuot kotibi", "bo'lim boshlig'i", "tizim administratori"],
    objects=["xodimlarning malakasini oshirish rejasini", "idoraviy axborot tizimlarining texnik holatini",
             "byudjet mablag'larining sarflanishi bo'yicha hisobotni", "elektron hujjat aylanishi tizimini",
             "normativ-huquqiy hujjatlar loyihalarini", "ma'lumotlar bazasining zaxira nusxasini", "tadbirlar rejasini",
             "hududiy bo'linmalar faoliyati monitoringini", "xizmat ko'rsatish standartlarini",
             "davlat xaridlari bo'yicha takliflarni", "ichki tartib qoidalari loyihasini", "server uskunalarining ro'yxatini",
             "xalqaro shartnomalar ijrosi bo'yicha ma'lumotni", "litsenziya berish tartibini soddalashtirish takliflarini",
             "axborot resurslarini yangilash jadvalini", "kadrlar zaxirasi ro'yxatini", "ommaviy tadbirlar rejasini",
             "rasmiy veb-saytdagi ma'lumotlarni", "statistik hisobot shakllarini", "texnik topshiriq loyihasini",
             "arxiv hujjatlarini raqamlashtirish rejasini", "mehnat xavfsizligi bo'yicha yo'riqnomani",
             "xarajatlar smetasini", "tashkiliy tuzilmani takomillashtirish takliflarini", "ish yuritish yo'riqnomasini"],
    topics=["mazkur qaror ijrosi", "rejadagi tadbirlar ijrosi", "loyiha holati", "topshiriqlar bajarilishi",
            "byudjet ijrosi", "xodimlar o'qishi"],
    subjects=["Choraklik hisobot", "Umumlashtirilgan ma'lumot", "Tahliliy ma'lumotnoma", "Yakuniy hisobot",
              "Takliflar to'plami"],
)
TEST = dict(
    domains=["Kiberxavfsizlik", "Yuridik ta'lim", "Sud ekspertizasi", "Intellektual mulk", "Murojaatlar bilan ishlash",
             "Strategik rejalashtirish", "Tashkiliy-nazorat", "Ma'lumotlar bazasini yuritish", "Innovatsion rivojlantirish",
             "Korrupsiyaga qarshi kurashish", "Raqamli transformatsiya", "Huquqiy targ'ibot"],
    single=["Hududiy markazlar", "Ekspertlar kengashi", "Qo'mita", "Shahar bo'limlari"],
    roles=["loyiha rahbari", "bosh mutaxassis", "kotibiyat mudiri"],
    objects=["fuqarolar murojaatlari tasnifini", "kiberhujumlarga qarshi choralar rejasini", "yuridik klinikalar faoliyatini",
             "ekspertiza xulosalari reyestrini", "patent talabnomalari navbatini", "strategik rivojlanish konsepsiyasini",
             "korrupsiyaviy xavflar xaritasini", "huquqiy targ'ibot materiallarini", "ma'lumotlar sifatini tekshirish tartibini",
             "raqamli xizmatlar katalogini"],
    topics=["dastur ijrosi", "monitoring natijalari"],
    subjects=["Oylik ma'lumot", "Ekspert xulosasi"],
)
UNITS = ["boshqarmasi", "bo'limi", "departamenti", "xizmati", "sektori", "guruhi", "laboratoriyasi", "markazi", "inspeksiyasi"]
OWNERS = ["Agentlikning", "Vazirlikning", "Markazning", "Inspeksiyaning", "Departamentning"]
TARGETS = ["Kengashga", "Vazirlikka", "rahbariyatga", "Agentlikka", "Komissiyaga", "Ijro nazorati boshqarmasiga",
           "Vazirlikning Ijro nazorati boshqarmasiga", "Agentlikning Moliya departamentiga"]
VERBS = ["ishlab chiqsin", "tayyorlasin", "ta'minlasin", "o'rganib chiqsin", "kiritsin", "qayta ko'rib chiqsin", "joriy etsin",
         "amalga oshirsin", "taqdim etsin", "muvofiqlashtirsin", "xatlovdan o'tkazsin", "tahlil qilsin", "takomillashtirsin",
         "yangilasin", "sinovdan o'tkazsin"]


def deadline():
    y, d, m = R.choice([2026, 2027]), R.randint(1, 28), R.randrange(12)
    mon = MONTHS[m]
    kind = R.choices(["sana", "nisbiy", "boshlanish", "davriy", "doimiy", "yo'q"], [30, 22, 8, 18, 6, 16])[0]
    if kind == "sana":
        dd, mm = f"{d:02d}", f"{m + 1:02d}"
        text = R.choice([f"{y}-yil {d}-{mon}ga qadar", f"{y}-yil {d}-{mon}gacha", f"{dd}.{mm}.{y} yilgacha",
                         f"{dd}.{mm}.{y}-yilga qadar", f"{y}-yil {d}-{mon}dan kechiktirmasdan"])
    elif kind == "nisbiy":
        n, unit = R.choice(NUM), R.choice(["kun", "oy", "hafta", "ish kuni"])
        text = R.choice([f"{n} {unit} muddatda", f"{n} {unit} ichida", f"{n} {unit}lik muddatda"])
    elif kind == "boshlanish":
        text = R.choice([f"{y}-yil {d}-{mon}dan boshlab", f"{d:02d}.{m + 1:02d}.{y} yildan boshlab"])
    elif kind == "davriy":
        text = R.choice(["har oyda", "har chorakda", "har haftada", "har yarim yilda", "har yili",
                         f"har oyning {R.randint(1, 28)}-sanasiga qadar",
                         f"har chorak yakunidan keyingi oyning {R.randint(1, 20)}-sanasigacha",
                         f"har yarim yil yakunidan keyingi oyning {R.randint(1, 20)}-sanasiga qadar",
                         "har dushanba kuni", f"har yili {d}-{mon}ga qadar"])
    elif kind == "doimiy":
        text = R.choice(["doimiy ravishda", "muntazam ravishda", "doimiy asosda"])
    else:
        text = None
    return text, kind


def unit_name(v):
    return f"{R.choice(v['domains'])} {R.choice(UNITS)}"


def executor(v):
    r = R.random()
    if r < 0.6:
        return unit_name(v)
    if r < 0.75:
        return f"{R.choice(OWNERS)} {unit_name(v)}"
    return R.choice(v["single"])


def sentence(v):
    dl, kind = deadline()
    d = f" {dl}" if dl else ""
    p = R.random()
    if p < 0.38:
        ex = [executor(v)]
        s = f"{ex[0]} {R.choice(v['objects'])}{d} {R.choice(VERBS)}."
    elif p < 0.55:
        ex = [executor(v), unit_name(v)]
        s = f"{ex[0]} {ex[1]} bilan birgalikda {R.choice(v['objects'])}{d} {R.choice(VERBS)}."
    elif p < 0.68:
        ex = [executor(v)]
        s = f"{ex[0]} {R.choice(v['objects'])} tahlil qilib, natijalar bo'yicha takliflarni{d} {R.choice(TARGETS)} kiritsin."
    elif p < 0.8:
        ex = [executor(v)]
        if kind not in ("davriy", "doimiy"):
            dl, kind = R.choice(["har oyda", "har chorakda", f"har oyning {R.randint(1, 28)}-sanasiga qadar"]), "davriy"
            d = f" {dl}"
        s = f"{ex[0]} {R.choice(v['topics'])} to'g'risida{d} {R.choice(TARGETS)} ma'lumot berib borsin."
    elif p < 0.9:
        role = R.choice(v["roles"])
        ex = [role[0].upper() + role[1:]]
        s = f"{R.choice(v['subjects'])} {role} orqali {R.choice(TARGETS)}{d} taqdim etilsin."
    else:
        ex = [executor(v)]
        obj = R.choice(v["objects"])
        s = f"{obj[0].upper() + obj[1:]}{d} {ex[0]} tomonidan ta'minlansin."
    n = R.randint(1, 12)
    if R.random() < 0.5:
        s = f"{n}. {s}"
    return {"text": s, "ijrochi": ex, "muddat": dl, "muddat_turi": kind}


def write(name, rows):
    with open(OUT / name, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(name, len(rows))


train = [sentence(TRAIN) for _ in range(1600)]
test_synth = [sentence(TEST) for _ in range(150)]

# haqiqiy test: ish beruvchi hujjatlari, ijrochisi gap ichida bo'lgan topshiriqlar
APO = dict.fromkeys(map(ord, "‘’ʻʼ`´"), "'")
norm = lambda s: re.sub(r"\s+", " ", unicodedata.normalize("NFC", s or "").translate(APO)).strip().lower()
gold = json.load(open(Path(__file__).resolve().parents[2] / "task2-docs/eval/gold.json", encoding="utf-8"))
real = []
for doc in gold.values():
    for t in doc["tasks"]:
        if t["executors"] and all(norm(e) in norm(t["text"]) for e in t["executors"]):
            dl = (t.get("deadline") or {})
            inside = dl.get("text") and norm(dl["text"]) in norm(t["text"])
            real.append({"text": unicodedata.normalize("NFC", t["text"]).translate(APO), "ijrochi": t["executors"],
                         "muddat": dl["text"] if inside else None, "muddat_turi": dl.get("type") if inside else "yo'q"})
leak = {e for r in real for e in r["ijrochi"]} & {e for r in train for e in r["ijrochi"]}
assert not leak, leak
write("train.jsonl", train)
write("test_synth.jsonl", test_synth)
write("test_real.jsonl", real)
for r in train[:4]:
    print(" ", json.dumps(r, ensure_ascii=False))
