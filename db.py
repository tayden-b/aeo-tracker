"""
SQLite persistence layer.

Local and zero-setup so the whole pipeline runs with no external services. The
schema is deliberately plain SQL so it ports directly to Postgres/Supabase later
(swap the connection; the tables are the same shape).

Tables:
  runs      — one row per (provider, feature) sample: the raw answer + metadata
  routings  — products extracted from each run (the structured signal)
  citations — source URLs cited in each run (empty until a browsing provider)
  rollups   — daily aggregates per feature/product (what the dashboard reads)
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "aeo.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ts         TEXT NOT NULL,          -- full ISO timestamp
    run_date   TEXT NOT NULL,          -- YYYY-MM-DD (for daily rollups)
    provider   TEXT NOT NULL,
    model      TEXT,
    category   TEXT NOT NULL,
    feature    TEXT NOT NULL,
    prompt     TEXT NOT NULL,
    raw_answer TEXT
);
CREATE TABLE IF NOT EXISTS routings (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id    INTEGER NOT NULL REFERENCES runs(id),
    product   TEXT NOT NULL,
    role      TEXT,
    position  INTEGER,
    sentiment TEXT
);
CREATE TABLE IF NOT EXISTS citations (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id),
    url    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS rollups (
    run_date           TEXT NOT NULL,
    provider           TEXT NOT NULL,   -- a provider name, or 'blended'
    category           TEXT NOT NULL,
    feature            TEXT NOT NULL,
    product            TEXT NOT NULL,
    routing_share      REAL,
    mention_rate       REAL,
    avg_position       REAL,
    n_samples          INTEGER,
    sentiment_positive INTEGER,
    sentiment_neutral  INTEGER,
    sentiment_negative INTEGER,
    PRIMARY KEY (run_date, provider, category, feature, product)
);
"""


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


# --- writes ---

def insert_run(conn, *, ts, run_date, provider, model, category, feature, prompt, raw_answer) -> int:
    cur = conn.execute(
        "INSERT INTO runs (ts, run_date, provider, model, category, feature, prompt, raw_answer)"
        " VALUES (?,?,?,?,?,?,?,?)",
        (ts, run_date, provider, model, category, feature, prompt, raw_answer),
    )
    return cur.lastrowid


def insert_routing(conn, run_id, product, role, position, sentiment) -> None:
    conn.execute(
        "INSERT INTO routings (run_id, product, role, position, sentiment) VALUES (?,?,?,?,?)",
        (run_id, product, role, position, sentiment),
    )


def insert_citation(conn, run_id, url) -> None:
    conn.execute("INSERT INTO citations (run_id, url) VALUES (?,?)", (run_id, url))


def upsert_rollup(conn, row: dict) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO rollups (run_date, provider, category, feature, product,"
        " routing_share, mention_rate, avg_position, n_samples,"
        " sentiment_positive, sentiment_neutral, sentiment_negative)"
        " VALUES (:run_date,:provider,:category,:feature,:product,"
        ":routing_share,:mention_rate,:avg_position,:n_samples,"
        ":sentiment_positive,:sentiment_neutral,:sentiment_negative)",
        row,
    )


# --- reads ---

def fetch_runs(conn, run_date: str) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM runs WHERE run_date = ?", (run_date,)).fetchall()


def fetch_routings(conn, run_id: int) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM routings WHERE run_id = ?", (run_id,)).fetchall()


def fetch_rollups(conn, run_date: str | None = None) -> list[sqlite3.Row]:
    if run_date:
        return conn.execute("SELECT * FROM rollups WHERE run_date = ?", (run_date,)).fetchall()
    return conn.execute("SELECT * FROM rollups").fetchall()


def distinct_run_dates(conn) -> list[str]:
    rows = conn.execute("SELECT DISTINCT run_date FROM runs ORDER BY run_date").fetchall()
    return [r["run_date"] for r in rows]
