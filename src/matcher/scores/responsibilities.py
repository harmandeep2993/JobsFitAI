# src/matcher/scores/responsibilities.py
"""
Responsibilities scoring for JOBfitAI.

Compares what the candidate has DONE against what the JD REQUIRES.

Sources:
    Resume → all responsibility bullets from all experience entries
           + project descriptions (show additional practical work)
    JD     → responsibilities list

Approach:
    Sentence-level best match — for each JD bullet find the best
    matching resume bullet. Average of best matches = final score.
    Irrelevant experience bullets are never selected as best match
    so they don't dilute the score.
"""

from sentence_transformers import util

from src.matcher.embedding_model import load_model
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Neutral score returned when the JD lists no responsibilities —
# a missing requirement must not penalize the candidate.
NO_REQUIREMENT_SCORE = 60.0

# Minimum cosine similarity for a resume bullet to count as matching a JD
# bullet. Below this threshold the match is treated as 0 — avoids inflating
# the score when two unrelated sentences happen to share common words.
MIN_MATCH_SIM = 0.35


def score_responsibilities(resume: dict, jd: dict) -> float:
    """
    Sentence-level semantic similarity between resume responsibilities
    and JD responsibilities.

    For each JD bullet finds the best matching resume bullet.
    Final score is the average of all best matches.

    Args:
        resume (dict): Extracted resume data
        jd     (dict): Extracted JD data

    Returns:
        float: Responsibilities score 0-100
    """
    # --- Collect resume bullets ---
    # From all experience entries
    resume_bullets = []

    for entry in resume.get("experience_entries", []):
        bullets = entry.get("responsibilities", [])
        resume_bullets.extend(bullets)

    # From project descriptions — shows practical work done
    for project in resume.get("projects", []):
        desc = project.get("description", "")
        if desc and desc.strip():
            resume_bullets.append(desc.strip())

    # --- Collect JD bullets ---
    jd_bullets = jd.get("responsibilities", [])

    # --- Clean both lists ---
    resume_bullets = [b.strip() for b in resume_bullets if b.strip()]
    jd_bullets     = [b.strip() for b in jd_bullets     if b.strip()]

    logger.info("Resume bullets collected : %d", len(resume_bullets))
    logger.info("JD bullets collected     : %d", len(jd_bullets))

    # --- Edge cases ---
    if not resume_bullets:
        logger.warning("No responsibility bullets found in resume")
        return 0.0

    if not jd_bullets:
        logger.info("No responsibilities in JD — returning neutral %.1f", NO_REQUIREMENT_SCORE)
        return NO_REQUIREMENT_SCORE

    # --- Encode ---
    model          = load_model()
    resume_vecs    = model.encode(resume_bullets, convert_to_tensor=True)
    jd_vecs        = model.encode(jd_bullets,     convert_to_tensor=True)

    logger.debug("Encoded %d resume bullets", len(resume_bullets))
    logger.debug("Encoded %d JD bullets",     len(jd_bullets))

    # --- Similarity matrix ---
    # Shape: (len(jd_bullets), len(resume_bullets))
    # Row i = similarities between JD bullet i and all resume bullets
    sim_matrix = util.cos_sim(jd_vecs, resume_vecs)

    # --- Best resume match per JD bullet ---
    best_per_jd_bullet = sim_matrix.max(dim=1).values

    logger.debug("Best match per JD bullet: %s",
                 [round(v.item(), 4) for v in best_per_jd_bullet])

    # Clamp weak matches to 0 — a similarity below MIN_MATCH_SIM means no
    # real match, not a weak one. Without this, unrelated sentences sharing
    # common words inflate the score.
    best_per_jd_bullet = best_per_jd_bullet.clone()
    best_per_jd_bullet[best_per_jd_bullet < MIN_MATCH_SIM] = 0.0

    # --- Final score ---
    score = float(best_per_jd_bullet.mean()) * 100
    score = round(max(score, 0), 1)

    logger.info("Responsibilities score: %s", score)
    return score