# src/fetchers/job_fetcher.py
"""
Adzuna job fetcher.

Fetches job postings from the Adzuna search API and normalizes each
result into a :class:`Job` dataclass. Returns a list of jobs so callers
(the extraction/matching pipeline or the UI) can consume structured data
instead of printed text.

Reuse note:
    A fetched ``Job.description`` is plain text and can be passed straight
    into ``src.extractors.extract_jd`` (or ``extract_all``) - see
    PROJECT_STATE.md for the full reuse map.
"""

import os
import re
import html
import time
import datetime as dt
from dataclasses import dataclass

import requests
from dotenv import load_dotenv
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

from src.utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

# Make language detection deterministic across runs.
DetectorFactory.seed = 0

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")

# Country code is part of the path; default to Germany ("de").
BASE_URL_TEMPLATE = "https://api.adzuna.com/v1/api/jobs/{country}/search/1"

_TAG_RE = re.compile(r"<[^>]+>")


@dataclass
class Job:
    """A single normalized job posting."""

    title: str
    company: str
    location: str
    url: str
    description: str
    language: str
    id: str = ""  # stable identifier for dedupe (source-specific)
    source: str = ""  # e.g. "adzuna", "arbeitnow"
    posted_at: str = ""  # publication time (unix epoch as string), if known


def _clean_html(raw: str) -> str:
    """
    Strip HTML tags and unescape entities from a description string.

    Args:
        raw (str): Raw description, may contain tags and HTML entities.

    Returns:
        str: Plain text with collapsed whitespace. Empty string if input is falsy.
    """
    if not raw:
        return ""

    text = _TAG_RE.sub(" ", raw)
    text = html.unescape(text)
    # Collapse all runs of whitespace into single spaces.
    return " ".join(text.split())


def _iso_to_epoch(created: str) -> str:
    """Convert an ISO8601 timestamp (e.g. Adzuna 'created') to epoch seconds as a string."""
    if not created:
        return ""
    try:
        d = dt.datetime.fromisoformat(created.replace("Z", "+00:00"))
        return str(int(d.timestamp()))
    except (ValueError, TypeError):
        return ""


def _detect_language(text: str) -> str:
    """
    Detect the ISO 639-1 language code of a piece of text.

    Args:
        text (str): Text to inspect.

    Returns:
        str: Language code (e.g. "en", "de") or "unknown" if detection fails.
    """
    if not text or not text.strip():
        return "unknown"

    try:
        return detect(text)
    except LangDetectException:
        logger.warning("Language detection failed - defaulting to 'unknown'")
        return "unknown"


def _parse_job(raw: dict) -> Job:
    """
    Convert a raw Adzuna result dict into a :class:`Job`.

    Args:
        raw (dict): A single entry from the Adzuna ``results`` array.

    Returns:
        Job: Normalized job with cleaned description and detected language.
    """
    description = _clean_html(raw.get("description", ""))
    title = (raw.get("title") or "").strip()

    return Job(
        title=title,
        company=(raw.get("company", {}) or {}).get("display_name", "").strip(),
        location=(raw.get("location", {}) or {}).get("display_name", "").strip(),
        url=raw.get("redirect_url", ""),
        description=description,
        # Prefer the (longer) description for detection; fall back to title.
        language=_detect_language(description or title),
        id=str(raw.get("id", "")),
        source="adzuna",
        posted_at=_iso_to_epoch(raw.get("created", "")),
    )


def fetch_adzuna_jobs(
    query: str = "machine learning engineer",
    location: str = "berlin",
    results: int = 5,
    country: str = "de",
) -> list[Job]:
    """
    Fetch job postings from the Adzuna API.

    Args:
        query (str):    Search terms (Adzuna ``what`` parameter).
        location (str): Location filter (Adzuna ``where`` parameter).
        results (int):  Number of results per page.
        country (str):  Adzuna country code used in the request path.

    Returns:
        list[Job]: Normalized jobs. Empty list if credentials are missing
                   or the request fails.
    """
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        logger.error("Missing ADZUNA_APP_ID / ADZUNA_APP_KEY - cannot fetch jobs")
        return []

    url = BASE_URL_TEMPLATE.format(country=country)
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "what": query,
        "where": location,
        "results_per_page": results,
        "content-type": "application/json",
    }

    # Retry on transient rate-limit / server errors (429, 5xx).
    response = None
    for attempt in range(3):
        try:
            response = requests.get(url, params=params, timeout=15)
            if response.status_code in (429, 500, 502, 503, 504) and attempt < 2:
                logger.warning(
                    "Adzuna %s for '%s' - retry %d",
                    response.status_code,
                    query,
                    attempt + 1,
                )
                time.sleep(1.0 * (attempt + 1))
                continue
            response.raise_for_status()
            break
        except requests.RequestException as e:
            if attempt < 2:
                time.sleep(1.0 * (attempt + 1))
                continue
            logger.error("Adzuna request failed: %s", e)
            return []

    if response is None:
        return []

    data = response.json()
    raw_jobs = data.get("results", [])
    logger.info(
        "Adzuna returned %d of %d total jobs", len(raw_jobs), data.get("count", 0)
    )

    return [_parse_job(job) for job in raw_jobs]


def fetch_adzuna_multi(
    titles: list[str],
    location: str = "",
    country: str = "de",
    per_title: int = 5,
) -> list[Job]:
    """
    Run one Adzuna search per target title and merge the results.

    Adzuna supports server-side search, so this finds far more AI/ML roles
    than the Arbeitnow feed. Results are deduplicated by id (falling back
    to url).

    Args:
        titles (list[str]): Role phrases to search for, one query each.
        location (str):     Location filter.
        country (str):      Adzuna country code.
        per_title (int):    Results requested per title.

    Returns:
        list[Job]: Unique jobs across all title searches.
    """
    seen: set[str] = set()
    out: list[Job] = []

    for i, title in enumerate(titles):
        if i:
            time.sleep(0.3)  # gentle throttle to avoid Adzuna rate-limit (503)
        for job in fetch_adzuna_jobs(
            query=title, location=location, results=per_title, country=country
        ):
            key = job.id or job.url
            if key and key not in seen:
                seen.add(key)
                out.append(job)

    logger.info(
        "Adzuna multi-title: %d unique jobs across %d titles", len(out), len(titles)
    )
    return out


if __name__ == "__main__":
    # Manual smoke test - prints a compact view of fetched jobs.
    for job in fetch_adzuna_jobs(
        query="python developer", location="berlin", results=3
    ):
        print(f"[{job.language}] {job.title} - {job.company} ({job.location})")
        print(f"  {job.url}")
        print("-" * 60)
