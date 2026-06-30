# core/database.py
"""
Database connection for JobsFitAI.

Uses Turso (cloud SQLite) when TURSO_DATABASE_URL + TURSO_AUTH_TOKEN are set,
falls back to local SQLite for development. Both paths expose the same
connect() context manager so no other file needs to know which backend is active.
"""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from core.logger import get_logger

logger = get_logger(__name__)

# === Connection mode ===

_TURSO_URL = (os.getenv("TURSO_DATABASE_URL") or os.getenv("TURSO_URL", "")).strip()
_TURSO_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "").strip()
_USE_TURSO = bool(_TURSO_URL and _TURSO_TOKEN)

DB_PATH = Path("data/jobsfitai.db")


# === Turso row/cursor/connection wrappers ===
# libsql_client has a different API from sqlite3. These thin wrappers make
# Turso connections look identical to sqlite3 connections so callers never
# need to know which backend they are talking to.


class _Row:
    """Dict-like row that supports both key and index access."""

    def __init__(self, data: dict):
        self._data = data

    def __getitem__(self, key):
        return self._data[key]

    def keys(self):
        """Return column names."""
        return self._data.keys()

    def get(self, key, default=None):
        """Return value for key, or default if missing."""
        return self._data.get(key, default)


class _Cursor:
    """Wraps a libsql_client ResultSet to match the sqlite3 cursor API."""

    def __init__(self, result_set):
        columns = list(result_set.columns)
        self._rows = [_Row(dict(zip(columns, r))) for r in result_set.rows]

    def fetchone(self):
        """Return first row or None."""
        return self._rows[0] if self._rows else None

    def fetchall(self):
        """Return all rows."""
        return self._rows

    def __iter__(self):
        return iter(self._rows)


class _TursoConn:
    """Wraps libsql_client ClientSync to match the sqlite3 connection API."""

    def __init__(self, client):
        self._client = client

    def execute(self, sql: str, params: tuple = ()) -> _Cursor:
        """Execute sql with params and return a cursor-like object."""
        rs = self._client.execute(sql, list(params))
        return _Cursor(rs)

    def commit(self):
        """No-op - libsql auto-commits each statement."""

    def close(self):
        """Close the underlying client."""
        self._client.close()


# === connect() context manager ===


@contextmanager
def connect():
    """Yield a database connection; commit on success, always close.

    Returns a Turso connection when TURSO_DATABASE_URL and TURSO_AUTH_TOKEN
    are set, otherwise a local SQLite connection. Both behave identically.
    """
    if _USE_TURSO:
        from libsql_client import create_client_sync

        client = create_client_sync(url=_TURSO_URL, auth_token=_TURSO_TOKEN)
        conn = _TursoConn(client)
        try:
            yield conn
        finally:
            conn.close()
    else:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()


# === Schema init ===


def init() -> None:
    """Create all tables if they don't exist. Safe to call multiple times."""
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
                jd_json          TEXT,
                section_scores   TEXT,
                summary          TEXT,
                status           TEXT DEFAULT 'scored',
                app_status       TEXT DEFAULT ''
            )
            """
        )
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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS seen_jobs (
                id         TEXT PRIMARY KEY,
                source     TEXT,
                title      TEXT,
                first_seen TEXT,
                decision   TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                type       TEXT,
                job_id     TEXT,
                detail     TEXT,
                created_at TEXT
            )
            """
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS resumes (
                id             TEXT PRIMARY KEY,
                user_id        TEXT NOT NULL DEFAULT 'local',
                slot           INTEGER NOT NULL DEFAULT 0,
                label          TEXT NOT NULL DEFAULT 'Base Resume',
                original_name  TEXT NOT NULL,
                file_path      TEXT NOT NULL,
                mime_type      TEXT NOT NULL,
                file_size_kb   REAL NOT NULL DEFAULT 0,
                uploaded_at    TEXT NOT NULL,
                extracted_json TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id         TEXT PRIMARY KEY,
                resume_id  TEXT NOT NULL,
                jd_snippet TEXT,
                score      REAL,
                label      TEXT,
                scored_at  TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_cache (
                hash        TEXT PRIMARY KEY,
                result_json TEXT NOT NULL,
                created_at  TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id              TEXT PRIMARY KEY,
                email           TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at      TEXT NOT NULL
            )
            """
        )

    mode = f"Turso ({_TURSO_URL})" if _USE_TURSO else f"SQLite ({DB_PATH})"
    logger.info("Database ready - %s", mode)


init()
