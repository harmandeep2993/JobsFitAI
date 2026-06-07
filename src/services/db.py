# src/services/db.py
"""
SQLite persistence for JobFitAI.

A single local database file (data/jobfitai.db, gitignored) holds scored
job matches and the current extracted resume, so both survive restarts.

Connections are short-lived (one per operation) for thread safety — NiceGUI
runs endpoint work in a threadpool.
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager

from src.utils.logger import get_logger

logger = get_logger(__name__)

DB_PATH = Path("data/jobfitai.db")


@contextmanager
def connect():
    """Yield a SQLite connection; commit on success, always close."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init() -> None:
    """Create tables if they don't exist."""
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS matches (
                id               TEXT PRIMARY KEY,
                source           TEXT,
                title            TEXT,
                company          TEXT,
                location         TEXT,
                url              TEXT,
                language         TEXT,
                posted_at        TEXT,
                score            REAL,
                label            TEXT,
                matched_required TEXT,
                missing_required TEXT,
                scored_at        TEXT,
                applied          INTEGER DEFAULT 0,
                jd_json          TEXT
            )
            """
        )
        # Migrate older DBs that predate the jd_json column.
        cols = [r[1] for r in conn.execute("PRAGMA table_info(matches)").fetchall()]
        if "jd_json" not in cols:
            conn.execute("ALTER TABLE matches ADD COLUMN jd_json TEXT")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS resume (
                id         INTEGER PRIMARY KEY CHECK (id = 1),
                name       TEXT,
                json       TEXT,
                created_at TEXT
            )
            """
        )
        # Every job id we've ever encountered (incl. rejected), so we never
        # re-fetch or re-classify the same posting — the main token saver.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS seen_jobs (
                id          TEXT PRIMARY KEY,
                source      TEXT,
                title       TEXT,
                first_seen  TEXT,
                decision    TEXT      -- scored | irrelevant | not_entry | stale
            )
            """
        )
        # Timeline of what the system did and when.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                type       TEXT,      -- fetched | scored | applied | run
                job_id     TEXT,
                detail     TEXT,
                created_at TEXT
            )
            """
        )
    logger.info("SQLite ready at %s", DB_PATH)


# Ensure the schema exists as soon as the module is imported.
init()
