# src/matcher/scores/certifications.py
"""
Certification scoring for JOBsFitAI.

Compares candidate certifications against JD required certifications
using semantic similarity.

Why semantic instead of exact match:
    "AWS Certified Machine Learning Specialty"
    vs "AWS ML Certification"
    → exact match fails, semantic match succeeds ✅

    "Google Professional Data Engineer"
    vs "GCP Data Engineer Certification"
    → exact match fails, semantic match succeeds ✅

Sources:
    Resume → certifications[]
    JD     → certifications[]
"""

from src.matcher.utils import _best_match_score
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Neutral score when JD has no certification requirements
NO_REQUIREMENT_SCORE = 60.0


def score_certifications(resume: dict, jd: dict) -> float:
    """
    Semantic similarity between candidate certifications
    and JD required certifications.

    For each JD certification finds the best matching
    resume certification. Final score is average of
    best matches.

    Neutral score (60) returned when:
        - JD has no certification requirements

    Zero score returned when:
        - JD has requirements but resume has no certifications

    Args:
        resume (dict): Extracted resume data
        jd     (dict): Extracted JD data

    Returns:
        float: Certification score 0-100
    """
    jd_certs = [c.strip() for c in jd.get("certifications", []) if c]
    resume_certs = [c.strip() for c in resume.get("certifications", []) if c]

    logger.info("JD certifications : %s", jd_certs)
    logger.info("Resume certifications : %s", resume_certs)

    # --- Edge case: no requirements ---
    if not jd_certs:
        logger.info(
            "No certification requirements in JD - returning neutral %.1f",
            NO_REQUIREMENT_SCORE,
        )
        return NO_REQUIREMENT_SCORE

    # --- Edge case: no certifications in resume ---
    if not resume_certs:
        logger.warning("No certifications found in resume")
        return 0.0

    # --- Semantic best match ---
    score = _best_match_score(source_list=resume_certs, target_list=jd_certs)

    logger.info("Certifications score: %s", score)
    return score
