# src/services/job_matcher.py
"""
Job matching service.

Scores fetched jobs against the stored resume and persists the results.
Each job costs one JD-extraction LLM call; the resume is extracted once
(held in session) and reused across all jobs.
"""

from datetime import datetime, timezone

from src.fetchers import Job
from src.fetchers.enrich import fetch_full_description
from src.extractors.jd import extract_jd
from src.matcher import match
from src.utils import session
from src.services import match_store
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Below this length an Adzuna description is just a snippet — fetch the full JD.
_SNIPPET_LIMIT = 1200


def _enrich(job: Job) -> None:
    """Replace a thin Adzuna snippet with the full JD from its detail page."""
    if job.source != "adzuna" or len(job.description) >= _SNIPPET_LIMIT:
        return
    full = fetch_full_description(job.url)
    if full and len(full) > len(job.description):
        logger.info("Enriched '%s': %d -> %d chars",
                    job.title[:40], len(job.description), len(full))
        job.description = full


def _score_one(job: Job, resume_json: dict) -> dict | None:
    """Extract a job's JD and score the resume against it."""
    try:
        jd_json = extract_jd(job.description)
        if not jd_json:
            logger.warning("Empty JD extraction for '%s'", job.title)
            return None

        result = match(resume_json, jd_json)

        return {
            "id":               job.id,
            "source":           job.source,
            "title":            job.title,
            "company":          job.company,
            "location":         job.location,
            "url":              job.url,
            "language":         job.language,
            "posted_at":        job.posted_at,
            "score":            result.get("overall_score", 0),
            "label":            result.get("label", ""),
            "matched_required": result.get("matched_required", []),
            "missing_required": result.get("missing_required", []),
            "scored_at":        datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    except Exception as e:
        logger.error("Scoring failed for '%s': %s", job.title, e)
        return None


def score_new_jobs(jobs: list[Job]) -> dict:
    """
    Score jobs not already in the store, persist them, and return the
    full ranked list.

    Returns:
        dict: {"scored": <int new>, "results": [<all stored, ranked>]}
              or {"error": "no_resume", ...} if no resume is loaded.
    """
    resume_json = session.get_resume()
    if not resume_json:
        return {"error": "no_resume", "scored": 0, "results": match_store.get_all()}

    seen = match_store.known_ids()
    new_jobs = [j for j in jobs if j.id and j.id not in seen]
    logger.info("Scoring %d new jobs (of %d fetched)", len(new_jobs), len(jobs))

    scored = []
    for job in new_jobs:
        _enrich(job)                       # fetch full JD (snippet -> full text)
        item = _score_one(job, resume_json)
        if item:
            scored.append(item)
    match_store.upsert(scored)

    return {
        "scored":  len(scored),
        "new_ids": [s["id"] for s in scored],
        "results": match_store.get_all(),
    }
