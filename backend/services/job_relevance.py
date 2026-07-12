# services/job_relevance.py
"""
LLM relevance gate for the Job Matches funnel.

Classifies jobs by title only - snippets are unreliable (BA posts metadata,
Adzuna posts company intros in the first N chars). Relevance is judged
against the user's own target titles, so the gate works for any profession;
seniority (Senior/Lead in title) is judged the same way for everyone.
Batch size 30 titles per LLM call keeps cost low.
"""

import re

from core.logger import get_logger
from services.llm.caller import call_llm, parse_json_response

logger = get_logger(__name__)

# Deterministic seniority fallback. The LLM is the primary classifier; this
# regex decides entry_level only when the LLM failed or skipped a title, and
# acts as a safety net when an explicit seniority word contradicts the LLM
# verdict. Covers German compounds like Teamleiter/Abteilungsleiterin.
_SENIORITY_RE = re.compile(
    r"\b(senior|sr\.?|lead|principal|staff|head|director|manager|architect)\b"
    r"|\w*leiter(in)?\b",
    re.IGNORECASE,
)


def title_is_senior(title: str) -> bool:
    """True when the job title carries an explicit seniority marker."""
    return bool(_SENIORITY_RE.search(title or ""))


# Fallback role description when a user has no target titles configured.
_DEFAULT_TARGET_DESC = "AI, ML, Data Science, or Data Analytics"

_PROMPT = """Screen a job title for a candidate targeting these roles: {targets}.

relevant=true: the job is one of the target roles or a close variant of them (same profession, related specialisation). relevant=false: a different profession or an unrelated department.
entry_level=true ONLY for roles a candidate with 0-2 years of experience can realistically get: junior, graduate, trainee, intern, working student (Werkstudent), apprentice (Azubi), entry level, associate, or a plain title with no seniority signal.
entry_level=false for senior/sr/lead/principal/staff/head/director/manager/architect/Teamleiter or any title implying 3+ years of experience.

Return ONLY JSON: {{"relevant": true/false, "entry_level": true/false, "reason": "<=8 words"}}

TITLE: {title}
JSON:"""


_BATCH_PROMPT = """Screen job titles for a candidate targeting these roles: {targets}.

relevant=true: the job is one of the target roles or a close variant of them (same profession, related specialisation). relevant=false: a different profession or an unrelated department.
entry_level=true ONLY for roles a candidate with 0-2 years of experience can realistically get: junior, graduate, trainee, intern, working student (Werkstudent), apprentice (Azubi), entry level, associate, or a plain title with no seniority signal.
entry_level=false for senior/sr/lead/principal/staff/head/director/manager/architect/Teamleiter or any title implying 3+ years of experience.

Return ONLY a JSON array: [{{"n":1,"relevant":true,"entry_level":true}}, ...]

TITLES ({count}):
{jobs}

JSON:"""


def _targets_desc(titles: list | None) -> str:
    """Human-readable target-role list for the prompts, with a safe fallback."""
    cleaned = [t.strip() for t in (titles or []) if t and t.strip()]
    return ", ".join(cleaned[:15]) if cleaned else _DEFAULT_TARGET_DESC


_BATCH_SIZE = 30


def _classify_chunk(chunk: list, targets: str) -> dict:
    lines = []
    for n, j in enumerate(chunk, 1):
        lines.append(f"{n}. {j.title}")
    prompt = _BATCH_PROMPT.format(
        targets=targets, count=len(chunk), jobs="\n".join(lines)
    )

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
        # LLM responded but may have skipped some jobs - for those, keep the
        # job (relevance unknown) and fall back to the keyword seniority check.
        for j in chunk:
            out.setdefault(
                j.id, {"relevant": True, "entry_level": not title_is_senior(j.title)}
            )
    else:
        # LLM call crashed entirely - fail closed so junk doesn't flood the scorer.
        logger.warning(
            "LLM classify failed for entire batch of %d - defaulting all to relevant=False",
            len(chunk),
        )
        for j in chunk:
            out.setdefault(j.id, {"relevant": False, "entry_level": False})

    # Safety net: an explicit seniority word in the title always wins, even
    # when the LLM verdict says otherwise.
    for j in chunk:
        if title_is_senior(j.title):
            out[j.id]["entry_level"] = False
    return out


def classify_batch(jobs: list, titles: list | None = None) -> dict:
    """
    Classify many jobs with few LLM calls (chunks of _BATCH_SIZE).

    Args:
        jobs: Jobs to classify.
        titles: The user's target role titles - relevance is judged against
            these, so the gate works for any profession, not just AI/ML.

    Returns {job_id: {"relevant": bool, "entry_level": bool}}.
    """
    targets = _targets_desc(titles)
    verdicts: dict = {}
    for i in range(0, len(jobs), _BATCH_SIZE):
        verdicts.update(_classify_chunk(jobs[i : i + _BATCH_SIZE], targets))
    logger.info(
        "Classified %d jobs in %d batch call(s)",
        len(jobs),
        (len(jobs) + _BATCH_SIZE - 1) // _BATCH_SIZE,
    )
    return verdicts


def classify(title: str, snippet: str = "", titles: list | None = None) -> dict:
    """
    Return {"relevant": bool, "entry_level": bool, "reason": str}.

    On any failure, fails OPEN (relevant=True, entry_level=True) so a flaky
    LLM call doesn't silently drop a job - the scorer still runs.
    """
    prompt = _PROMPT.format(targets=_targets_desc(titles), title=title or "")
    try:
        _r = call_llm(prompt)
        data = parse_json_response(_r.text) if (_r and _r.text) else None
        if isinstance(data, dict) and "relevant" in data:
            return {
                "relevant": bool(data.get("relevant")),
                "entry_level": bool(data.get("entry_level"))
                and not title_is_senior(title),
                "reason": str(data.get("reason", ""))[:80],
            }
    except Exception as e:
        logger.error("Relevance classify failed for '%s': %s", title[:40], e)

    logger.warning("Relevance classify unusable for '%s' - failing closed", title[:40])
    return {"relevant": False, "entry_level": False, "reason": "classify failed"}
