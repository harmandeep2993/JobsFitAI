# services/matcher/scores/experiences.py
"""
Experience scoring for JOBsFitAI.

Two-step approach:
    Step 1 - Relevance filter: identify which experience entries
             are relevant to the JD using semantic similarity.
    Step 2 - Score: semantic similarity between relevant experience
             text and JD experience requirements.

Why two steps:
    A resume may have multiple jobs across different domains.
    Scoring all experience equally would penalize career changers
    and reward irrelevant experience. Filtering first ensures
    only relevant experience contributes to the score.

Sources:
    Resume -> experience_entries[] (title, responsibilities, duration_years)
    JD     -> experience_requirements[] + responsibilities[] (for relevance filter)
"""

from sentence_transformers import util

from services.matcher.embedding_model import load_model
from services.matcher.scoring_utils import calibrate_similarity
from core.logger import get_logger

logger = get_logger(__name__)

# Minimum similarity for an experience entry to be considered relevant
RELEVANCE_THRESHOLD = 0.30

# Score when the JD has no explicit requirements and nothing in the resume
# is even topically relevant - low but not zero (the JD gave us little to
# judge against, so we cannot rule the candidate out entirely).
NO_RELEVANT_EXPERIENCE_SCORE = 20.0


def _build_entry_text(entry: dict) -> str:
    """
    Build a single text string from an experience entry
    combining title, company, and responsibilities.

    Args:
        entry (dict): Single experience entry

    Returns:
        str: Combined text for embedding
    """
    parts = [
        entry.get("title", ""),
        entry.get("company", ""),
        " ".join(entry.get("responsibilities", [])),
    ]
    return " ".join(p for p in parts if p).strip()


def _filter_relevant_entries(experience_entries: list, jd_context: str) -> list:
    """
    Filter experience entries by semantic relevance to JD context.
    Entries with similarity >= RELEVANCE_THRESHOLD are kept.

    Args:
        experience_entries (list): All resume experience entries
        jd_context (str):  Combined JD responsibilities +
                                   experience requirements text

    Returns:
        list: Relevant experience entries only
    """
    model = load_model()
    jd_vec = model.encode(jd_context, convert_to_tensor=True)

    relevant = []

    for entry in experience_entries:
        entry_text = _build_entry_text(entry)

        if not entry_text:
            logger.debug("Skipping empty experience entry")
            continue

        entry_vec = model.encode(entry_text, convert_to_tensor=True)
        sim = util.cos_sim(jd_vec, entry_vec).item()

        logger.debug(
            "Entry '%s @ %s' - relevance similarity: %.4f",
            entry.get("title", ""),
            entry.get("company", ""),
            sim,
        )

        if sim >= RELEVANCE_THRESHOLD:
            relevant.append(entry)

    return relevant


def score_experience(resume: dict, jd: dict) -> float | None:
    """
    Score candidate experience against JD requirements.

    Step 1 - Filter relevant experience entries via semantic
             similarity against JD context.
    Step 2 - Calibrated semantic similarity between relevant experience
             text and JD experience requirements.

    Fallback when the JD has no explicit requirements:
        Relevant entries found -> None (section excluded from overall)
        No relevant entries    -> NO_RELEVANT_EXPERIENCE_SCORE

    Args:
        resume (dict): Extracted resume data
        jd (dict): Extracted JD data

    Returns:
        float | None: Experience score 0-100, or None when the JD gives
        nothing to judge against and the resume looks relevant.
    """
    experience_entries = resume.get("experience_entries", [])
    experience_requirements = jd.get("experience_requirements", [])
    jd_responsibilities = jd.get("responsibilities", [])

    logger.info("Total experience entries : %d", len(experience_entries))
    logger.info("JD experience requirements: %s", experience_requirements)

    # --- Edge case: no experience in resume ---
    if not experience_entries:
        logger.warning("No experience entries found in resume")
        return 0.0

    # --- Build JD context for relevance filter ---
    # Combine responsibilities + requirements for broader context
    jd_context = " ".join(jd_responsibilities + experience_requirements).strip()

    # --- Step 1: filter relevant entries ---
    if not jd_context:
        # No JD context available - treat all entries as relevant
        logger.warning("No JD context available - using all experience entries")
        relevant_entries = experience_entries
    else:
        relevant_entries = _filter_relevant_entries(experience_entries, jd_context)

    logger.info(
        "Relevant experience entries: %d / %d",
        len(relevant_entries),
        len(experience_entries),
    )

    for entry in relevant_entries:
        logger.debug(
            "Relevant: '%s @ %s' (%.1f years)",
            entry.get("title", ""),
            entry.get("company", ""),
            entry.get("duration_years", 0),
        )

    # --- Step 2: score against requirements ---
    if not experience_requirements:
        # JD has no explicit requirements - nothing to score against
        if relevant_entries:
            logger.info(
                "No explicit requirements - relevant experience found, section excluded"
            )
            return None
        logger.debug(
            "No explicit requirements and no relevant experience - returning %.0f",
            NO_RELEVANT_EXPERIENCE_SCORE,
        )
        return NO_RELEVANT_EXPERIENCE_SCORE

    # Build candidate text from the relevant entries. If the relevance
    # filter excluded everything, fall back to ALL entries rather than
    # zeroing the score - a candidate with real experience should still be
    # scored against the requirements, not penalized for a strict pre-filter.
    scoring_entries = relevant_entries or experience_entries
    if not relevant_entries:
        logger.info(
            "No entries passed the relevance filter - scoring all %d entries instead",
            len(experience_entries),
        )

    candidate_text = " ".join(
        [_build_entry_text(entry) for entry in scoring_entries]
    ).strip()

    if not candidate_text:
        logger.warning("No experience text available to score")
        return 0.0

    requirements_text = " ".join(experience_requirements).strip()

    # Calibrated semantic similarity - raw cosines top out around 0.8 even
    # for excellent matches, so map them onto the full 0-100 range.
    model = load_model()
    vecs = model.encode([candidate_text, requirements_text], convert_to_tensor=True)
    sim = util.cos_sim(vecs[0], vecs[1]).item()
    score = calibrate_similarity(sim)

    logger.info("Experience score: %s", score)
    return score
