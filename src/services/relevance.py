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
- entry_level: true if suitable for 0-2 years experience (junior/graduate/trainee/working student, or no senior/lead/principal/staff/manager wording and not requiring 3+ years).

Return ONLY JSON, no prose: {{"relevant": true/false, "entry_level": true/false, "reason": "<=8 words"}}

TITLE: {title}
SNIPPET: {snippet}
JSON:"""


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
