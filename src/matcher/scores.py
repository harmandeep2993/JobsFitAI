# src/matcher/scores.py

from sentence_transformers import util

from .utils import get_all_skills
from .embedding_model import load_model

# SCORE 1 — REQUIRED SKILLS MATCH (35%)
# Most important signal
# Does candidate have what JD explicitly requires?

def score_required_skills(resume_json, jd_json):
    """
    Compare resume skills against JD required skills.
    Uses rule matching first, then embedding similarity fallback.
    """

    required = [s.lower().strip() for s in jd_json.get("required_skills", []) if s]

    if not required:
        return 0, [], []

    candidate = get_all_skills(resume_json.get("skills", []))

    matched = []
    missing = []

    model = load_model()

    candidate_vecs = None
    # Pre-encode candidate skills once
    if candidate:
        candidate_vecs = model.encode(candidate, convert_to_tensor=True)

    for r in required:

        # Rule-based match
        rule_match = any(r in c or c in r for c in candidate)

        if rule_match:
            matched.append(r)
            continue

        # Embedding fallback
        if candidate_vecs is not None:
            
            r_vec = model.encode(r, convert_to_tensor=True)

            sims = util.cos_sim(r_vec, candidate_vecs)[0]

            if sims.max() >= 0.75:
                matched.append(r)
                continue

        missing.append(r)

    score = round(len(matched) / len(required) * 100, 1)

    return score, matched, missing


# SCORE 2 — RESPONSIBILITIES SEMANTIC MATCH (20%)
# What did candidate actually do vs what JD needs?
# Sentence level comparison — most accurate semantic method

def score_responsibilities(resume_json, jd_json):
    """
    Semantic similarity between resume responsibilities
    and JD responsibilities.

    Uses sentence level comparison:
      For each JD sentence find best matching
      resume sentence — takes average of best matches.

    This is more accurate than full text comparison
    because irrelevant experience does not
    dilute the score.

    Args:
        resume_json (dict): Extracted resume data
        jd_json     (dict): Extracted JD data

    Returns:
        float: Semantic similarity score 0-100
    """
    model = load_model()

    # Collect all resume responsibility bullets
    resume_bullets = []
    for exp in resume_json.get("experience", []):
        resume_bullets.extend(
            exp.get("responsibilities", [])
        )

    jd_bullets = jd_json.get("responsibilities", [])

    # Need at least one bullet on each side
    if not resume_bullets or not jd_bullets:
        return 0

    # Filter out empty strings
    resume_bullets = [b for b in resume_bullets if b.strip()]
    jd_bullets     = [b for b in jd_bullets     if b.strip()]

    if not resume_bullets or not jd_bullets:
        return 0

    try:
        # Encode all sentences at once — efficient
        resume_vecs = model.encode(
            resume_bullets,
            convert_to_tensor=True
        )
        jd_vecs     = model.encode(
            jd_bullets,
            convert_to_tensor=True
        )

        # For each JD sentence find best matching
        # resume sentence
        # Shape: (len(resume), len(jd))
        similarity_matrix = util.cos_sim(
            resume_vecs, jd_vecs
        )

        # Best resume match per JD sentence
        best_per_jd = similarity_matrix.max(dim=0).values

        # Average of best matches
        score = float(best_per_jd.mean()) * 100

        return round(score, 1)

    except Exception as e:
        print(f"Warning: semantic scoring failed: {e}")
        return 0


# SCORE 3 — EXPERIENCE MATCH (15%)
# Does candidate have enough years?

def score_experience(resume_json, jd_json):
    """
    Compare candidate years vs required years.

    Args:
        resume_json (dict): Extracted resume data
        jd_json     (dict): Extracted JD data

    Returns:
        float: Experience match score 0-100
    """
    required  = jd_json.get("required_years_experience", 0)
    candidate = resume_json.get("total_years_experience", 0)

    # JD does not specify years — neutral score
    if not required:
        return 60

    if candidate >= required:
        return 100
    if candidate >= required * 0.75:
        return 75
    if candidate >= required * 0.50:
        return 50

    return 25


# SCORE 4 — EDUCATION MATCH (15%)
# Does candidate meet degree requirement?

def score_education(resume_json, jd_json):
    """
    Compare candidate education vs JD requirement.
    Uses degree hierarchy — higher degree always satisfies
    lower degree requirement.

    Args:
        resume_json (dict): Extracted resume data
        jd_json     (dict): Extracted JD data

    Returns:
        float: Education match score 0-100
    """

    # Degree hierarchy — higher number = higher degree
    hierarchy = {
        "phd":      4,
        "msc":      3,
        "mba":      3,
        "bsc":      2,
        "diploma":  1,
    }

    # Get required degree level
    required_raw = (
        jd_json
        .get("required_education", {})
        .get("degree", "")
        .lower()
        .strip()
    )

    required_level = 0
    for degree, level in hierarchy.items():
        if degree in required_raw:
            required_level = level
            break

    # No education requirement specified
    if not required_level:
        return 60

    # Get candidate highest degree
    candidate_level = 0
    for edu in resume_json.get("education", []):
        degree_raw = edu.get("degree", "").lower()
        for degree, level in hierarchy.items():
            if degree in degree_raw:
                candidate_level = max(candidate_level, level)
                break

    if candidate_level >= required_level:
        return 100
    if candidate_level == required_level - 1:
        return 60
    return 20


# SCORE 5 — PREFERRED SKILLS MATCH (5%)
# Nice to have — smaller weight

def score_preferred_skills(resume_json, jd_json):
    """
    Compare resume skills against JD preferred skills.
    Lower weight — nice to have not required.

    Args:
        resume_json (dict): Extracted resume data
        jd_json     (dict): Extracted JD data

    Returns:
        tuple: (score, matched, missing)
    """
    preferred = [
        s.lower().strip()
        for s in jd_json.get("preferred_skills", [])
        if s
    ]

    if not preferred:
        return 0, [], []

    candidate = get_all_skills(
        resume_json.get("skills", {})
    )

    # Also check languages
    candidate_langs = [
        l.lower()
        for l in resume_json.get("languages", [])
    ]
    candidate = candidate + candidate_langs

    matched = [s for s in preferred if s in candidate]
    missing = [s for s in preferred if s not in candidate]

    score = round(len(matched) / len(preferred) * 100, 1)

    return score, matched, missing


# SCORE 6 — LANGUAGE MATCH (5%)
# Does candidate speak required languages?

def score_languages(resume_json, jd_json):
    """
    Compare candidate languages vs required languages.

    Also checks preferred_skills for languages
    in case LLM put them there instead.

    Args:
        resume_json (dict): Extracted resume data
        jd_json     (dict): Extracted JD data

    Returns:
        float: Language match score 0-100
    """
    required = [
        l.lower().strip()
        for l in jd_json.get("required_languages", [])
        if l
    ]

    # Check preferred_skills too
    # LLM sometimes puts languages there
    language_names = [
        "english", "german", "french", "spanish",
        "mandarin", "arabic", "italian", "portuguese",
        "dutch", "russian", "japanese", "korean"
    ]

    for skill in jd_json.get("preferred_skills", []):
        if skill.lower() in language_names:
            if skill.lower() not in required:
                required.append(skill.lower())

    if not required:
        return 60    # no language requirement — neutral

    candidate = [
        l.lower()
        for l in resume_json.get("languages", [])
    ]

    matched = [l for l in required if l in candidate]
    score   = round(len(matched) / len(required) * 100, 1)

    return score