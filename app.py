# app.py

"""
Application entry point for JobFitAI.

Responsibilities:
- Serve the static frontend (templates/index.html + assets/)
- Expose all REST API endpoints
- Run background auto-fetch scheduler
- Start the FastAPI/uvicorn server
"""

import csv
import io
import os
import time
import asyncio
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Set

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from starlette.requests import Request
from starlette.concurrency import run_in_threadpool

from src.utils.logger import get_logger

logger = get_logger("app")

from src.utils import session
from src.utils.router import check_llm
from src.parsers import extract_all_text
from src.extractors import extract_all
from src.extractors.resume import extract_resume
from src.matcher.matcher import match
from src.frontend.results import build_results_html
from src.services.job_matcher import (
    discover_and_score,
    begin_run,
    end_run,
    get_run_status,
    rescore_all,
    fetch_combined,
)
from src.services import match_store, event_store, vector_store, settings_store
from src.services.summary import generate_summary
from src.utils.config import SEARCH_PER_TITLE, MAX_AGE_DAYS


app = FastAPI(title="JobFitAI")

# Static assets
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Allowed resume file extensions
ALLOWED_EXTENSIONS: Set[str] = {".pdf", ".docx"}

# Maximum allowed upload size (MB)
MAX_FILE_MB: int = 5


# ── Frontend ──────────────────────────────────────────────

@app.get("/")
async def index() -> HTMLResponse:
    with open("templates/index.html", encoding="utf-8") as f:
        return HTMLResponse(f.read())


# ── Resume upload ─────────────────────────────────────────

@app.post("/api/upload")
async def api_upload(request: Request) -> JSONResponse:
    """
    Handle resume file uploads.

    Returns {ok, name, tmp, kb, ext} on success.
    """
    form   = await request.form()
    upload = form.get("file")

    if upload is None:
        return JSONResponse({"ok": False, "error": "no file uploaded"}, status_code=400)

    data     = await upload.read()
    filename = upload.filename or "resume"
    suffix   = Path(filename).suffix.lower()

    if len(data) > MAX_FILE_MB * 1024 * 1024:
        return JSONResponse({"ok": False, "error": "file too large"}, status_code=400)

    if suffix not in ALLOWED_EXTENSIONS:
        return JSONResponse({"ok": False, "error": "unsupported file type"}, status_code=400)

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(data)
        temp_path = tmp_file.name

    return JSONResponse({
        "ok":   True,
        "name": filename,
        "tmp":  temp_path,
        "kb":   round(len(data) / 1024, 1),
        "ext":  suffix.upper()[1:],
    })


# ── Analyzer ──────────────────────────────────────────────

@app.post("/api/analyze")
async def api_analyze(request: Request) -> JSONResponse:
    """
    Full analysis pipeline: parse resume → extract → score → summarize.

    Body: {"tmp": <temp path from /api/upload>, "jd": <job description text>}
    Returns: {"ok": true, "score": float, "label": str, "html": str}
    """
    body    = await request.json()
    tmp     = (body.get("tmp") or "").strip()
    jd_text = (body.get("jd")  or "").strip()

    if not tmp or not os.path.exists(tmp):
        return JSONResponse({"ok": False, "error": "resume file not found"}, status_code=400)
    if len(jd_text) < 50:
        return JSONResponse({"ok": False, "error": "job description too short"}, status_code=400)
    if not check_llm():
        return JSONResponse({"ok": False, "error": "llm_unavailable"}, status_code=503)

    def _run():
        resume_text = extract_all_text(tmp)
        if not resume_text or len(resume_text) < 50:
            return None, None, None, None

        resume_json, jd_json = extract_all(resume_text, jd_text)
        if not resume_json or not jd_json:
            return resume_json, jd_json, None, None

        results = match(resume_json, jd_json)
        summary = generate_summary(resume_json, jd_json, results)
        return resume_json, jd_json, results, summary

    try:
        resume_json, jd_json, results, summary = await run_in_threadpool(_run)
    except Exception as e:
        logger.error("analyze failed: %s", e)
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)
    finally:
        try:
            if tmp and os.path.exists(tmp):
                os.unlink(tmp)
        except OSError:
            pass

    if not resume_json and not jd_json:
        return JSONResponse({"ok": False, "error": "could not parse resume"}, status_code=422)
    if not resume_json:
        return JSONResponse({"ok": False, "error": "resume_extraction_failed"}, status_code=422)
    if not jd_json:
        return JSONResponse({"ok": False, "error": "jd_extraction_failed"}, status_code=422)
    if not results:
        return JSONResponse({"ok": False, "error": "scoring_failed"}, status_code=500)

    html = build_results_html(results, resume_json, jd_json, summary or "")
    return JSONResponse({
        "ok":    True,
        "score": results.get("overall_score", 0),
        "label": results.get("label", ""),
        "html":  html,
    })


# ── LLM settings ──────────────────────────────────────────

@app.get("/api/llm-settings")
async def api_get_llm_settings() -> JSONResponse:
    return JSONResponse({
        "ok":        True,
        "current":   session.get_settings(),
        "providers": session.provider_catalog(),
    })


@app.post("/api/llm-settings")
async def api_set_llm_settings(request: Request) -> JSONResponse:
    body     = await request.json()
    provider = (body.get("provider") or "").strip()
    model    = (body.get("model")    or "").strip()

    try:
        session.set_active(provider, model)
    except ValueError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)

    online = await run_in_threadpool(check_llm)

    return JSONResponse({
        "ok":      True,
        "current": session.get_settings(),
        "online":  online,
    })


# ── Resume diff ───────────────────────────────────────────

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
        "skills_added":   sorted(new_skills - old_skills),
        "skills_removed": sorted(old_skills - new_skills),
        "exp_added":      sorted(new_exp - old_exp),
        "exp_removed":    sorted(old_exp - new_exp),
        "years_before":   old_yrs,
        "years_after":    new_yrs,
        "languages_before": old.get("languages", []),
        "languages_after":  new.get("languages", []),
    }


# ── Job matches ───────────────────────────────────────────

@app.post("/api/match/resume")
async def api_match_resume(request: Request) -> JSONResponse:
    """Parse + extract an uploaded resume and store it for matching."""
    body = await request.json()
    tmp  = (body.get("tmp")  or "").strip()
    name = (body.get("name") or "resume").strip()

    if not tmp or not os.path.exists(tmp):
        return JSONResponse({"ok": False, "error": "resume file not found"}, status_code=400)

    def _process() -> dict:
        text = extract_all_text(tmp)
        if not text or len(text) < 50:
            return {}
        return extract_resume(text)

    resume_json = await run_in_threadpool(_process)
    try:
        if os.path.exists(tmp):
            os.unlink(tmp)
    except OSError:
        pass

    if not resume_json:
        return JSONResponse({"ok": False, "error": "could not parse resume"}, status_code=422)

    prev_resume = session.get_resume()
    diff = _resume_diff(prev_resume, resume_json) if prev_resume else None

    session.set_resume(resume_json, name)

    rescored = await run_in_threadpool(rescore_all)
    if rescored:
        event_store.log_event("rescore", "", f"{rescored} jobs re-scored vs {name}")

    years = resume_json.get("meta", {}).get("total_experience_years", 0)
    return JSONResponse({
        "ok": True,
        "name": name,
        "experience_years": years,
        "rescored": rescored,
        "diff": diff,
    })


@app.get("/api/match/run")
async def api_match_run(request: Request) -> JSONResponse:
    if not session.has_resume():
        return JSONResponse(
            {"ok": False, "error": "no_resume", "results": match_store.get_all()},
            status_code=400,
        )

    if not begin_run():
        return JSONResponse({"ok": True, "started": False, "already_running": True})

    params     = request.query_params
    query      = (params.get("query") or "").strip()
    entry_only = params.get("entry_only", "true").lower() != "false"
    titles     = [query] if query else settings_store.get_titles()
    location   = (params.get("location") or "").strip() or settings_store.get_location()
    countries  = settings_store.get_countries()

    async def _bg() -> None:
        def _run() -> None:
            jobs = fetch_combined(titles, location=location, countries=countries, per_title=SEARCH_PER_TITLE)
            discover_and_score(jobs, entry_only=entry_only)

        try:
            await run_in_threadpool(_run)
        except Exception as e:
            logger.error("match run failed: %s", e)
            end_run()

    asyncio.create_task(_bg())
    return JSONResponse({"ok": True, "started": True})


@app.get("/api/match/state")
async def api_match_state() -> JSONResponse:
    return JSONResponse({
        "ok":          True,
        "has_resume":  session.has_resume(),
        "resume_name": session.get_resume_name(),
        "filters": {
            "target_titles": settings_store.get_titles(),
            "countries":     settings_store.country_names(),
            "location":      settings_store.get_location(),
            "max_age_days":  MAX_AGE_DAYS,
        },
        "stats":       event_store.stats(),
        "run_status":  get_run_status(),
        "resume":      session.resume_info(),
        "scheduler": {
            "enabled":  settings_store.get_scheduler_enabled(),
            "interval": settings_store.get_scheduler_interval(),
        },
        "results": match_store.get_all(),
    })


@app.post("/api/match/applied")
async def api_match_applied(request: Request) -> JSONResponse:
    body   = await request.json()
    job_id = (body.get("id") or "").strip()
    applied = bool(body.get("applied"))
    if not job_id:
        return JSONResponse({"ok": False, "error": "id required"}, status_code=400)
    match_store.set_applied(job_id, applied)
    if applied:
        event_store.log_event("applied", job_id)
    return JSONResponse({"ok": True, "id": job_id, "applied": applied})


@app.get("/api/match/detail")
async def api_match_detail(request: Request) -> JSONResponse:
    job_id = (request.query_params.get("id") or "").strip()
    row    = match_store.get_one(job_id)
    if not row:
        return JSONResponse({"ok": False, "error": "not found"}, status_code=404)

    summary = row.get("summary")
    if not summary and session.has_resume():
        resume_json = session.get_resume()
        results = {
            "overall_score":    row.get("score", 0),
            "label":            row.get("label", ""),
            "section_scores":   row.get("section_scores", {}),
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

    return JSONResponse({
        "ok": True,
        "job": {
            "id":        row["id"],
            "title":     row["title"],
            "company":   row["company"],
            "location":  row["location"],
            "url":       row["url"],
            "language":  row["language"],
            "posted_at": row["posted_at"],
            "score":     row["score"],
            "label":     row["label"],
            "applied":   row.get("applied", 0),
        },
        "section_scores":   row.get("section_scores", {}),
        "matched_required": row.get("matched_required", []),
        "missing_required": row.get("missing_required", []),
        "jd":               row.get("jd_json", {}),
        "resume":           session.resume_info(),
        "summary":          summary or "",
    })


@app.post("/api/match/filters")
async def api_match_filters(request: Request) -> JSONResponse:
    body = await request.json()

    if isinstance(body.get("target_titles"), list):
        settings_store.set_titles(body["target_titles"])

    if "countries" in body:
        c     = body["countries"]
        names = c if isinstance(c, list) else str(c).replace(",", " ").split()
        settings_store.set_countries(names)

    if "location" in body:
        settings_store.set_location(body.get("location") or "")

    return JSONResponse({
        "ok":            True,
        "target_titles": settings_store.get_titles(),
        "countries":     settings_store.country_names(),
        "location":      settings_store.get_location(),
    })


@app.post("/api/match/scheduler")
async def api_match_scheduler(request: Request) -> JSONResponse:
    global _sched_last
    body = await request.json()
    if "enabled" in body:
        settings_store.set_scheduler_enabled(bool(body["enabled"]))
        if body.get("enabled"):
            _sched_last = 0.0
    if "interval" in body:
        settings_store.set_scheduler_interval(int(body["interval"]))
    return JSONResponse({
        "ok":       True,
        "enabled":  settings_store.get_scheduler_enabled(),
        "interval": settings_store.get_scheduler_interval(),
    })


@app.post("/api/match/delete")
async def api_match_delete(request: Request) -> JSONResponse:
    body   = await request.json()
    job_id = (body.get("id") or "").strip()
    if not job_id:
        return JSONResponse({"ok": False, "error": "id required"}, status_code=400)
    match_store.delete(job_id)
    event_store.block(job_id)
    return JSONResponse({"ok": True})


@app.post("/api/match/clear")
async def api_match_clear() -> JSONResponse:
    match_store.clear()
    event_store.clear()
    vector_store.clear()
    return JSONResponse({"ok": True})


@app.get("/api/match/export")
async def api_match_export() -> StreamingResponse:
    """Download all scored matches as a CSV file."""
    rows = match_store.get_all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "title", "company", "location", "score", "label",
        "language", "posted_at", "applied", "url",
    ])
    for r in rows:
        posted = r.get("posted_at") or ""
        if posted and posted.isdigit():
            try:
                posted = datetime.fromtimestamp(int(posted), tz=timezone.utc).strftime("%Y-%m-%d")
            except (OSError, OverflowError):
                pass
        writer.writerow([
            r.get("title", ""),
            r.get("company", ""),
            r.get("location", ""),
            r.get("score", ""),
            r.get("label", ""),
            r.get("language", ""),
            posted,
            "yes" if r.get("applied") else "no",
            r.get("url", ""),
        ])

    buf.seek(0)
    filename = "jobfitai_matches.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ── Background scheduler ──────────────────────────────────

_sched_last = 0.0


async def _auto_fetch_loop() -> None:
    global _sched_last
    while True:
        await asyncio.sleep(30)
        try:
            if not settings_store.get_scheduler_enabled():
                continue
            interval = settings_store.get_scheduler_interval() * 60
            if _sched_last and (time.monotonic() - _sched_last) < interval:
                continue
            if not session.has_resume() or get_run_status()["running"]:
                continue

            _sched_last = time.monotonic()

            def _run() -> dict:
                jobs = fetch_combined(
                    settings_store.get_titles(),
                    location=settings_store.get_location(),
                    countries=settings_store.get_countries(),
                    per_title=SEARCH_PER_TITLE,
                )
                return discover_and_score(jobs, entry_only=True)

            out = await run_in_threadpool(_run)
            logger.info(
                "[scheduler] auto-fetch: %d checked, %d scored",
                out.get("checked", 0),
                out.get("scored", 0),
            )
        except Exception as e:
            logger.error("[scheduler] error: %s", e)


@app.on_event("startup")
async def _start_scheduler() -> None:
    asyncio.create_task(_auto_fetch_loop())
    logger.info(
        "[scheduler] loop started (enabled=%s, every %s min)",
        settings_store.get_scheduler_enabled(),
        settings_store.get_scheduler_interval(),
    )


# ── Entry point ───────────────────────────────────────────

PORT = 8080


def _port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


if __name__ == "__main__":
    import uvicorn

    if _port_in_use(PORT):
        import sys
        print(
            f"\n[JobFitAI] Port {PORT} is already in use — an old server is still running.\n"
            f"           Stop it first, then re-run:\n"
            f"           Windows    : taskkill /F /IM python.exe\n"
            f"           macOS/Linux: kill $(lsof -ti tcp:{PORT})\n"
        )
        sys.exit(1)

    uvicorn.run("app:app", host="0.0.0.0", port=PORT, reload=False)
