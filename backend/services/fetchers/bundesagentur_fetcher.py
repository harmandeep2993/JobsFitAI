# services/fetchers/bundesagentur_fetcher.py
"""
Bundesagentur fur Arbeit job fetcher.

Uses the public Jobborse API - no signup required; the key is publicly
documented by the BA themselves. Covers Germany only.

Flow (per official docs v2.1):
  1. Search via /pc/v6/jobs with veroeffentlichtseit to restrict to recent
     postings. Paginates until all results collected.
  2. Collect all raw list entries first (fast list requests only).
  3. For BA-hosted jobs (no externeURL): fetch descriptions in parallel
     via /pc/v4/jobdetails/{base64(referenznummer)}.
  4. For jobs with externeURL: _enrich() scrapes the third-party page.
"""

import base64
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from services.fetchers.job_fetcher import (
    Job,
    _clean_html,
    _detect_language,
    _iso_to_epoch,
)
from core.logger import get_logger

logger = get_logger(__name__)

_BASE = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service"
_HEADERS = {"X-API-Key": "jobboerse-jobsuche", "User-Agent": "JobsFitAI/1.0"}
_JOB_URL = "https://www.arbeitsagentur.de/jobsuche/jobdetail/{}"
_PAGE_SIZE = 100  # API maximum per page
_DETAIL_WORKERS = 8  # parallel detail calls

# angebotsart=1 = permanent Arbeitsstelle (excludes internships, apprenticeships)
_ANGEBOTSART = 1


def _encode_refnr(refnr: str) -> str:
    """Base64-encode a referenznummer for the v4 jobdetails endpoint."""
    return base64.b64encode(refnr.encode()).decode()


def _fetch_detail(refnr: str) -> str:
    """
    Fetch the full job description from the BA detail endpoint.

    Returns plain text description, or empty string if unavailable.
    """
    encoded = _encode_refnr(refnr)
    try:
        resp = requests.get(
            f"{_BASE}/pc/v4/jobdetails/{encoded}",
            headers=_HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        raw = resp.json().get("stellenangebotsBeschreibung") or ""
        return _clean_html(raw)
    except (requests.RequestException, ValueError) as e:
        logger.warning("BA detail fetch failed for %s: %s", refnr, e)
        return ""


def _fetch_details_parallel(refnrs: list[str]) -> dict[str, str]:
    """Fetch descriptions for multiple BA-hosted refnrs concurrently."""
    results: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=_DETAIL_WORKERS) as pool:
        futures = {pool.submit(_fetch_detail, r): r for r in refnrs}
        for fut in as_completed(futures):
            refnr = futures[fut]
            try:
                results[refnr] = fut.result()
            except Exception as e:
                logger.warning("BA detail worker failed for %s: %s", refnr, e)
                results[refnr] = ""
    return results


def _parse_job(raw: dict, description: str) -> Job:
    """Convert a BA v6 list entry + fetched description into a normalized Job."""
    refnr = raw.get("referenznummer") or ""
    title = (raw.get("stellenangebotsTitel") or "").strip()
    company = (raw.get("firma") or "").strip()

    locs = raw.get("stellenlokationen") or []
    location = ""
    if locs:
        adr = locs[0].get("adresse") or {}
        location = (adr.get("ort") or "").strip()

    posted_at = _iso_to_epoch(raw.get("datumErsteVeroeffentlichung") or "")
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
    max_age_days: int = 30,
    limit: int = 500,
) -> list[Job]:
    """
    Fetch permanent job postings from the Bundesagentur fur Arbeit Jobborse API.

    Paginates through all results published within max_age_days. BA-hosted
    descriptions are fetched in parallel; external jobs are left empty for
    _enrich() to scrape.

    Args:
        query (str):        Job title / keywords (was parameter).
        location (str):     City or region (wo parameter). Omitted if empty.
        max_age_days (int): Only return jobs published within this many days.
        limit (int):        Safety ceiling on total jobs returned per call.

    Returns:
        list[Job]: Normalized jobs. Empty list on failure.
    """
    base_params: dict = {
        "was": query,
        "angebotsart": _ANGEBOTSART,
        "size": _PAGE_SIZE,
        "veroeffentlichtseit": max_age_days,
    }
    if location:
        base_params["wo"] = location

    # Phase 1: collect all raw list entries via pagination (fast, no detail calls)
    raw_entries: list[dict] = []
    page = 1
    while len(raw_entries) < limit:
        params = {**base_params, "page": page}
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
            logger.error("Bundesagentur list request failed (page %d): %s", page, e)
            break

        raw_jobs = data.get("ergebnisliste") or []
        total = data.get("maxErgebnisse", 0)
        if page == 1:
            logger.info(
                "Bundesagentur '%s': %d total within %d days",
                query,
                total,
                max_age_days,
            )

        for raw in raw_jobs:
            if len(raw_entries) >= limit:
                break
            if raw.get("referenznummer"):
                raw_entries.append(raw)

        if len(raw_jobs) < _PAGE_SIZE or len(raw_entries) >= total:
            break
        page += 1

    # Phase 2: fetch descriptions in parallel for BA-hosted jobs only
    hosted_refnrs = [
        r["referenznummer"]
        for r in raw_entries
        if not (r.get("externeURL") or "").strip()
    ]
    if hosted_refnrs:
        logger.info(
            "Bundesagentur '%s': fetching %d BA-hosted descriptions in parallel",
            query,
            len(hosted_refnrs),
        )
        descriptions = _fetch_details_parallel(hosted_refnrs)
    else:
        descriptions = {}

    # Phase 3: build Job objects
    jobs: list[Job] = []
    for raw in raw_entries:
        refnr = raw["referenznummer"]
        externe_url = (raw.get("externeURL") or "").strip()
        description = "" if externe_url else descriptions.get(refnr, "")
        jobs.append(_parse_job(raw, description))

    logger.info(
        "Bundesagentur '%s': collected %d jobs (%d with descriptions)",
        query,
        len(jobs),
        sum(1 for j in jobs if j.description),
    )
    return jobs
