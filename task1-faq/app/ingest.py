"""Savol-javoblarni fayldan PostgreSQL ga yuklaydi va Qdrant indeksini qayta quradi.

  python -m app.ingest --answers data/answers.csv --questions data/questions.csv
  python -m app.ingest --excel data/faq.xlsx          # "answers" va "questions" varaqlari
  python -m app.ingest --excel data/faq.xlsx --flat   # bitta varaq: savol | javob ustunlari

Ustun nomlari o'zbekcha, inglizcha yoki ruscha bo'lishi mumkin (savol/question/вопрос ...).
"""
import argparse
import sys

import pandas as pd
from qdrant_client import QdrantClient

from . import db
from .config import settings
from .index import build
from .normalize import normalize

ALIASES = {
    "question": ["question", "savol", "вопрос"],
    "answer": ["answer", "javob", "ответ"],
    "answer_id": ["answer_id", "javob_id"],
    "id": ["id"],
    "category_id": ["category_id", "kategoriya_id"],
    "topic_id": ["topic_id", "mavzu_id"],
    "status": ["status", "holat"],
    "is_active": ["is_active", "faol"],
    "created_at": ["created_at"],
    "updated_at": ["updated_at"],
}


def read_table(path: str, sheet: str | int | None = None) -> pd.DataFrame:
    if path.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(path, sheet_name=sheet if sheet is not None else 0, dtype=str)
    else:
        df = pd.read_csv(path, dtype=str, encoding="utf-8-sig")
    df = df.fillna("")
    rename = {}
    for col in df.columns:
        key = str(col).strip().lower()
        for canon, names in ALIASES.items():
            if key in names:
                rename[col] = canon
    return df.rename(columns=rename)


def _int(v):
    v = str(v).strip()
    return int(float(v)) if v else None


def _ts(v):
    v = str(v).strip()
    return v or None


def _active(v) -> bool:
    return str(v).strip().lower() in ("", "true", "1", "yes", "ha", "t", "active")


def from_tables(adf: pd.DataFrame, qdf: pd.DataFrame):
    answers = [
        {"id": _int(r["id"]), "category_id": _int(r.get("category_id", "")), "topic_id": _int(r.get("topic_id", "")),
         "answer": normalize(r["answer"]), "status": (str(r.get("status", "")).strip() or "active"),
         "created_at": _ts(r.get("created_at", "")), "updated_at": _ts(r.get("updated_at", ""))}
        for r in adf.to_dict("records")
    ]
    questions = [
        {"id": _int(r["id"]), "answer_id": _int(r["answer_id"]), "question": normalize(r["question"]),
         "is_active": _active(r.get("is_active", "")),
         "created_at": _ts(r.get("created_at", "")), "updated_at": _ts(r.get("updated_at", ""))}
        for r in qdf.to_dict("records")
    ]
    return answers, questions


def from_flat(df: pd.DataFrame):
    """Bitta jadval: har qatorda savol va javob. Bir xil javob matni bitta javob bo'ladi."""
    answers, questions, ids = [], [], {}
    for n, r in enumerate(df.to_dict("records"), start=1):
        a, q = normalize(r["answer"]), normalize(r["question"])
        if a not in ids:
            ids[a] = len(ids) + 1
            answers.append({"id": ids[a], "category_id": None, "topic_id": None, "answer": a, "status": "active",
                            "created_at": None, "updated_at": None})
        questions.append({"id": n, "answer_id": ids[a], "question": q, "is_active": True,
                          "created_at": None, "updated_at": None})
    return answers, questions


def validate(answers: list[dict], questions: list[dict]):
    problems = []
    answers = [a for a in answers if a["id"] is not None and a["answer"]]
    ids = {a["id"] for a in answers}
    if len(ids) != len(answers):
        problems.append("takrorlangan javob id lari bor")
    good = []
    for q in questions:
        if not q["question"]:
            problems.append(f"savol {q['id']}: matn bo'sh, o'tkazib yuborildi")
        elif q["answer_id"] not in ids:
            problems.append(f"savol {q['id']}: answer_id={q['answer_id']} topilmadi, o'tkazib yuborildi")
        else:
            good.append(q)
    seen = {}
    for q in good:
        key = q["question"].lower()
        if key in seen and seen[key] != q["answer_id"]:
            problems.append(f"bir xil savol ikki xil javobga bog'langan: {q['question']!r}")
        seen[key] = q["answer_id"]
    return answers, good, problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--answers")
    ap.add_argument("--questions")
    ap.add_argument("--excel")
    ap.add_argument("--flat", action="store_true")
    ap.add_argument("--replace", action="store_true", help="avval jadvallarni tozalash (to'liq almashtirish)")
    ap.add_argument("--no-index", action="store_true", help="faqat bazaga yozish, indeksni qurmaslik")
    args = ap.parse_args(argv)

    if args.excel and args.flat:
        answers, questions = from_flat(read_table(args.excel))
    elif args.excel:
        answers, questions = from_tables(read_table(args.excel, "answers"), read_table(args.excel, "questions"))
    elif args.answers and args.questions:
        answers, questions = from_tables(read_table(args.answers), read_table(args.questions))
    else:
        ap.error("--answers va --questions yoki --excel kerak")

    answers, questions, problems = validate(answers, questions)
    for p in problems[:50]:
        print("OGOHLANTIRISH:", p, file=sys.stderr)
    print(f"javoblar: {len(answers)}, savollar: {len(questions)}")

    conn = db.connect()
    db.init_schema(conn)
    if args.replace:
        conn.execute("TRUNCATE questions, answers")
    db.upsert_answers(conn, answers)
    db.upsert_questions(conn, questions)
    print("PostgreSQL ga yozildi:", db.counts(conn))

    if not args.no_index:
        from .embedder import Embedder
        build(QdrantClient(url=settings.qdrant_url), Embedder(), db.index_items(conn))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
