import uuid
from datetime import datetime, timezone

from src.services import db


def save(resume_id: str, jd_snippet: str, score: float, label: str) -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with db.connect() as conn:
        conn.execute(
            """INSERT INTO analyses (id, resume_id, jd_snippet, score, label, scored_at)
               VALUES (?,?,?,?,?,?)""",
            (str(uuid.uuid4()), resume_id, (jd_snippet or "")[:120], round(score), label, now),
        )


def get_for_resume(resume_id: str, limit: int = 5) -> list[dict]:
    with db.connect() as conn:
        rows = conn.execute(
            """SELECT jd_snippet, score, label, scored_at
               FROM analyses WHERE resume_id=? ORDER BY scored_at DESC LIMIT ?""",
            (resume_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]
