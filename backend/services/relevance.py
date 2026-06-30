# services/relevance.py
"""
LLM relevance gate for the Job Matches funnel.

Classifies jobs by title only - snippets are unreliable (BA posts metadata,
Adzuna posts company intros in the first N chars). The title alone reliably
signals relevance (AI/ML/Data vs unrelated) and seniority (Senior/Lead in
title). Batch size 30 titles per LLM call keeps cost low.
"""

from core.logger import get_logger
from services.llm.router import call_llm, parse_json_response

logger = get_logger(__name__)

_PROMPT = """Screen a job title for an entry-level AI/ML/Data candidate.

relevant=true: AI, ML, Data Science, NLP, LLM, GenAI, MLOps, Computer Vision, Data Analyst, Analytics Engineer, Applied Scientist (incl. junior/graduate/trainee). NOT sales, marketing, finance, HR, civil/mechanical engineering, general software dev unrelated to AI.
entry_level=true by DEFAULT. false ONLY if title contains: senior/sr/lead/principal/staff/head/director/manager/architect.

Return ONLY JSON: {{"relevant": true/false, "entry_level": true/false, "reason": "<=8 words"}}

TITLE: {title}
JSON:"""


_BATCH_PROMPT = """Screen job titles for an entry-level AI/ML/Data candidate.

relevant=true: AI, ML, Data Science, NLP, LLM, GenAI, MLOps, Computer Vision, Data Analyst, Analytics Engineer, Applied Scientist roles (incl. junior/graduate/trainee/working-student). NOT sales, marketing, finance, HR, civil/mechanical engineering, general software dev unrelated to AI.
entry_level=true by DEFAULT. false ONLY if title contains: senior/sr/lead/principal/staff/head/director/manager/architect.

Return ONLY a JSON array: [{{"n":1,"relevant":true,"entry_level":true}}, ...]

TITLES ({count}):
{jobs}

JSON:"""

_BATCH_SIZE = 30


def _classify_chunk(chunk: list) -> dict:
    lines = []
    for n, j in enumerate(chunk, 1):
        lines.append(f"{n}. {j.title}")
    prompt = _BATCH_PROMPT.format(count=len(chunk), jobs="\n".join(lines))

    out: dict = {}
    llm_ok = False
    try:
        _r = call_llm(prompt)
        data = parse_json_response(_r.text) if (_r and _r.text) else None
        if isinstance(data, list):
            llm_ok = True
            for obj in data:
                n = obj.get("n") if isinstance(obj, dict) else None
                if isinstance(n, int) and 1 <= n <= len(chunk):
                    out[chunk[n - 1].id] = {
                        "relevant": bool(obj.get("relevant")),
                        "entry_level": bool(obj.get("entry_level")),
                    }
    except Exception as e:
        logger.error("batch classify failed: %s", e)

    if llm_ok:
        # LLM responded but may have skipped some jobs - fail open for those only.
        for j in chunk:
            out.setdefault(j.id, {"relevant": True, "entry_level": True})
    else:
        # LLM call crashed entirely - fail closed so junk doesn't flood the scorer.
        logger.warning(
            "LLM classify failed for entire batch of %d - defaulting all to relevant=False",
            len(chunk),
        )
        for j in chunk:
            out.setdefault(j.id, {"relevant": False, "entry_level": False})
    return out


def classify_batch(jobs: list) -> dict:
    """
    Classify many jobs with few LLM calls (chunks of _BATCH_SIZE).

    Returns {job_id: {"relevant": bool, "entry_level": bool}}.
    """
    verdicts: dict = {}
    for i in range(0, len(jobs), _BATCH_SIZE):
        verdicts.update(_classify_chunk(jobs[i : i + _BATCH_SIZE]))
    logger.info(
        "Classified %d jobs in %d batch call(s)",
        len(jobs),
        (len(jobs) + _BATCH_SIZE - 1) // _BATCH_SIZE,
    )
    return verdicts


def classify(title: str, snippet: str = "") -> dict:
    """
    Return {"relevant": bool, "entry_level": bool, "reason": str}.

    On any failure, fails OPEN (relevant=True, entry_level=True) so a flaky
    LLM call doesn't silently drop a job - the scorer still runs.
    """
    prompt = _PROMPT.format(title=title or "")
    try:
        _r = call_llm(prompt)
        data = parse_json_response(_r.text) if (_r and _r.text) else None
        if isinstance(data, dict) and "relevant" in data:
            return {
                "relevant": bool(data.get("relevant")),
                "entry_level": bool(data.get("entry_level")),
                "reason": str(data.get("reason", ""))[:80],
            }
    except Exception as e:
        logger.error("Relevance classify failed for '%s': %s", title[:40], e)

    logger.warning("Relevance classify unusable for '%s' - failing closed", title[:40])
    return {"relevant": False, "entry_level": False, "reason": "classify failed"}
