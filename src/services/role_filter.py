# src/services/role_filter.py
"""
Heuristic filtering for the Job Matches dashboard.

Two concerns, both cheap (no LLM) so they run BEFORE scoring:
  1. Is the posting one of the target roles? (title match)
  2. Is it entry-level? (seniority keywords + required-years guard)

Rules come from config.yaml (job_search.*), so they can be tuned without
code changes.
"""

import re
import time

from src.fetchers import Job
from src.utils.config import (
    TARGET_TITLES,
    EXCLUDE_KEYWORDS,
    ENTRY_KEYWORDS,
    MAX_EXPERIENCE_YEARS,
    MAX_AGE_DAYS,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

_YEARS_RE = re.compile(r"(\d{1,2})\s*\+?\s*(?:-\s*\d{1,2}\s*)?(?:years|yrs|year|jahre|jahr)")


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower())


def is_target_role(title: str, titles: list[str] | None = None) -> bool:
    """True if the job title contains one of the target role phrases."""
    t = _norm(title)
    for phrase in (titles or TARGET_TITLES):
        if phrase.lower() in t:
            return True
    return False


def min_years_required(text: str) -> int | None:
    """
    Smallest "N years" figure mentioned (the entry bar), or None if none.

    Lenient by design: if any low number is present (e.g. "0-2 years")
    the role is not excluded on experience grounds.
    """
    nums = [int(n) for n in _YEARS_RE.findall(_norm(text))]
    return min(nums) if nums else None


def is_entry_level(job: Job) -> bool:
    """
    Lenient entry-level test.

    - Explicit entry marker (junior/graduate/working student/…) -> keep.
    - Seniority marker in the TITLE -> reject.
    - Requires more than MAX_EXPERIENCE_YEARS -> reject.
    - Otherwise (unmarked, e.g. plain "Data Scientist") -> keep.
    """
    title = _norm(job.title)
    full  = _norm(job.title + " " + job.description)

    if any(k in full for k in ENTRY_KEYWORDS):
        return True

    if any(k in title for k in EXCLUDE_KEYWORDS):
        return False

    years = min_years_required(full)
    if years is not None and years > MAX_EXPERIENCE_YEARS:
        return False

    return True


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


def filter_jobs(jobs: list[Job], entry_only: bool = True,
                titles: list[str] | None = None) -> list[Job]:
    """
    Keep target-role, recent jobs; if entry_only, also require entry-level.

    Drops stale postings (older than MAX_AGE_DAYS) which are likely filled.
    """
    kept = []
    dropped_old = 0
    for job in jobs:
        if not is_target_role(job.title, titles):
            continue
        if not is_recent(job):
            dropped_old += 1
            continue
        if entry_only and not is_entry_level(job):
            continue
        kept.append(job)

    logger.info(
        "Role filter: kept %d / %d jobs (entry_only=%s, dropped %d stale > %dd)",
        len(kept), len(jobs), entry_only, dropped_old, MAX_AGE_DAYS
    )
    return kept
