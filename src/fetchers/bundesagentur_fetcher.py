# src/fetchers/bundesagentur_fetcher.py
"""
Bundesagentur für Arbeit job fetcher.

Uses the public Jobbörse API - no signup required; the key is publicly
documented by the BA themselves. Covers Germany only.

Two-step per job: the list endpoint returns metadata, the detail endpoint
returns the full description (required for meaningful match scoring).
"""

import time

import requests

from src.fetchers.job_fetcher import Job, _clean_html, _detect_language, _iso_to_epoch
from src.utils.logger import get_logger

logger = get_logger(__name__)

_BASE = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4"
_HEADERS = {"X-API-Key": "jobboerse-jobsuche", "User-Agent": "JobFitAI/1.0"}
_JOB_URL = "https://www.arbeitsagentur.de/jobsuche/jobdetail/{}"

# angebotsart=1 = permanent Arbeitsstelle (excludes internships, apprenticeships)
_ANGEBOTSART = 1


def _fetch_detail(hash_id: str) -> tuple[str, str]:
    """
    Fetch description and external URL from the BA detail endpoint.

    Returns (description, externe_url). Either may be empty if the API
    does not provide it - callers should fall back to scraping externe_url.
    """
    try:
        resp = requests.get(
            f"{_BASE}/jobdetails/{hash_id}",
            headers=_HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        raw = (
            data.get("stellenbeschreibung")
            or data.get("beschreibung")
            or data.get("angebotsbeschreibung")
            or ""
        )
        externe_url = data.get("externeUrl") or data.get("externerLink") or ""
        return _clean_html(raw), externe_url.strip()
    except (requests.RequestException, ValueError) as e:
        logger.warning("BA detail fetch failed for %s: %s", hash_id, e)
        return "", ""


def _parse_job(raw: dict, description: str, externe_url: str = "") -> Job:
    """Convert a BA list entry + fetched description into a normalized Job."""
    hash_id = raw.get("hashId", "")
    title = (raw.get("titel") or "").strip()
    company = (raw.get("arbeitgeber") or "").strip()
    ort = raw.get("arbeitsort") or {}
    location = (ort.get("ort") or "").strip()
    posted_at = _iso_to_epoch(raw.get("aktuelleVeroeffentlichungsdatum") or "")
    # Prefer the external URL so _enrich() can scrape the real JD page when
    # the BA detail endpoint returned an empty description.
    url = externe_url or _JOB_URL.format(hash_id)

    return Job(
        title=title,
        company=company,
        location=location,
        url=url,
        description=description,
        language=_detect_language(description or title),
        id=f"ba-{hash_id}",
        source="bundesagentur",
        posted_at=posted_at,
    )


def fetch_bundesagentur_jobs(
    query: str = "",
    location: str = "",
    limit: int = 10,
) -> list[Job]:
    """
    Fetch permanent job postings from the Bundesagentur für Arbeit Jobbörse API.

    Args:
        query (str):   Job title / keywords (was parameter).
        location (str): City or region (wo parameter).
        limit (int):   Max number of jobs to return.

    Returns:
        list[Job]: Normalized jobs with full descriptions. Empty list on failure.
    """
    params = {
        "was": query,
        "wo": location,
        "angebotsart": _ANGEBOTSART,
        "page": 0,
        "size": min(limit, 100),
    }

    try:
        resp = requests.get(
            f"{_BASE}/jobs",
            headers=_HEADERS,
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as e:
        logger.error("Bundesagentur list request failed: %s", e)
        return []

    raw_jobs = data.get("stellenangebote") or []
    logger.info(
        "Bundesagentur returned %d of %d total",
        len(raw_jobs),
        data.get("maxErgebnisse", 0),
    )

    jobs: list[Job] = []
    for raw in raw_jobs[:limit]:
        hash_id = raw.get("hashId", "")
        if not hash_id:
            continue

        description, externe_url = _fetch_detail(hash_id)
        time.sleep(0.2)  # gentle throttle between detail calls

        # Always keep the job - even with an empty description. If the real JD
        # lives on an external site (StepStone etc.) the pipeline's _enrich()
        # will scrape it; if that also fails the job becomes jd_unavailable and
        # the user can paste the JD text manually.
        job = _parse_job(raw, description, externe_url)
        jobs.append(job)

    logger.info(
        "Bundesagentur: collected %d jobs (%d with descriptions)",
        len(jobs),
        sum(1 for j in jobs if j.description),
    )
    return jobs
