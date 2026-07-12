# services/matcher/scores/certifications.py
"""
Certification scoring for JOBsFitAI.

Compares candidate certifications against JD required certifications
using semantic similarity.

Why semantic instead of exact match:
    "AWS Certified Machine Learning Specialty"
    vs "AWS ML Certification"
    -> exact match fails, semantic match succeeds

    "Google Professional Data Engineer"
    vs "GCP Data Engineer Certification"
    -> exact match fails, semantic match succeeds

Sources:
    Resume -> certifications[]
    JD     -> certifications[]
"""

from services.matcher.scoring_utils import _best_match_score
from core.logger import get_logger

logger = get_logger(__name__)


def score_certifications(resume: dict, jd: dict) -> float | None:
    """
    Semantic similarity between candidate certifications
    and JD required certifications.

    For each JD certification finds the best matching
    resume certification. Final score is average of
    best matches.

    None returned when the JD has no certification requirements
    (section excluded from the overall score).

    Zero score returned when:
        - JD has requirements but resume has no certifications

    Args:
        resume (dict): Extracted resume data
        jd (dict): Extracted JD data

    Returns:
        float | None: Certification score 0-100, or None when not required
    """
    jd_certs = [
        c.strip() for c in jd.get("certifications", []) if c and isinstance(c, str)
    ]
    resume_certs = [
        c.strip() for c in resume.get("certifications", []) if c and isinstance(c, str)
    ]

    logger.info("JD certifications : %s", jd_certs)
    logger.info("Resume certifications : %s", resume_certs)

    # --- Edge case: no requirements ---
    if not jd_certs:
        logger.info(
            "No certification requirements in JD - section excluded from overall"
        )
        return None

    # --- Edge case: no certifications in resume ---
    if not resume_certs:
        logger.warning("No certifications found in resume")
        return 0.0

    # --- Semantic best match ---
    score = _best_match_score(source_list=resume_certs, target_list=jd_certs)

    logger.info("Certifications score: %s", score)
    return score
