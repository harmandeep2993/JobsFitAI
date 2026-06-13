import uuid
from datetime import datetime, timezone

from src.services import db


def save(resume_id: str, jd_snippet: str, score: float, label: str) -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    snippet = (jd_snippet or "")[:120]
    with db.connect() as conn:
        existing = conn.execute(
            "SELECT id FROM analyses WHERE resume_id=? AND jd_snippet=?",
            (resume_id, snippet),
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE analyses SET score=?, label=?, scored_at=? WHERE id=?",
                (round(score), label, now, existing["id"]),
            )
        else:
            conn.execute(
                """INSERT INTO analyses (id, resume_id, jd_snippet, score, label, scored_at)
                   VALUES (?,?,?,?,?,?)""",
                (str(uuid.uuid4()), resume_id, snippet, round(score), label, now),
            )


def get_for_resume(resume_id: str, limit: int = 5) -> list[dict]:
    with db.connect() as conn:
        rows = conn.execute(
            """SELECT jd_snippet, score, label, scored_at
               FROM analyses WHERE resume_id=? ORDER BY scored_at DESC LIMIT ?""",
            (resume_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]
