"""Savolga shaxsiy ma'lumot qo'shish: fuqaro haqiqatda savolini ismi, pasporti, telefoni bilan yozadi.
Barcha qiymatlar to'qima, haqiqiy odamga tegishli emas."""
import random

NAMES = {
    "o'zbek lotin": ["Karimov Akmal Rustam o'g'li", "Yusupova Malika Anvar qizi", "Toshpo'latov Bahodir Erkin o'g'li",
                     "Rahimova Nigora", "Ergashev Ulug'bek", "Nazarova Feruza Akbar qizi", "Abdullayev Sherzod"],
    "o'zbek kirill": ["Каримов Акмал Рустам ўғли", "Юсупова Малика Анвар қизи", "Тошпўлатов Баҳодир Эркин ўғли",
                      "Раҳимова Нигора Шавкат қизи", "Абдуллаев Шерзод Бахтиёр ўғли"],
    "rus tili": ["Петрова Анна Сергеевна", "Каримов Алишер Олимович", "Ким Виктор Николаевич",
                 "Юсупова Малика Анваровна", "Ахмедов Санжар Рустамович"],
}
TEMPLATES = {
    "o'zbek lotin": ["Assalomu alaykum, men {ism}. {q} Telefonim {tel}.",
                     "{q} Men {ism}, pasportim {pas}.",
                     "Hurmatli mutaxassis! {q} Ma'lumot uchun: {ism}, JSHSHIR {jsh}, tel {tel}."],
    "o'zbek kirill": ["Ассалому алайкум, мен {ism}. {q} Телефоним {tel}.",
                      "{q} Мен {ism}, паспортим {pas}."],
    "rus tili": ["Здравствуйте, меня зовут {ism}. {q} Мой телефон {tel}.",
                 "{q} Я {ism}, паспорт {pas}, ПИНФЛ {jsh}."],
}


def add_pii(question: str, script: str, r: random.Random) -> str:
    tel = f"+998 {r.choice(['90', '91', '93', '94', '97', '99'])} {r.randint(100, 999)} {r.randint(10, 99)} {r.randint(10, 99)}"
    pas = r.choice(["AA", "AB", "AC", "AD"]) + f"{r.randint(0, 9999999):07d}"
    jsh = f"{r.choice('34')}{r.randint(1, 28):02d}{r.randint(1, 12):02d}{r.randint(60, 99):02d}{r.randint(0, 9999999):07d}"
    return r.choice(TEMPLATES[script]).format(q=question.strip(), ism=r.choice(NAMES[script]), tel=tel, pas=pas, jsh=jsh)
