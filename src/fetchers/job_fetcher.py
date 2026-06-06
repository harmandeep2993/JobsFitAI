# src/fetchers/job_fetcher.py
"""
Adzuna job fetcher.

Fetches job postings from the Adzuna search API and normalizes each
result into a :class:`Job` dataclass. Returns a list of jobs so callers
(the extraction/matching pipeline or the UI) can consume structured data
instead of printed text.

Reuse note:
    A fetched ``Job.description`` is plain text and can be passed straight
    into ``src.extractors.extract_jd`` (or ``extract_all``) — see
    PROJECT_STATE.md for the full reuse map.
"""

import os
import re
import html
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
        logger.warning("Language detection failed — defaulting to 'unknown'")
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
        logger.error("Missing ADZUNA_APP_ID / ADZUNA_APP_KEY — cannot fetch jobs")
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

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error("Adzuna request failed: %s", e)
        return []

    data = response.json()
    raw_jobs = data.get("results", [])
    logger.info(
        "Adzuna returned %d of %d total jobs", len(raw_jobs), data.get("count", 0)
    )

    return [_parse_job(job) for job in raw_jobs]


if __name__ == "__main__":
    # Manual smoke test — prints a compact view of fetched jobs.
    for job in fetch_adzuna_jobs(query="python developer", location="berlin", results=3):
        print(f"[{job.language}] {job.title} — {job.company} ({job.location})")
        print(f"  {job.url}")
        print("-" * 60)
