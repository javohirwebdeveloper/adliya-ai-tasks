"""PostgreSQL: savol-javoblarning asl manbasi va so'rovlar jurnali."""
import hashlib

import psycopg
from psycopg.rows import dict_row

from .config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS answers (
    id          INTEGER PRIMARY KEY,
    category_id INTEGER,
    topic_id    INTEGER,
    answer      TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'active',
    created_at  TIMESTAMP,
    updated_at  TIMESTAMP
);
CREATE TABLE IF NOT EXISTS questions (
    id          INTEGER PRIMARY KEY,
    answer_id   INTEGER NOT NULL REFERENCES answers(id) ON DELETE CASCADE,
    question    TEXT NOT NULL,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP,
    updated_at  TIMESTAMP
);
CREATE INDEX IF NOT EXISTS questions_answer_id ON questions(answer_id);
CREATE TABLE IF NOT EXISTS query_log (
    id          BIGSERIAL PRIMARY KEY,
    ts          TIMESTAMPTZ NOT NULL DEFAULT now(),
    channel     TEXT,
    user_hash   TEXT,
    query       TEXT NOT NULL,
    status      TEXT NOT NULL,
    answer_id   INTEGER,
    score       REAL,
    latency_ms  INTEGER
);
ALTER TABLE query_log ADD COLUMN IF NOT EXISTS feedback SMALLINT;      -- 1 foydali, -1 foydasiz
ALTER TABLE query_log ADD COLUMN IF NOT EXISTS voice BOOLEAN NOT NULL DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS query_log_ts ON query_log(ts);
"""


def connect(url: str | None = None) -> psycopg.Connection:
    return psycopg.connect(url or settings.database_url, autocommit=True, row_factory=dict_row)


def init_schema(conn: psycopg.Connection) -> None:
    conn.execute(SCHEMA)


def upsert_answers(conn, rows: list[dict]) -> None:
    with conn.cursor() as cur:
        cur.executemany(
            """INSERT INTO answers (id, category_id, topic_id, answer, status, created_at, updated_at)
               VALUES (%(id)s, %(category_id)s, %(topic_id)s, %(answer)s, %(status)s, %(created_at)s, %(updated_at)s)
               ON CONFLICT (id) DO UPDATE SET category_id = EXCLUDED.category_id, topic_id = EXCLUDED.topic_id,
                 answer = EXCLUDED.answer, status = EXCLUDED.status, updated_at = EXCLUDED.updated_at""",
            rows,
        )


def upsert_questions(conn, rows: list[dict]) -> None:
    with conn.cursor() as cur:
        cur.executemany(
            """INSERT INTO questions (id, answer_id, question, is_active, created_at, updated_at)
               VALUES (%(id)s, %(answer_id)s, %(question)s, %(is_active)s, %(created_at)s, %(updated_at)s)
               ON CONFLICT (id) DO UPDATE SET answer_id = EXCLUDED.answer_id, question = EXCLUDED.question,
                 is_active = EXCLUDED.is_active, updated_at = EXCLUDED.updated_at""",
            rows,
        )


def index_items(conn) -> list[dict]:
    """Indeksga kiradigan matnlar: faol savollar va faol javoblarning o'zi."""
    return conn.execute(
        """SELECT 'question' AS kind, q.id AS item_id, q.answer_id, q.question AS text, a.category_id, a.topic_id
             FROM questions q JOIN answers a ON a.id = q.answer_id
            WHERE q.is_active AND a.status = 'active'
           UNION ALL
           SELECT 'answer', a.id, a.id, a.answer, a.category_id, a.topic_id
             FROM answers a WHERE a.status = 'active'
           ORDER BY kind DESC, item_id"""
    ).fetchall()


def get_answers(conn, ids: list[int]) -> dict[int, dict]:
    if not ids:
        return {}
    rows = conn.execute(
        "SELECT id, category_id, topic_id, answer FROM answers WHERE id = ANY(%s) AND status = 'active'", (ids,)
    ).fetchall()
    return {r["id"]: r for r in rows}


def counts(conn) -> dict:
    return conn.execute(
        """SELECT (SELECT count(*) FROM answers WHERE status = 'active') AS answers,
                  (SELECT count(*) FROM questions WHERE is_active) AS questions,
                  (SELECT count(*) FROM query_log) AS queries"""
    ).fetchone()


def log_query(conn, *, channel: str, user_id: str | None, query: str, status: str,
              answer_id: int | None, score: float | None, latency_ms: int, voice: bool = False) -> int:
    # foydalanuvchi ID si ochiq saqlanmaydi, faqat xeshi (shaxsga doir ma'lumot)
    user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:16] if user_id else None
    return conn.execute(
        """INSERT INTO query_log (channel, user_hash, query, status, answer_id, score, latency_ms, voice)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
        (channel, user_hash, query[:1000], status, answer_id, score, latency_ms, voice),
    ).fetchone()["id"]


def set_feedback(conn, log_id: int, value: int) -> dict | None:
    return conn.execute("UPDATE query_log SET feedback = %s WHERE id = %s RETURNING query, answer_id",
                        (value, log_id)).fetchone()


def category_counts(conn) -> dict[int, int]:
    rows = conn.execute("SELECT category_id, count(*) AS n FROM answers WHERE status = 'active' GROUP BY 1").fetchall()
    return {r["category_id"]: r["n"] for r in rows}


def category_questions(conn, category_id: int, limit: int, offset: int) -> list[dict]:
    """Kategoriyadagi har bir javob uchun bitta (birinchi) savol."""
    return conn.execute(
        """SELECT a.id AS answer_id,
                  (SELECT q.question FROM questions q WHERE q.answer_id = a.id AND q.is_active ORDER BY q.id LIMIT 1) AS question
             FROM answers a WHERE a.category_id = %s AND a.status = 'active' ORDER BY a.id LIMIT %s OFFSET %s""",
        (category_id, limit, offset),
    ).fetchall()


def first_questions(conn, ids: list[int]) -> dict[int, str]:
    if not ids:
        return {}
    rows = conn.execute(
        """SELECT DISTINCT ON (answer_id) answer_id, question FROM questions
            WHERE answer_id = ANY(%s) AND is_active ORDER BY answer_id, id""", (ids,)).fetchall()
    return {r["answer_id"]: r["question"] for r in rows}


def stats(conn, days: int = 7) -> dict:
    s = conn.execute(
        """SELECT count(*) AS total,
                  count(*) FILTER (WHERE status = 'answered') AS answered,
                  count(*) FILTER (WHERE status = 'unsure') AS unsure,
                  count(*) FILTER (WHERE status = 'not_found') AS not_found,
                  count(*) FILTER (WHERE feedback = 1) AS likes,
                  count(*) FILTER (WHERE feedback = -1) AS dislikes,
                  count(*) FILTER (WHERE voice) AS voice,
                  count(DISTINCT user_hash) AS users,
                  coalesce(round(percentile_cont(0.5) WITHIN GROUP (ORDER BY latency_ms))::int, 0) AS median_ms
             FROM query_log WHERE ts > now() - make_interval(days => %s) AND channel NOT IN ('eval', 'test', 'loadtest')""", (days,)).fetchone()
    gaps = conn.execute(
        """SELECT lower(query) AS query, count(*) AS n, max(ts) AS last
             FROM query_log WHERE ts > now() - make_interval(days => %s) AND channel NOT IN ('eval', 'test', 'loadtest')
              AND (status = 'not_found' OR feedback = -1)
            GROUP BY lower(query) ORDER BY n DESC, last DESC LIMIT 30""", (days,)).fetchall()
    recent = conn.execute(
        """SELECT id, ts, channel, query, status, answer_id, score, feedback, latency_ms, voice
             FROM query_log WHERE channel NOT IN ('eval', 'test', 'loadtest') ORDER BY id DESC LIMIT 50""").fetchall()
    top = conn.execute(
        """SELECT answer_id, count(*) AS n FROM query_log
            WHERE ts > now() - make_interval(days => %s) AND status = 'answered' AND channel NOT IN ('eval', 'test', 'loadtest')
            GROUP BY answer_id ORDER BY n DESC LIMIT 10""", (days,)).fetchall()
    return {"summary": s, "gaps": gaps, "recent": recent, "top": top}
