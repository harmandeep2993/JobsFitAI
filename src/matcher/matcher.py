# src/matcher/matcher.py

from .utils import get_score_label
from src.utils.config import WEIGHTS

from .scores import (
    score_required_skills,
    score_responsibilities,
    score_experience,
    score_education,
    score_preferred_skills,
    score_languages
)

def get_match_score(resume_json, jd_json):
    """
    Calculate final weighted match score.
    Combines all 6 signals into one reliable score.

    Weights defined in config.yaml:
      required_skills:   35%
      responsibilities:  25%
      experience:        15%
      education:         15%
      preferred_skills:   5%
      languages:          5%

    Args:
        resume_json (dict): Extracted resume data
        jd_json     (dict): Extracted JD data

    Returns:
        dict: Complete match results
    """
    results = {}

    # Calculate all scores
    print("Scoring required skills...")
    req_score, matched_req, missing_req = (score_required_skills(resume_json, jd_json))

    print("Scoring responsibilities semantically...")
    resp_score = score_responsibilities(resume_json, jd_json)

    print("Scoring experience...")
    exp_score = score_experience(resume_json, jd_json)

    print("Scoring education...")
    edu_score = score_education(resume_json, jd_json)

    print("Scoring preferred skills...")
    pref_score, matched_pref, missing_pref = (score_preferred_skills(resume_json, jd_json))

    print("Scoring languages...")
    lang_score = score_languages(resume_json, jd_json)

    # Weighted final score
    final = (
        (req_score  * WEIGHTS["required_skills"])
        + (resp_score * WEIGHTS["responsibilities"])
        + (exp_score  * WEIGHTS["experience"])
        + (edu_score  * WEIGHTS["education"])
        + (pref_score * WEIGHTS["preferred_skills"])
        + (lang_score * WEIGHTS["languages"])
    )

    final_score = round(final, 1)

    return {
        # Final score
        "final_score":   final_score,
        "label": get_score_label(final_score),

        # Individual scores
        "scores": {
            "required_skills":  req_score,
            "responsibilities": resp_score,
            "experience":       exp_score,
            "education":        edu_score,
            "preferred_skills": pref_score,
            "languages":        lang_score,
        },

        # Skills breakdown
        "matched_required":  matched_req,
        "missing_required":  missing_req,
        "matched_preferred": matched_pref,
        "missing_preferred": missing_pref,

        # Context
        "candidate_years":  resume_json.get(
            "total_years_experience", 0
        ),
        "required_years":   jd_json.get(
            "required_years_experience", 0
        ),
        "candidate_langs":  resume_json.get(
            "languages", []
        ),
        "required_langs":   jd_json.get(
            "required_languages", []
        ),
    }