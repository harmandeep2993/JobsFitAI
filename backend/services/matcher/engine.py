# services/matcher/engine.py
"""
Main matcher for JOBsFitAI.

Orchestrates all section scorers and computes a final
weighted overall score.

Flow:
    1. Run all 7 section scorers independently
    2. Apply weights from config
    3. Return structured results dict

Output format:
    {
        "overall_score":    74.5,
        "label":            "Good Match",
        "section_scores": {
            "required_skills":  88.0,
            "preferred_skills": 55.0,
            "responsibilities": 72.0,
            "experience":       65.0,
            "education":        80.0,
            "languages":        100.0,
            "certifications":   None,   # None = JD had no data, excluded
        },
        "matched_required":  ["python", "git"],
        "partial_required":  ["tensorflow"],   # related skill, half credit
        "missing_required":  ["docker", "pydantic-ai"],
        "matched_preferred": ["sql"],
        "partial_preferred": [],
        "missing_preferred": ["kubernetes"],
    }
"""

from services.matcher.scores import (
    score_certifications,
    score_education,
    score_experience,
    score_languages,
    score_preferred_skills,
    score_required_skills,
    score_responsibilities,
)
from services.matcher.scoring_utils import get_score_label
from core.config import WEIGHTS
from core.logger import get_logger

logger = get_logger(__name__)


def match(resume: dict, jd: dict) -> dict:
    """
    Run all section scorers and compute weighted overall score.

    Args:
        resume (dict): Extracted resume data
        jd (dict): Extracted JD data

    Returns:
        dict: Full match results including overall score,
              label, section scores, and skill details.
              Returns empty dict if inputs are invalid.
    """
    # --- Validate inputs ---
    if not resume or not jd:
        logger.error("Invalid inputs - resume or JD is empty")
        return {}

    logger.debug("Starting match scoring")

    # --- Run all scorers (per-section detail at DEBUG) ---
    # Every scorer returns None when the JD gives it nothing to judge
    # against; those sections are excluded from the weighted overall.
    req_score, matched_required, partial_required, missing_required = (
        score_required_skills(resume, jd)
    )
    pref_score, matched_preferred, partial_preferred, missing_preferred = (
        score_preferred_skills(resume, jd)
    )
    resp_score = score_responsibilities(resume, jd)
    exp_score = score_experience(resume, jd)
    edu_score = score_education(resume, jd)
    lang_score, matched_languages, weak_languages = score_languages(resume, jd)
    cert_score = score_certifications(resume, jd)

    # --- Build section scores dict (clamp real scores, keep None as None) ---
    def _clamp(v: float | None) -> float | None:
        if v is None:
            return None
        return round(max(0.0, min(100.0, float(v))), 1)

    section_scores = {
        "required_skills": _clamp(req_score),
        "preferred_skills": _clamp(pref_score),
        "responsibilities": _clamp(resp_score),
        "experience": _clamp(exp_score),
        "education": _clamp(edu_score),
        "languages": _clamp(lang_score),
        "certifications": _clamp(cert_score),
    }
    logger.debug("Section scores: %s", section_scores)

    # --- Compute weighted overall score ---
    # None sections (JD had no data for them) are excluded and their weight
    # is redistributed to the remaining sections, so an absent JD section
    # never drags the overall toward a fake neutral value.
    active = {s: v for s, v in section_scores.items() if v is not None}
    active_weight_total = sum(WEIGHTS.get(s, 0) for s in active)

    if active and active_weight_total > 0:
        overall_score = round(
            sum(v * WEIGHTS.get(s, 0) / active_weight_total for s, v in active.items()),
            1,
        )
    else:
        # Degenerate JD: no scoreable sections at all
        overall_score = 0.0
        logger.warning("No scoreable sections - JD extraction produced no data")

    # Clamp to 0-100
    overall_score = max(0.0, min(100.0, overall_score))

    label = get_score_label(overall_score)

    role = (jd.get("job") or {}).get("title") or "role"
    logger.debug(
        "Scored %.0f%% %s · %s  (active sections: %s)",
        overall_score,
        label,
        role[:40],
        ", ".join(f"{s} {v:.0f}" for s, v in active.items()),
    )

    # --- Build results ---
    results = {
        "overall_score": overall_score,
        "label": label,
        "section_scores": section_scores,
        "matched_required": matched_required,
        "partial_required": partial_required,
        "missing_required": missing_required,
        "matched_preferred": matched_preferred,
        "partial_preferred": partial_preferred,
        "missing_preferred": missing_preferred,
        "matched_languages": matched_languages,
        "weak_languages": weak_languages,
    }

    return results
