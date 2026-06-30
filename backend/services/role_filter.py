# services/role_filter.py
"""
Cheap (no-LLM) pre-checks used by the Job Matches funnel:
  - is_target_role: does the title match one of the configured roles?
  - is_recent:      is the posting within the age limit?

Final relevance/entry-level decisions are made by the LLM relevance gate
(services/relevance.py), not by keyword rules.
"""

import re
import time

from services.fetchers import Job
from core.config import MAX_AGE_DAYS, TARGET_TITLES


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower())


def is_target_role(title: str, titles: list[str] | None = None) -> bool:
    """True if the job title contains one of the target role phrases."""
    t = _norm(title)
    for phrase in titles or TARGET_TITLES:
        if phrase.lower() in t:
            return True
    return False


def job_age_days(job: Job) -> float | None:
    """Age of the posting in days from its epoch posted_at, or None if unknown."""
    try:
        ts = int(job.posted_at)
    except (TypeError, ValueError):
        return None
    if ts <= 0:
        return None
    return (time.time() - ts) / 86400.0


def is_recent(job: Job, max_age_days: int | None = None) -> bool:
    """True if the posting is within the age limit (unknown dates are kept)."""
    limit = MAX_AGE_DAYS if max_age_days is None else max_age_days
    age = job_age_days(job)
    return age is None or age <= limit
