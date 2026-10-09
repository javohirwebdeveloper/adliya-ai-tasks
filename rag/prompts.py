"""Gemma uchun so'rovlar: RAG bilan, RAG'siz (solishtirish uchun) va hakam."""
import json
import re

RULES = ("Savolda [ISM_1], [TELEFON_1] kabi belgilar bo'lishi mumkin: bu yashirilgan shaxsiy ma'lumot, ularni "
         "o'zgartirmasdan ishlat, o'zingdan ism yoki raqam to'qima.\n"
         "Javobni fuqaro yozgan tilda va yozuvda yoz: ruscha savolga rus tilida, o'zbek kirillida yozilganga kirillda, "
         "lotinda yozilganga lotinda. 2-5 gap.\n")
ROLE = "Sen Adliya vazirligining fuqarolar savollariga javob beruvchi yordamchisisan.\n"


def rag_prompt(question: str, items: list[dict]) -> str:
    src = "\n\n".join(f"[{i}] Savol: {it['question']}\nJavob: {it['answer']}" for i, it in enumerate(items, 1))
    return (ROLE +
            "Faqat quyidagi manbalardagi ma'lumotdan foydalan. Manbada yo'q summa, muddat, idora nomi yoki hujjatni "
            "o'zingdan qo'shma. Agar manbalarda fuqaro savoliga javob bo'lmasa, javob_bor: false qil.\n" + RULES +
            'Faqat JSON qaytar: {"javob_bor": true yoki false, "manbalar": [foydalangan manbalar raqami], "javob": "..."}'
            f"\n\nManbalar:\n{src}\n\nFuqaro savoli:\n{question}")


def closed_prompt(question: str) -> str:
    return (ROLE + "Agar javobni aniq bilmasang, javob_bor: false qil.\n" + RULES +
            'Faqat JSON qaytar: {"javob_bor": true yoki false, "javob": "..."}\n\nFuqaro savoli:\n' + question)


def rewrite_prompt(message: str) -> str:
    """Qidiruv uchun savolni qayta yozish: fuqaro xabaridan faqat savol mazmuni (salom, ism, telefon kabi gaplarsiz)."""
    return ("Quyidagi fuqaro xabaridan ma'lumotlar bazasida qidirish uchun bitta qisqa savol yoz. Faqat savolning "
            "mazmuni bo'lsin: salom, ism, telefon, pasport va [ISM_1] kabi belgilar bo'lmasin. Savolni fuqaro yozgan "
            "tilda yoz. Faqat savolning o'zini qaytar.\n\nXabar:\n" + message)


def judge_prompt(question: str, reference: str, answer: str) -> str:
    return ("Quyida fuqaro savoli, rasmiy ma'lumotnomadagi javob va tekshiriladigan javob bor. Tekshiriladigan javobni "
            "ma'lumotnoma bilan solishtir:\n"
            "to'g'ri: savolga javob beradi va ma'lumotnomaga zid hech narsa yo'q;\n"
            "qisman: muhim qismi yetishmaydi yoki ma'lumotnomada yo'q da'vo (summa, muddat, idora) qo'shilgan;\n"
            "noto'g'ri: ma'lumotnomaga zid yoki savolga javob bermaydi.\n"
            'Faqat JSON qaytar: {"baho": "to\'g\'ri" yoki "qisman" yoki "noto\'g\'ri", "sabab": "bir gap"}\n\n'
            f"Savol: {question}\n\nMa'lumotnoma: {reference}\n\nTekshiriladigan javob: {answer}")


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
