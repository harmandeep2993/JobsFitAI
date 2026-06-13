# src/services/job_matcher.py
"""
Job matching service.

Scores fetched jobs against the stored resume and persists the results.
Each job costs one JD-extraction LLM call; the resume is extracted once
(held in session) and reused across all jobs.
"""

import json as _json
from datetime import datetime, timezone

from src.fetchers import Job, fetch_adzuna_multi, fetch_arbeitnow_jobs
from src.fetchers.enrich import fetch_full_description
from src.extractors.jd import extract_jd
from src.matcher import match
from src.utils import session
from src.services import match_store, event_store, relevance, role_filter, vector_store
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Below this length an Adzuna description is just a snippet - fetch the full JD.
_SNIPPET_LIMIT = 1200


def _enrich(job: Job) -> None:
    """Replace a thin Adzuna snippet with the full JD from its detail page."""
    if job.source != "adzuna" or len(job.description) >= _SNIPPET_LIMIT:
        return
    full = fetch_full_description(job.url)
    if full and len(full) > len(job.description):
        logger.debug(
            "Enriched '%s': %d -> %d chars",
            job.title[:40],
            len(job.description),
            len(full),
        )
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
            "id": job.id,
            "source": job.source,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "url": job.url,
            "language": job.language,
            "posted_at": job.posted_at,
            "score": result.get("overall_score", 0),
            "label": result.get("label", ""),
            "matched_required": result.get("matched_required", []),
            "missing_required": result.get("missing_required", []),
            "section_scores": result.get("section_scores", {}),
            "scored_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "jd_json": jd_json,
        }
    except Exception as e:
        logger.error("Scoring failed for '%s': %s", job.title, e)
        return None


# Progress of the current/last run, polled by the dashboard for live updates.
_run_status = {"running": False, "phase": "idle", "checked": 0, "scored": 0, "total": 0}


def get_run_status() -> dict:
    """Snapshot of the current run's progress."""
    return dict(_run_status)


def begin_run() -> bool:
    """Mark a run as starting. Returns False if one is already in progress."""
    if _run_status["running"]:
        return False
    _run_status.update(
        {"running": True, "phase": "fetching", "checked": 0, "scored": 0, "total": 0}
    )
    return True


def end_run() -> None:
    """Force-clear the running flag (e.g. after a failure before scoring)."""
    _run_status.update({"running": False, "phase": "idle"})


def fetch_combined(
    titles: list[str],
    location: str = "",
    countries: list[str] | None = None,
    per_title: int = 5,
    arbeitnow_limit: int = 100,
) -> list[Job]:
    """
    Pull jobs from both sources across one or more countries, and merge.

    - Adzuna: server-side search per target title, per country code.
    - Arbeitnow: Germany feed filtered to target-title roles (only when
      Germany is among the countries; it has no other-country data).

    Deduped by id; the LLM funnel and vector dedup refine further.
    """
    countries = countries or ["de"]

    adzuna: list[Job] = []
    for code in countries:
        adzuna += fetch_adzuna_multi(
            titles, location=location, country=code, per_title=per_title
        )

    arbeitnow: list[Job] = []
    if "de" in countries:
        terms = sorted({w for t in titles for w in t.split()})
        arb_raw = fetch_arbeitnow_jobs(
            query=" ".join(terms), location=location, limit=arbeitnow_limit
        )
        arbeitnow = [j for j in arb_raw if role_filter.is_target_role(j.title, titles)]

    merged, seen_ids, seen_content = [], set(), set()
    for job in adzuna + arbeitnow:
        ckey = (
            (job.title or "").strip().lower()
            + "|"
            + (job.company or "").strip().lower()
        )
        if job.id and job.id not in seen_ids and ckey not in seen_content:
            seen_ids.add(job.id)
            seen_content.add(ckey)
            merged.append(job)

    logger.info(
        "Combined sources (%s): %d adzuna + %d arbeitnow -> %d unique",
        ",".join(countries),
        len(adzuna),
        len(arbeitnow),
        len(merged),
    )
    return merged


def rescore_all() -> int:
    """
    Re-score every stored job against the current resume using the cached
    JD - local embeddings only, no LLM tokens and no re-fetch. Used when a
    new resume is loaded.

    Returns the number of jobs re-scored.
    """
    resume_json = session.get_resume()
    if not resume_json:
        return 0

    rows = match_store.rows_with_jd()
    count = 0
    for row in rows:
        jd = row.get("jd")
        if not jd:
            continue
        try:
            result = match(resume_json, jd)
            match_store.update_score(row["id"], result)
            count += 1
        except Exception as e:
            logger.error("Re-score failed for %s: %s", row["id"], e)

    logger.info("Re-scored %d stored jobs against the new resume", count)
    return count


def discover_and_score(jobs: list[Job], entry_only: bool = True) -> dict:
    """
    Token-efficient funnel:
      skip already-seen -> recency -> cheap LLM relevance gate ->
      full-JD enrich + extract + score.

    Each scored job is persisted immediately so the dashboard can show
    results streaming in. Progress is exposed via get_run_status().
    """
    _run_status["running"] = True  # idempotent (begin_run may have set it)
    resume_json = session.get_resume()
    if not resume_json:
        _run_status.update({"running": False, "phase": "idle"})
        return {
            "error": "no_resume",
            "checked": 0,
            "scored": 0,
            "results": match_store.get_all(),
        }

    seen = event_store.seen_ids()
    new_jobs = [j for j in jobs if j.id and j.id not in seen]

    # --- recency filter (free) ---
    candidates = []
    for job in new_jobs:
        if role_filter.is_recent(job):
            candidates.append(job)
        else:
            event_store.mark_seen(job, "stale")

    logger.info(
        ">> Run: %d fetched, %d new, %d recent",
        len(jobs),
        len(new_jobs),
        len(candidates),
    )

    # --- bulk LLM relevance gate (few calls, not one-per-job) ---
    _run_status.update(
        {"phase": "classifying", "total": len(candidates), "checked": 0, "scored": 0}
    )
    verdicts = relevance.classify_batch(candidates)

    survivors = []
    for job in candidates:
        v = verdicts.get(job.id, {"relevant": True, "entry_level": True})
        if not v["relevant"]:
            event_store.mark_seen(job, "irrelevant")
        elif entry_only and not v["entry_level"]:
            event_store.mark_seen(job, "not_entry")
        else:
            survivors.append(job)

    logger.info("   %d relevant entry-level survivors", len(survivors))
    _run_status.update({"phase": "scoring", "total": len(survivors), "checked": 0})

    scored = 0
    try:
        for job in survivors:
            _run_status["checked"] += 1
            tag = f"{job.title[:42]} @ {job.company[:20]}"

            # cross-source near-duplicate dedup (free, local embeddings)
            if vector_store.is_duplicate(job):
                event_store.mark_seen(job, "duplicate")
                logger.debug("   skip duplicate | %s", tag)
                continue

            # store metadata now (appears on dashboard), then enrich + score
            match_store.upsert_pending(job)
            vector_store.add(job)

            _enrich(job)
            item = _score_one(job, resume_json)
            jd = item.get("jd_json") if item else None
            has_jd = bool(
                jd and (jd.get("required_skills") or jd.get("responsibilities"))
            )

            if item and has_jd:
                item["status"] = "scored"
                match_store.upsert([item])
                scored += 1
                _run_status["scored"] = scored
                event_store.mark_seen(job, "scored")
                event_store.log_event(
                    "scored", job.id, f"{round(item['score'])}% · {item['title'][:40]}"
                )
                logger.debug("   stored %3d%% | %s", round(item["score"]), tag)
            else:
                # JD not on Adzuna (real posting lives elsewhere) - keep for
                # manual review instead of a fake score.
                match_store.set_status(job.id, "jd_unavailable")
                event_store.mark_seen(job, "jd_unavailable")
                logger.debug("   jd-unavailable | %s", tag)

        by_source = {}
        for j in jobs:
            by_source[j.source] = by_source.get(j.source, 0) + 1

        run_detail = _json.dumps(
            {
                "fetched": len(jobs),
                "new": len(new_jobs),
                "recent": len(candidates),
                "relevant": len(survivors),
                "scored": scored,
                "adzuna": by_source.get("adzuna", 0),
                "arbeitnow": by_source.get("arbeitnow", 0),
                "total_seen": len(seen) + len(new_jobs),
            }
        )
        event_store.log_event("run", "", run_detail)
        logger.info(
            "== Run complete: %d candidates, %d survivors, %d scored",
            len(candidates),
            len(survivors),
            scored,
        )
    finally:
        _run_status.update({"running": False, "phase": "idle"})

    return {
        "checked": len(candidates),
        "scored": scored,
        "results": match_store.get_all(),
    }
