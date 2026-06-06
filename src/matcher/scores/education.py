# src/matcher/scores/education.py
"""
Education scoring for JOBfitAI.

Compares candidate education against JD education requirements
using semantic similarity.

Why semantic instead of degree hierarchy:
    Degree hierarchy is rigid and domain-blind.
    "MSc Data Analytics" matches "Bachelor Computer Science requirement"
    better semantically than a strict hierarchy check.
    Also handles non-standard degrees, bootcamps, and vocational
    qualifications across different countries naturally.

Sources:
    Resume → education[] (degree, field, institution)
    JD     → education_requirements[]
"""


from src.matcher.utils import _cosine_score
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Neutral score when JD has no education requirements
NO_REQUIREMENT_SCORE = 60.0


def _build_education_text(education_entries: list) -> str:
    """
    Build a single text string from all education entries.
    Combines degree, field, and institution for each entry.

    Args:
        education_entries (list): List of education dicts

    Returns:
        str: Combined education text for embedding
    """
    parts = []

    for edu in education_entries:
        degree      = edu.get("degree", "")
        field       = edu.get("field", "")
        institution = edu.get("institution", "")

        entry_text = " ".join(p for p in [degree, field, institution] if p).strip()

        if entry_text:
            parts.append(entry_text)
            logger.debug("Education entry: %s", entry_text)

    return " ".join(parts).strip()


def score_education(resume: dict, jd: dict) -> float:
    """
    Semantic similarity between candidate education
    and JD education requirements.

    Combines all education entries into a single text block
    and compares against all JD education requirements combined.

    Neutral score (60) returned when:
        - JD has no education requirements

    Zero score returned when:
        - JD has requirements but resume has no education entries

    Args:
        resume (dict): Extracted resume data
        jd     (dict): Extracted JD data

    Returns:
        float: Education score 0-100
    """
    education_requirements = jd.get("education_requirements", [])
    education_entries      = resume.get("education", [])

    logger.info("JD education requirements : %s", education_requirements)
    logger.info("Resume education entries  : %d", len(education_entries))

    # --- Edge case: no requirements ---
    if not education_requirements:
        logger.info(
            "No education requirements in JD — returning neutral score %.1f",
            NO_REQUIREMENT_SCORE
        )
        return NO_REQUIREMENT_SCORE

    # --- Edge case: no education in resume ---
    if not education_entries:
        logger.warning("No education entries found in resume")
        return 0.0

    # --- Build text blocks ---
    candidate_text    = _build_education_text(education_entries)
    requirements_text = " ".join(
        r for r in education_requirements if r
    ).strip()

    logger.info("Candidate education text  : %s", candidate_text)
    logger.info("Requirements text         : %s", requirements_text)

    if not candidate_text:
        logger.warning("Education entries produced no text")
        return 0.0

    # --- Semantic similarity ---
    score = _cosine_score(candidate_text, requirements_text)

    logger.info("Education score: %s", score)
    return score