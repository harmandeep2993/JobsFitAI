# src/fetchers/bundesagentur_fetcher.py
"""
Bundesagentur fur Arbeit job fetcher.

Uses the public Jobborse API - no signup required; the key is publicly
documented by the BA themselves. Covers Germany only.

Flow (per official docs v2.1):
  1. Search via /pc/v6/jobs (page=1-indexed) -> get referenznummer per result
  2. For jobs hosted on BA itself: fetch full description via
     /pc/v4/jobdetails/{base64(referenznummer)}
  3. For jobs with externeURL: description comes from _enrich() scraping
     the external posting; the detail call returns an empty description.
"""

import base64
import time

import requests

from src.fetchers.job_fetcher import Job, _clean_html, _detect_language, _iso_to_epoch
from src.utils.logger import get_logger

logger = get_logger(__name__)

_BASE = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service"
_HEADERS = {"X-API-Key": "jobboerse-jobsuche", "User-Agent": "JobFitAI/1.0"}
_JOB_URL = "https://www.arbeitsagentur.de/jobsuche/jobdetail/{}"

# angebotsart=1 = permanent Arbeitsstelle (excludes internships, apprenticeships)
_ANGEBOTSART = 1


def _encode_refnr(refnr: str) -> str:
    """Base64-encode a referenznummer for the v4 jobdetails endpoint."""
    return base64.b64encode(refnr.encode()).decode()


def _fetch_detail(refnr: str) -> str:
    """
    Fetch the full job description from the BA detail endpoint.

    Returns plain text description, or empty string if unavailable
    (external jobs redirect to third-party sites and return no description).
    """
    encoded = _encode_refnr(refnr)
    try:
        resp = requests.get(
            f"{_BASE}/pc/v4/jobdetails/{encoded}",
            headers=_HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        raw = data.get("stellenangebotsBeschreibung") or ""
        return _clean_html(raw)
    except (requests.RequestException, ValueError) as e:
        logger.warning("BA detail fetch failed for %s: %s", refnr, e)
        return ""


def _parse_job(raw: dict, description: str) -> Job:
    """Convert a BA v6 list entry + fetched description into a normalized Job."""
    refnr = raw.get("referenznummer") or ""
    title = (raw.get("stellenangebotsTitel") or "").strip()
    company = (raw.get("firma") or "").strip()

    # Location: take first stellenlokationen entry
    locs = raw.get("stellenlokationen") or []
    location = ""
    if locs:
        adr = locs[0].get("adresse") or {}
        location = (adr.get("ort") or "").strip()

    posted_at = _iso_to_epoch(raw.get("datumErsteVeroeffentlichung") or "")
    # externeURL is already in the list response for externally-hosted jobs
    externe_url = (raw.get("externeURL") or "").strip()
    url = externe_url or _JOB_URL.format(refnr)

    return Job(
        title=title,
        company=company,
        location=location,
        url=url,
        description=description,
        language=_detect_language(description or title),
        id=f"ba-{refnr}",
        source="bundesagentur",
        posted_at=posted_at,
    )


def fetch_bundesagentur_jobs(
    query: str = "",
    location: str = "",
    limit: int = 10,
) -> list[Job]:
    """
    Fetch permanent job postings from the Bundesagentur fur Arbeit Jobborse API.

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
        "page": 1,
        "size": min(limit, 100),
    }

    try:
        resp = requests.get(
            f"{_BASE}/pc/v6/jobs",
            headers=_HEADERS,
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as e:
        logger.error("Bundesagentur list request failed: %s", e)
        return []

    raw_jobs = data.get("ergebnisliste") or []
    logger.info(
        "Bundesagentur returned %d of %d total",
        len(raw_jobs),
        data.get("maxErgebnisse", 0),
    )

    jobs: list[Job] = []
    for raw in raw_jobs[:limit]:
        refnr = raw.get("referenznummer") or ""
        if not refnr:
            logger.warning(
                "BA job missing referenznummer, skipping: %s",
                raw.get("stellenangebotsTitel"),
            )
            continue

        externe_url = (raw.get("externeURL") or "").strip()
        if externe_url:
            # External job - description lives on the third-party site.
            # Skip detail call (it returns empty); _enrich() will scrape it.
            description = ""
        else:
            description = _fetch_detail(refnr)
            time.sleep(0.2)  # gentle throttle between detail calls

        # Always keep the job even with no description - jd_unavailable fallback
        # allows manual paste, and _enrich() may still retrieve the text.
        job = _parse_job(raw, description)
        jobs.append(job)

    logger.info(
        "Bundesagentur: collected %d jobs (%d with descriptions)",
        len(jobs),
        sum(1 for j in jobs if j.description),
    )
    return jobs
