# services/matcher/scores/responsibilities.py
"""
Responsibilities scoring for JOBsFitAI.

Compares what the candidate has DONE against what the JD REQUIRES.

Sources:
    Resume -> all responsibility bullets from all experience entries
           + project descriptions (show additional practical work)
    JD     -> responsibilities list

Approach:
    Sentence-level best match - for each JD bullet find the best
    matching resume bullet. Average of best matches = final score.
    Irrelevant experience bullets are never selected as best match
    so they don't dilute the score.
"""

from sentence_transformers import util

from services.matcher.embedding_model import load_model
from services.matcher.scoring_utils import calibrate_similarity
from core.logger import get_logger

logger = get_logger(__name__)


def score_responsibilities(resume: dict, jd: dict) -> float | None:
    """
    Sentence-level semantic similarity between resume responsibilities
    and JD responsibilities.

    For each JD bullet finds the best matching resume bullet; the final
    score is the average of the calibrated best matches.

    Args:
        resume (dict): Extracted resume data
        jd (dict): Extracted JD data

    Returns:
        float | None: Responsibilities score 0-100, or None when the JD
        lists no responsibilities (section excluded from the overall).
    """
    # --- Collect resume bullets ---
    # From all experience entries
    resume_bullets = []

    for entry in resume.get("experience_entries", []):
        bullets = entry.get("responsibilities", [])
        resume_bullets.extend(bullets)

    # From project descriptions - shows practical work done
    for project in resume.get("projects", []):
        desc = project.get("description", "")
        if desc and desc.strip():
            resume_bullets.append(desc.strip())

    # --- Collect JD bullets ---
    jd_bullets = jd.get("responsibilities", [])

    # --- Clean both lists ---
    resume_bullets = [
        b.strip() for b in resume_bullets if isinstance(b, str) and b.strip()
    ]
    jd_bullets = [b.strip() for b in jd_bullets if isinstance(b, str) and b.strip()]

    logger.info("Resume bullets collected : %d", len(resume_bullets))
    logger.info("JD bullets collected : %d", len(jd_bullets))

    # --- Edge cases ---
    if not jd_bullets:
        logger.info("No responsibilities in JD - section excluded from overall")
        return None

    if not resume_bullets:
        logger.warning("No responsibility bullets found in resume")
        return 0.0

    # --- Encode ---
    model = load_model()
    resume_vecs = model.encode(resume_bullets, convert_to_tensor=True)
    jd_vecs = model.encode(jd_bullets, convert_to_tensor=True)

    logger.debug("Encoded %d resume bullets", len(resume_bullets))
    logger.debug("Encoded %d JD bullets", len(jd_bullets))

    # --- Similarity matrix ---
    # Shape: (len(jd_bullets), len(resume_bullets))
    # Row i = similarities between JD bullet i and all resume bullets
    sim_matrix = util.cos_sim(jd_vecs, resume_vecs)

    # --- Best resume match per JD bullet, calibrated to 0-100 ---
    # Raw cosines cluster around 0.6-0.8 even for near-perfect bullet pairs,
    # so calibrate_similarity maps them onto the full score range instead of
    # structurally capping this section at ~75.
    best_per_jd_bullet = sim_matrix.max(dim=1).values
    calibrated = [calibrate_similarity(float(v)) for v in best_per_jd_bullet]

    logger.debug("Calibrated match per JD bullet: %s", calibrated)

    score = round(sum(calibrated) / len(calibrated), 1)

    logger.info("Responsibilities score: %s", score)
    return score
