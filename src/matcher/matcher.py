# src/matcher/matcher.py
"""
Main matcher for JOBfitAI.

Orchestrates all section scorers and computes a final
weighted overall score.

Flow:
    1. Run all 7 section scorers independently
    2. Apply weights from config
    3. Return structured results dict

Output format:
    {
        "overall_score":    74.5,
        "label":            "Good Match 🟡",
        "section_scores": {
            "required_skills":  88.0,
            "preferred_skills": 60.0,
            "responsibilities": 72.0,
            "experience":       65.0,
            "education":        80.0,
            "languages":        100.0,
            "certifications":   60.0,
        },
        "matched_required":  ["python", "git"],
        "missing_required":  ["docker", "pydantic-ai"],
        "matched_preferred": ["sql"],
        "missing_preferred": ["kubernetes"],
    }
"""

from src.matcher.scores import (
    score_required_skills,
    score_preferred_skills,
    score_responsibilities,
    score_experience,
    score_education,
    score_languages,
    score_certifications,
)
from src.matcher.utils import get_score_label
from src.utils.config  import WEIGHTS
from src.utils.logger  import get_logger

logger = get_logger(__name__)


def match(resume: dict, jd: dict) -> dict:
    """
    Run all section scorers and compute weighted overall score.

    Args:
        resume (dict): Extracted resume data
        jd     (dict): Extracted JD data

    Returns:
        dict: Full match results including overall score,
              label, section scores, and skill details.
              Returns empty dict if inputs are invalid.
    """
    # --- Validate inputs ---
    if not resume or not jd:
        logger.error("Invalid inputs — resume or JD is empty")
        return {}

    logger.debug("Starting match scoring")

    # --- Run all scorers (per-section detail at DEBUG) ---
    req_score, matched_required, missing_required = score_required_skills(resume, jd)
    logger.debug("Required skills   : %.1f", req_score)

    pref_score, matched_preferred, missing_preferred = score_preferred_skills(resume, jd)
    logger.debug("Preferred skills  : %.1f", pref_score)

    resp_score = score_responsibilities(resume, jd)
    logger.debug("Responsibilities  : %.1f", resp_score)

    exp_score = score_experience(resume, jd)
    logger.debug("Experience        : %.1f", exp_score)

    edu_score = score_education(resume, jd)
    logger.debug("Education         : %.1f", edu_score)

    lang_score = score_languages(resume, jd)
    logger.debug("Languages         : %.1f", lang_score)

    cert_score = score_certifications(resume, jd)
    logger.debug("Certifications    : %.1f", cert_score)

    # --- Build section scores dict ---
    section_scores = {
        "required_skills":  req_score,
        "preferred_skills": pref_score,
        "responsibilities": resp_score,
        "experience":       exp_score,
        "education":        edu_score,
        "languages":        lang_score,
        "certifications":   cert_score,
    }

    # --- Compute weighted overall score ---
    overall_score = round(
        sum(
            section_scores[section] * WEIGHTS.get(section, 0)
            for section in section_scores
        ),
        1
    )

    # Clamp to 0-100
    overall_score = max(0.0, min(100.0, overall_score))

    label = get_score_label(overall_score)

    role = (jd.get("job") or {}).get("title") or "role"
    logger.info(
        "Scored %.0f%% %s · %s  (skills %.0f · resp %.0f · exp %.0f · edu %.0f · lang %.0f)",
        overall_score, label, role[:40],
        req_score, resp_score, exp_score, edu_score, lang_score
    )

    # --- Build results ---
    results = {
        "overall_score":    overall_score,
        "label":            label,
        "section_scores":   section_scores,
        "matched_required":  matched_required,
        "missing_required":  missing_required,
        "matched_preferred": matched_preferred,
        "missing_preferred": missing_preferred,
    }

    return results
