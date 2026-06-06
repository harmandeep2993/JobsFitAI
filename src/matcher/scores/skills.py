# src/matcher/scores/skills.py
"""
Skill scoring functions for JOBfitAI.

Covers:
    score_required_skills()  — semantic match, threshold 0.75
    score_preferred_skills() — semantic match, threshold 0.70
"""

from sentence_transformers import util

from src.matcher.embedding_model import load_model
from src.matcher.utils import get_all_skills
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Similarity thresholds
# Kept in the semantic-match range — sentence-transformer cosine scores
# for genuine synonyms typically land ~0.5-0.75, so 0.90 collapsed the
# matcher down to exact string matching only.
REQUIRED_THRESHOLD  = 0.75
PREFERRED_THRESHOLD = 0.70

# Neutral score when the JD lists no preferred skills — a missing
# requirement must not penalize the candidate (mirrors score_languages).
NO_REQUIREMENT_SCORE = 60.0


def score_required_skills(resume: dict, jd: dict) -> tuple[float, list, list]:
    """
    Semantic match between resume skills and JD required skills.

    Each required skill is compared against all candidate skills.
    A skill is considered matched if best cosine similarity >= REQUIRED_THRESHOLD.

    Args:
        resume (dict): Extracted resume data
        jd     (dict): Extracted JD data

    Returns:
        tuple: (score 0-100, matched_skills, missing_skills)
    """
    required  = [s.lower().strip() for s in jd.get("required_skills", []) if s]
    candidate = get_all_skills(resume.get("skills", []))

    logger.info("Required skills from JD: %s", required)
    logger.info("Candidate skills from resume: %s", candidate)

    # Edge cases
    if not required:
        logger.warning("No required skills found in JD")
        return 0.0, [], []

    if not candidate:
        logger.warning("No skills found in resume")
        return 0.0, [], required

    # Encode both lists
    model          = load_model()
    required_vecs  = model.encode(required,  convert_to_tensor=True)
    candidate_vecs = model.encode(candidate, convert_to_tensor=True)

    logger.debug("Encoded %d required skills", len(required))
    logger.debug("Encoded %d candidate skills", len(candidate))

    # Similarity matrix — shape: (len(required), len(candidate))
    sim_matrix = util.cos_sim(required_vecs, candidate_vecs)

    matched = []
    missing = []

    for i, skill in enumerate(required):
        best_sim = sim_matrix[i].max().item()
        logger.debug("Required skill '%s' — best similarity: %.4f", skill, best_sim)

        if skill in candidate:
            matched.append(skill)
            logger.debug("Required skill '%s' found exactly in candidate skills", skill)
            continue

        if best_sim >= REQUIRED_THRESHOLD:
            matched.append(skill)
        else:
            missing.append(skill)

    score = round(len(matched) / len(required) * 100, 1)

    logger.info("Required skills score : %s", score)
    logger.info("Matched skills        : %s", matched)
    logger.info("Missing skills        : %s", missing)

    return score, matched, missing


def score_preferred_skills(resume: dict, jd: dict) -> tuple[float, list, list]:
    """
    Semantic match between resume skills and JD preferred skills.

    Same approach as required skills but lower threshold (PREFERRED_THRESHOLD)
    since preferred skills are nice-to-have not mandatory.

    Args:
        resume (dict): Extracted resume data
        jd     (dict): Extracted JD data

    Returns:
        tuple: (score 0-100, matched_skills, missing_skills)
    """
    preferred = [s.lower().strip() for s in jd.get("preferred_skills", []) if s]
    candidate = get_all_skills(resume.get("skills", []))

    logger.info("Preferred skills from JD: %s", preferred)
    logger.info("Candidate skills from resume: %s", candidate)

    # Edge cases
    if not preferred:
        logger.info(
            "No preferred skills in JD — returning neutral %.1f",
            NO_REQUIREMENT_SCORE
        )
        return NO_REQUIREMENT_SCORE, [], []

    if not candidate:
        return 0.0, [], preferred

    # Encode both lists
    model = load_model()
    preferred_vecs = model.encode(preferred,  convert_to_tensor=True)
    candidate_vecs = model.encode(candidate,  convert_to_tensor=True)

    # Similarity matrix — shape: (len(preferred), len(candidate))
    sim_matrix = util.cos_sim(preferred_vecs, candidate_vecs)

    matched = []
    missing = []
    # add this temporarily in score_preferred_skills for debugging
    for i, skill in enumerate(preferred):
        best_sim = sim_matrix[i].max().item()
        best_idx = sim_matrix[i].argmax().item()
        best_match = candidate[best_idx]
        logger.info(
            "Preferred '%s' → best match: '%s' (%.4f)",
            skill, best_match, best_sim
        )

    for i, skill in enumerate(preferred):
        best_sim = sim_matrix[i].max().item()

        if skill in candidate:
            matched.append(skill)
            logger.info("Preferred skill '%s' found exactly in candidate skills", skill)
            continue

        logger.info("Preferred skill '%s' — best similarity: %.4f", skill, best_sim)

        if best_sim >= PREFERRED_THRESHOLD:
            matched.append(skill)
        else:
            missing.append(skill)

    score = round(len(matched) / len(preferred) * 100, 1)

    logger.info("Preferred skills score : %s", score)
    logger.info("Matched preferred      : %s", matched)
    logger.info("Missing preferred      : %s", missing)

    return score, matched, missing