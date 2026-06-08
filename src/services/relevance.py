# src/services/relevance.py
"""
LLM relevance gate for the Job Matches funnel.

A single cheap call per new job — it sees only the title and a short
snippet — decides whether the posting is a relevant AI/ML/Data role and
whether it's entry-level. Running this BEFORE the full-JD extraction means
we never spend the expensive extraction/scoring tokens on irrelevant or
senior jobs.
"""

from src.utils.router import call_llm, parse_json_response
from src.utils.logger import get_logger

logger = get_logger(__name__)

_PROMPT = """You screen job postings for an ENTRY-LEVEL candidate targeting AI / Machine Learning / Data roles (e.g. machine learning engineer, AI engineer, data scientist, NLP/LLM/GenAI engineer, MLOps, computer vision, data analyst, analytics engineer, applied scientist — including junior/graduate/trainee/working-student versions).

Decide two things from the title and snippet:
- relevant: true only if it is an AI/ML/Data role (NOT sales, marketing, finance, accounting, HR, civil/mechanical engineering, consulting, support, etc.).
- entry_level: true by DEFAULT. Set it false ONLY when the role is clearly senior — i.e. the title contains senior / sr. / lead / principal / staff / head / director / manager / architect, OR the text explicitly requires 3+ years of experience. A plain role with no seniority wording (e.g. "Data Scientist", "ML Engineer") IS entry_level=true.

Return ONLY JSON, no prose: {{"relevant": true/false, "entry_level": true/false, "reason": "<=8 words"}}

TITLE: {title}
SNIPPET: {snippet}
JSON:"""


_BATCH_PROMPT = """You screen job postings for an ENTRY-LEVEL candidate targeting AI / Machine Learning / Data roles (machine learning engineer, AI engineer, data scientist, NLP/LLM/GenAI engineer, MLOps, computer vision, data analyst, analytics engineer, applied scientist — incl. junior/graduate/trainee).

For EACH numbered job decide:
- relevant: true ONLY if it is an AI/ML/Data role (NOT sales, marketing, finance, accounting, HR, civil/mechanical engineering, consulting, support, etc.).
- entry_level: true by DEFAULT; false ONLY if clearly senior (title has senior/sr/lead/principal/staff/head/director/manager/architect, OR the text requires 3+ years).

Return ONLY a JSON array, one object per job, in order:
[{{"n":1,"relevant":true,"entry_level":true}}, ...]

JOBS ({count}):
{jobs}

JSON:"""

_BATCH_SIZE = 25


def _classify_chunk(chunk: list) -> dict:
    lines = []
    for n, j in enumerate(chunk, 1):
        snip = (j.description or "")[:200].replace("\n", " ")
        lines.append(f"{n}. TITLE: {j.title} | SNIPPET: {snip}")
    prompt = _BATCH_PROMPT.format(count=len(chunk), jobs="\n".join(lines))

    out: dict = {}
    try:
        data = parse_json_response(call_llm(prompt))
        if isinstance(data, list):
            for obj in data:
                n = obj.get("n") if isinstance(obj, dict) else None
                if isinstance(n, int) and 1 <= n <= len(chunk):
                    out[chunk[n - 1].id] = {
                        "relevant":    bool(obj.get("relevant")),
                        "entry_level": bool(obj.get("entry_level")),
                    }
    except Exception as e:
        logger.error("batch classify failed: %s", e)

    # Fail open for anything the model skipped — don't silently drop jobs.
    for j in chunk:
        out.setdefault(j.id, {"relevant": True, "entry_level": True})
    return out


def classify_batch(jobs: list) -> dict:
    """
    Classify many jobs with few LLM calls (chunks of _BATCH_SIZE).

    Returns {job_id: {"relevant": bool, "entry_level": bool}}.
    """
    verdicts: dict = {}
    for i in range(0, len(jobs), _BATCH_SIZE):
        verdicts.update(_classify_chunk(jobs[i:i + _BATCH_SIZE]))
    logger.info("Classified %d jobs in %d batch call(s)",
                len(jobs), (len(jobs) + _BATCH_SIZE - 1) // _BATCH_SIZE)
    return verdicts


def classify(title: str, snippet: str) -> dict:
    """
    Return {"relevant": bool, "entry_level": bool, "reason": str}.

    On any failure, fails OPEN (relevant=True, entry_level=True) so a flaky
    LLM call doesn't silently drop a job — the scorer still runs.
    """
    prompt = _PROMPT.format(title=title or "", snippet=(snippet or "")[:600])
    try:
        data = parse_json_response(call_llm(prompt))
        if isinstance(data, dict) and "relevant" in data:
            return {
                "relevant":    bool(data.get("relevant")),
                "entry_level": bool(data.get("entry_level")),
                "reason":      str(data.get("reason", ""))[:80],
            }
    except Exception as e:
        logger.error("Relevance classify failed for '%s': %s", title[:40], e)

    logger.warning("Relevance classify unusable for '%s' — failing open", title[:40])
    return {"relevant": True, "entry_level": True, "reason": "classify failed"}
