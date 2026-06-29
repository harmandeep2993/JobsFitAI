# api/routes/matches.py
"""
/api/match/* endpoints - job fetch, score, and state.
"""

import asyncio
import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request

from core.config import MAX_AGE_DAYS, SEARCH_PER_TITLE
from core.logger import get_logger
from core import session
from extractors.jd import extract_jd
from matcher.matcher import match
from parsers import extract_all_text
from extractors.resume import extract_resume
from repositories import event_repo as event_store
from repositories import match_repo as match_store
from repositories import settings_repo as settings_store
from services.job_matcher import (
    begin_run,
    discover_and_score,
    end_run,
    fetch_combined,
    get_run_status,
    rescore_all,
)
from services.summary import generate_summary
from services import vector_store

logger = get_logger(__name__)

router = APIRouter()


def _resume_diff(old: dict, new: dict) -> dict:
    """Compare two extracted resume dicts and return what changed."""

    def flat_skills(r):
        s = r.get("skills", [])
        if isinstance(s, list):
            return {x.lower().strip() for x in s if isinstance(x, str)}
        if isinstance(s, dict):
            out = set()
            for v in s.values():
                if isinstance(v, list):
                    out.update(x.lower().strip() for x in v if isinstance(x, str))
            return out
        return set()

    old_skills = flat_skills(old)
    new_skills = flat_skills(new)

    old_exp = {
        (e.get("title", "") + "|" + e.get("company", "")).lower()
        for e in old.get("experience_entries", [])
    }
    new_exp = {
        (e.get("title", "") + "|" + e.get("company", "")).lower()
        for e in new.get("experience_entries", [])
    }

    old_yrs = (old.get("meta") or {}).get("total_experience_years", 0)
    new_yrs = (new.get("meta") or {}).get("total_experience_years", 0)

    return {
        "skills_added": sorted(new_skills - old_skills),
        "skills_removed": sorted(old_skills - new_skills),
        "exp_added": sorted(new_exp - old_exp),
        "exp_removed": sorted(old_exp - new_exp),
        "years_before": old_yrs,
        "years_after": new_yrs,
        "languages_before": old.get("languages", []),
        "languages_after": new.get("languages", []),
    }


@router.post("/resume")
async def api_match_resume(request: Request) -> JSONResponse:
    """Parse + extract an uploaded resume and store it for matching."""
    import os

    body = await request.json()
    tmp = (body.get("tmp") or "").strip()
    name = (body.get("name") or "resume").strip()

    if not tmp or not os.path.exists(tmp):
        return JSONResponse(
            {"ok": False, "error": "resume file not found"}, status_code=400
        )

    def _process() -> dict:
        text = extract_all_text(tmp)
        if not text or len(text) < 50:
            return {}
        return extract_resume(text)

    resume_json = await run_in_threadpool(_process)

    if not resume_json:
        return JSONResponse(
            {"ok": False, "error": "could not parse resume"}, status_code=422
        )

    prev_resume = session.get_resume()
    diff = _resume_diff(prev_resume, resume_json) if prev_resume else None

    session.set_resume(resume_json, name)

    rescored = await run_in_threadpool(rescore_all)
    if rescored:
        event_store.log_event("rescore", "", f"{rescored} jobs re-scored vs {name}")

    years = resume_json.get("meta", {}).get("total_experience_years", 0)
    return JSONResponse(
        {
            "ok": True,
            "name": name,
            "experience_years": years,
            "rescored": rescored,
            "diff": diff,
        }
    )


@router.get("/run")
async def api_match_run(request: Request) -> JSONResponse:
    """
    Kick off a background job-fetch-and-score run.

    Returns immediately with {started: true} and runs the pipeline in a
    background task. Only one run can be active at a time.
    """
    if not session.has_resume():
        return JSONResponse(
            {"ok": False, "error": "no_resume", "results": match_store.get_all()},
            status_code=400,
        )

    if not begin_run():
        return JSONResponse({"ok": True, "started": False, "already_running": True})

    params = request.query_params
    query = (params.get("query") or "").strip()
    entry_only = params.get("entry_only", "true").lower() != "false"
    titles = [query] if query else settings_store.get_titles()
    location = (params.get("location") or "").strip() or settings_store.get_location()
    countries = settings_store.get_countries()

    async def _bg() -> None:
        def _run() -> None:
            jobs = fetch_combined(
                titles,
                location=location,
                countries=countries,
                per_title=SEARCH_PER_TITLE,
                arbeitnow_limit=settings_store.get_arbeitnow_limit(),
                bundesagentur_limit=settings_store.get_bundesagentur_limit(),
            )
            discover_and_score(jobs, entry_only=entry_only, manual=True)

        try:
            await run_in_threadpool(_run)
        except Exception as e:
            logger.error("match run failed: %s", e)
            try:
                import json as _j

                event_store.log_event(
                    "run",
                    "",
                    _j.dumps(
                        {
                            "fetched": 0,
                            "new": 0,
                            "recent": 0,
                            "relevant": 0,
                            "scored": 0,
                            "adzuna": 0,
                            "arbeitnow": 0,
                            "bundesagentur": 0,
                            "total_seen": 0,
                            "manual": True,
                            "error": str(e)[:120],
                        }
                    ),
                )
            except Exception:
                pass
            end_run()

    asyncio.create_task(_bg())
    return JSONResponse({"ok": True, "started": True})


@router.get("/state")
async def api_match_state() -> JSONResponse:
    """Full state snapshot polled by the frontend while a run is active."""
    return JSONResponse(
        {
            "ok": True,
            "has_resume": session.has_resume(),
            "resume_name": session.get_resume_name(),
            "filters": {
                "target_titles": settings_store.get_titles(),
                "countries": settings_store.country_names(),
                "location": settings_store.get_location(),
                "max_age_days": MAX_AGE_DAYS,
                "entry_only": settings_store.get_entry_only(),
                "arbeitnow_limit": settings_store.get_arbeitnow_limit(),
                "bundesagentur_limit": settings_store.get_bundesagentur_limit(),
            },
            "stats": event_store.stats(),
            "run_status": get_run_status(),
            "resume": session.resume_info(),
            "scheduler": {
                "enabled": settings_store.get_scheduler_enabled(),
                "interval": settings_store.get_scheduler_interval(),
            },
            "results": match_store.get_all(),
        }
    )


@router.post("/applied")
async def api_match_applied(request: Request) -> JSONResponse:
    """Toggle the applied flag on a scored job and log an 'applied' event."""
    body = await request.json()
    job_id = (body.get("id") or "").strip()
    applied = bool(body.get("applied"))
    if not job_id:
        return JSONResponse({"ok": False, "error": "id required"}, status_code=400)
    match_store.set_applied(job_id, applied)
    if applied:
        event_store.log_event("applied", job_id)
    return JSONResponse({"ok": True, "id": job_id, "applied": applied})


@router.post("/app-status")
async def api_match_app_status(request: Request) -> JSONResponse:
    """Set the application status for a job (applied / interview / offer / rejected)."""
    body = await request.json()
    job_id = (body.get("id") or "").strip()
    status = (body.get("status") or "").strip().lower()
    if not job_id:
        return JSONResponse({"ok": False, "error": "id required"}, status_code=400)
    match_store.set_app_status(job_id, status)
    if status == "applied":
        event_store.log_event("applied", job_id)
    return JSONResponse({"ok": True, "id": job_id, "app_status": status})


@router.get("/detail")
async def api_match_detail(request: Request) -> JSONResponse:
    """
    Return full detail for a scored job, lazily generating an LLM summary if absent.
    """
    job_id = (request.query_params.get("id") or "").strip()
    row = match_store.get_one(job_id)
    if not row:
        return JSONResponse({"ok": False, "error": "not found"}, status_code=404)

    summary = row.get("summary")
    if not summary and session.has_resume():
        resume_json = session.get_resume()
        results = {
            "overall_score": row.get("score", 0),
            "label": row.get("label", ""),
            "section_scores": row.get("section_scores", {}),
            "matched_required": row.get("matched_required", []),
            "missing_required": row.get("missing_required", []),
            "matched_preferred": [],
            "missing_preferred": [],
        }
        try:
            summary = await run_in_threadpool(
                generate_summary, resume_json, row.get("jd_json", {}), results
            )
            match_store.set_summary(job_id, summary)
        except Exception as e:
            logger.error("summary generation failed: %s", e)
            summary = ""

    return JSONResponse(
        {
            "ok": True,
            "job": {
                "id": row["id"],
                "title": row["title"],
                "company": row["company"],
                "location": row["location"],
                "url": row["url"],
                "language": row["language"],
                "posted_at": row["posted_at"],
                "score": row["score"],
                "label": row["label"],
                "applied": row.get("applied", 0),
            },
            "section_scores": row.get("section_scores", {}),
            "matched_required": row.get("matched_required", []),
            "missing_required": row.get("missing_required", []),
            "jd": row.get("jd_json", {}),
            "resume": session.resume_info(),
            "summary": summary or "",
        }
    )


@router.post("/filters")
async def api_match_filters(request: Request) -> JSONResponse:
    """Update target titles, countries, and/or location filter."""
    body = await request.json()

    if isinstance(body.get("target_titles"), list):
        settings_store.set_titles(body["target_titles"])

    if "countries" in body:
        c = body["countries"]
        names = c if isinstance(c, list) else str(c).replace(",", " ").split()
        settings_store.set_countries(names)

    if "location" in body:
        settings_store.set_location(body.get("location") or "")

    if "entry_only" in body:
        settings_store.set_entry_only(bool(body["entry_only"]))

    if "arbeitnow_limit" in body:
        try:
            settings_store.set_arbeitnow_limit(int(body["arbeitnow_limit"]))
        except (ValueError, TypeError):
            pass

    if "bundesagentur_limit" in body:
        try:
            settings_store.set_bundesagentur_limit(int(body["bundesagentur_limit"]))
        except (ValueError, TypeError):
            pass

    return JSONResponse(
        {
            "ok": True,
            "target_titles": settings_store.get_titles(),
            "countries": settings_store.country_names(),
            "location": settings_store.get_location(),
            "entry_only": settings_store.get_entry_only(),
            "arbeitnow_limit": settings_store.get_arbeitnow_limit(),
            "bundesagentur_limit": settings_store.get_bundesagentur_limit(),
        }
    )


@router.post("/score-jd")
async def api_score_jd(request: Request) -> JSONResponse:
    """Score a jd_unavailable job using a manually pasted JD."""
    body = await request.json()
    job_id = (body.get("id") or "").strip()
    jd_text = (body.get("jd_text") or "").strip()

    if not job_id:
        return JSONResponse({"ok": False, "error": "id required"}, status_code=400)
    if len(jd_text) < 50:
        return JSONResponse(
            {"ok": False, "error": "jd_text too short"}, status_code=400
        )
    if not session.has_resume():
        return JSONResponse({"ok": False, "error": "no_resume"}, status_code=400)

    row = match_store.get_one(job_id)
    if not row:
        return JSONResponse({"ok": False, "error": "job not found"}, status_code=404)

    def _score():
        try:
            jd_json = extract_jd(jd_text)
        except Exception as exc:
            logger.warning("extract_jd failed: %s", exc)
            return None, None
        if not jd_json:
            return None, None
        try:
            return jd_json, match(session.get_resume(), jd_json)
        except Exception as exc:
            logger.exception("match() failed in score-jd: %s", exc)
            return None, None

    jd_json, result = await run_in_threadpool(_score)
    if not result:
        return JSONResponse(
            {"ok": False, "error": "could not parse JD"}, status_code=422
        )

    match_store.upsert(
        [
            {
                "id": job_id,
                "source": row["source"],
                "title": row["title"],
                "company": row["company"],
                "location": row["location"],
                "url": row["url"],
                "language": row["language"],
                "posted_at": row["posted_at"],
                "score": result.get("overall_score", 0),
                "label": result.get("label", ""),
                "matched_required": result.get("matched_required", []),
                "missing_required": result.get("missing_required", []),
                "section_scores": result.get("section_scores", {}),
                "scored_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "jd_json": jd_json,
                "status": "scored",
            }
        ]
    )

    return JSONResponse(
        {
            "ok": True,
            "score": result.get("overall_score", 0),
            "label": result.get("label", ""),
        }
    )


@router.post("/scheduler")
async def api_match_scheduler(request: Request) -> JSONResponse:
    """Enable/disable the auto-fetch scheduler or change its interval (minutes)."""
    from app import _sched_last_ref

    body = await request.json()
    if "enabled" in body:
        settings_store.set_scheduler_enabled(bool(body["enabled"]))
        if body.get("enabled"):
            _sched_last_ref[0] = 0.0
    if "interval" in body:
        settings_store.set_scheduler_interval(int(body["interval"]))
    return JSONResponse(
        {
            "ok": True,
            "enabled": settings_store.get_scheduler_enabled(),
            "interval": settings_store.get_scheduler_interval(),
        }
    )


@router.post("/delete")
async def api_match_delete(request: Request) -> JSONResponse:
    body = await request.json()
    job_id = (body.get("id") or "").strip()
    if not job_id:
        return JSONResponse({"ok": False, "error": "id required"}, status_code=400)
    match_store.delete(job_id)
    event_store.block(job_id)
    return JSONResponse({"ok": True})


@router.post("/clear")
async def api_match_clear() -> JSONResponse:
    match_store.clear()
    event_store.clear()
    vector_store.clear()
    return JSONResponse({"ok": True})


@router.get("/export")
async def api_match_export() -> StreamingResponse:
    """Download all scored matches as a CSV file."""
    rows = match_store.get_all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "title",
            "company",
            "location",
            "score",
            "label",
            "language",
            "posted_at",
            "applied",
            "url",
        ]
    )
    for r in rows:
        posted = r.get("posted_at") or ""
        if posted and posted.isdigit():
            try:
                posted = datetime.fromtimestamp(int(posted), tz=timezone.utc).strftime(
                    "%Y-%m-%d"
                )
            except (OSError, OverflowError):
                pass
        writer.writerow(
            [
                r.get("title", ""),
                r.get("company", ""),
                r.get("location", ""),
                r.get("score", ""),
                r.get("label", ""),
                r.get("language", ""),
                posted,
                "yes" if r.get("applied") else "no",
                r.get("url", ""),
            ]
        )

    buf.seek(0)
    filename = "jobsfitai_matches.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
