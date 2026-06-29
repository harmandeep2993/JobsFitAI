# src/fetchers/arbeitnow_fetcher.py
"""
Arbeitnow job fetcher.

Arbeitnow (https://www.arbeitnow.com) exposes a free, key-less job-board
API focused on Germany/EU that returns the FULL job description - unlike
Adzuna's ~500-char snippet. That makes the resume↔JD match scores far
more trustworthy.

The API's `search` parameter does not filter server-side, so we page
through the feed and filter client-side by query terms and location.
Each job's `slug` is a stable id used for deduplication.
"""

import requests

from src.fetchers.job_fetcher import Job, _clean_html, _detect_language
from src.utils.logger import get_logger

logger = get_logger(__name__)

API_URL = "https://www.arbeitnow.com/api/job-board-api"


def _matches(raw: dict, query_terms: list[str], location: str) -> bool:
    """Client-side filter: keep a job if it matches the query and location."""
    if location:
        loc = (raw.get("location") or "").lower()
        if location.lower() not in loc and not raw.get("remote"):
            return False

    if query_terms:
        haystack = " ".join(
            [
                raw.get("title", ""),
                " ".join(raw.get("tags", []) or []),
                " ".join(raw.get("job_types", []) or []),
                raw.get("description", "")[:600],
            ]
        ).lower()
        if not any(term in haystack for term in query_terms):
            return False

    return True


def _parse_job(raw: dict) -> Job:
    """Convert a raw Arbeitnow entry into a normalized Job with full text."""
    description = _clean_html(raw.get("description", ""))
    title = (raw.get("title") or "").strip()

    return Job(
        title=title,
        company=(raw.get("company_name") or "").strip(),
        location=(raw.get("location") or "").strip(),
        url=raw.get("url", ""),
        description=description,
        language=_detect_language(description or title),
        id=raw.get("slug", "") or raw.get("url", ""),
        source="arbeitnow",
        posted_at=str(raw.get("created_at", "") or ""),
    )


def fetch_arbeitnow_jobs(
    query: str = "",
    location: str = "",
    limit: int = 15,
    max_pages: int = 3,
) -> list[Job]:
    """
    Fetch job postings (with full descriptions) from Arbeitnow.

    Args:
        query (str):     Space-separated terms; a job matches if any term
                         appears in its title/tags/description. Empty = no filter.
        location (str):  Location substring filter (remote jobs always pass).
        limit (int):     Max number of jobs to return.
        max_pages (int): Max feed pages to scan (100 jobs/page).

    Returns:
        list[Job]: Normalized jobs with full, HTML-stripped descriptions.
                   Empty list on request failure.
    """
    query_terms = [t for t in query.lower().split() if t]
    collected: list[Job] = []

    for page in range(1, max_pages + 1):
        try:
            response = requests.get(API_URL, params={"page": page}, timeout=20)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error("Arbeitnow request failed (page %d): %s", page, e)
            break

        try:
            raw_jobs = response.json().get("data", [])
        except ValueError as e:
            logger.error("Arbeitnow JSON parse failed (page %d): %s", page, e)
            break
        if not raw_jobs:
            break

        for raw in raw_jobs:
            if _matches(raw, query_terms, location):
                collected.append(_parse_job(raw))
                if len(collected) >= limit:
                    logger.info("Arbeitnow: collected %d jobs", len(collected))
                    return collected

    logger.info("Arbeitnow: collected %d jobs", len(collected))
    return collected
