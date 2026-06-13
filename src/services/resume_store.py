# src/services/resume_store.py
"""
Persistent resume storage (disk + SQLite).

Files live under resumes/<user_id>/<uuid>.<ext>.
user_id is always 'local' for now; add auth later without schema changes.

Slots: 0 = Base Resume, 1 = Tailored Resume 1, 2 = Tailored Resume 2.
Uploading to a slot replaces any existing resume in that slot.
"""

import uuid
import shutil
from pathlib import Path
from datetime import datetime, timezone

from src.services import db
from src.utils.logger import get_logger

logger = get_logger(__name__)

RESUME_DIR = Path("resumes")
MAX_SLOTS  = 3

SLOT_LABELS = {
    0: "Base Resume",
    1: "Tailored Resume 1",
    2: "Tailored Resume 2",
}


def _user_dir(user_id: str) -> Path:
    d = RESUME_DIR / user_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def save(user_id: str, slot: int, original_name: str, data: bytes,
         suffix: str, mime_type: str) -> dict:
    """Save a resume file to disk and record it in SQLite. Returns the record."""
    if slot not in range(MAX_SLOTS):
        raise ValueError(f"slot must be 0-{MAX_SLOTS - 1}")

    resume_id = str(uuid.uuid4())
    dest      = _user_dir(user_id) / f"{resume_id}{suffix}"
    dest.write_bytes(data)

    kb    = round(len(data) / 1024, 1)
    label = SLOT_LABELS[slot]
    now   = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with db.connect() as conn:
        # Remove old resume in this slot (and its file).
        old = conn.execute(
            "SELECT file_path FROM resumes WHERE user_id=? AND slot=?",
            (user_id, slot),
        ).fetchone()
        if old:
            _safe_delete(old["file_path"])
        conn.execute(
            "DELETE FROM resumes WHERE user_id=? AND slot=?",
            (user_id, slot),
        )
        conn.execute(
            """INSERT INTO resumes
               (id, user_id, slot, label, original_name, file_path, mime_type, file_size_kb, uploaded_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (resume_id, user_id, slot, label, original_name, str(dest), mime_type, kb, now),
        )

    record = {
        "id": resume_id, "slot": slot, "label": label,
        "name": original_name, "kb": kb, "uploaded_at": now,
    }
    logger.info("Saved resume slot=%d id=%s user=%s", slot, resume_id, user_id)
    return record


def list_all(user_id: str) -> list[dict]:
    """Return all stored resumes for a user, ordered by slot, with last analysis."""
    with db.connect() as conn:
        rows = conn.execute(
            """SELECT r.id, r.slot, r.label, r.original_name, r.file_path, r.mime_type,
                      r.file_size_kb, r.uploaded_at,
                      a.score      AS last_score,
                      a.label      AS last_label,
                      a.jd_snippet AS last_jd,
                      a.scored_at  AS last_analysed_at
               FROM resumes r
               LEFT JOIN (
                   SELECT resume_id, score, label, jd_snippet, scored_at
                   FROM analyses
                   WHERE (resume_id, scored_at) IN (
                       SELECT resume_id, MAX(scored_at) FROM analyses GROUP BY resume_id
                   )
               ) a ON a.resume_id = r.id
               WHERE r.user_id=? ORDER BY r.slot ASC""",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def get(user_id: str, resume_id: str) -> dict | None:
    """Fetch a single resume record."""
    with db.connect() as conn:
        row = conn.execute(
            "SELECT * FROM resumes WHERE id=? AND user_id=?",
            (resume_id, user_id),
        ).fetchone()
    return dict(row) if row else None


def delete(user_id: str, resume_id: str) -> bool:
    """Delete a resume from disk and SQLite. Returns True if found."""
    row = get(user_id, resume_id)
    if not row:
        return False
    _safe_delete(row["file_path"])
    with db.connect() as conn:
        conn.execute(
            "DELETE FROM resumes WHERE id=? AND user_id=?",
            (resume_id, user_id),
        )
    logger.info("Deleted resume id=%s user=%s", resume_id, user_id)
    return True


def set_label(user_id: str, resume_id: str, label: str) -> bool:
    """Rename the display label of a stored resume."""
    with db.connect() as conn:
        conn.execute(
            "UPDATE resumes SET label=? WHERE id=? AND user_id=?",
            (label, resume_id, user_id),
        )
    return True


def set_extracted(user_id: str, resume_id: str, extracted_json: str) -> None:
    """Cache the LLM-extracted resume JSON so recommendation scoring skips re-extraction."""
    with db.connect() as conn:
        conn.execute(
            "UPDATE resumes SET extracted_json=? WHERE id=? AND user_id=?",
            (extracted_json, resume_id, user_id),
        )


def list_scoreable(user_id: str) -> list[dict]:
    """Return only resumes that have a cached extracted_json — ready for scoring."""
    with db.connect() as conn:
        rows = conn.execute(
            """SELECT id, slot, label, original_name, extracted_json
               FROM resumes WHERE user_id=? AND extracted_json IS NOT NULL
               ORDER BY slot ASC""",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def _safe_delete(path_str: str) -> None:
    try:
        p = Path(path_str)
        if p.exists():
            p.unlink()
    except Exception as e:
        logger.warning("Could not delete resume file %s: %s", path_str, e)
