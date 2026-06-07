# src/matcher/scores/languages.py
"""
Language scoring for JOBfitAI.

Compares candidate languages against JD required languages.

Handles:
    - Native/variant language names (deutsch→german, français→french)
      using langcodes library — no manual mapping needed
    - Proficiency levels (CEFR: a1-c2, fluent, conversational, etc.)
    - Partial credit for language present at insufficient level
    - All world languages supported via langcodes

Scoring per required language:
    100 — language present at acceptable level (B1+) or level unspecified
     50 — language present but below B1
      0 — language missing entirely

Final score = average of per-language scores.
"""

import langcodes

from src.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Proficiency level map
# ---------------------------------------------------------------------------

PROFICIENCY_LEVELS = {
    # C2 — mastery
    "c2":                   6,
    "mastery":              6,
    "native":               6,
    "muttersprache":        6,
    "mother tongue":        6,
    "first language":       6,
    # C1 — advanced
    "c1":                   5,
    "fluent":               5,
    "fließend":             5,
    "advanced":             5,
    "proficient":           5,
    "verhandlungssicher":   5,
    # B2 — upper intermediate
    "b2":                   4,
    "upper intermediate":   4,
    "professional":         4,
    "business":             4,
    "working proficiency":  4,
    # B1 — intermediate
    "b1":                   3,
    "intermediate":         3,
    "conversational":       3,
    "konversation":         3,
    "learning b2":          3,
    # A2 — elementary
    "a2":                   2,
    "elementary":           2,
    "basic":                2,
    "grundkenntnisse":      2,
    "beginner":             2,
    # A1 — starter
    "a1":                   1,
    "anfänger":             1,
    "starter":              1,
}

# Minimum proficiency level considered acceptable — B1 / conversational
MIN_ACCEPTABLE_LEVEL = 3

# Neutral score when JD has no language requirements
NO_REQUIREMENT_SCORE = 60.0

# Partial credit for language present but below minimum level
PARTIAL_CREDIT_SCORE = 50.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_level(text: str) -> int:
    """
    Extract proficiency level from a language string.
    Checks longest keywords first to avoid partial matches.

    Args:
        text (str): Raw language string (already lowercased)

    Returns:
        int: Proficiency level 0-6. 0 means not specified.
    """
    sorted_keywords = sorted(
        PROFICIENCY_LEVELS.keys(),
        key=len,
        reverse=True
    )

    for keyword in sorted_keywords:
        if keyword in text:
            return PROFICIENCY_LEVELS[keyword]

    return 0


def _normalize_language(text: str) -> tuple[str, int]:
    """
    Parse a raw language string into canonical English name
    and numeric proficiency level.

    Uses langcodes library to normalize language names —
    handles native names, ISO codes, and English names
    for all world languages automatically.

    Examples:
        "german (c1)"              → ("german", 5)
        "english (professional)"   → ("english", 4)
        "français (courant)"       → ("french", 3)
        "deutsch (b2)"             → ("german", 4)
        "conversational german"    → ("german", 3)
        "german"                   → ("german", 0)

    Args:
        text (str): Raw language string from resume or JD

    Returns:
        tuple[str, int]: (canonical_english_name, proficiency_level)
                         level 0 means not specified
    """
    text  = text.lower().strip()
    level = _extract_level(text)

    # Extract language name — part before parenthesis or comma
    lang_part = text.split("(")[0].split(",")[0].strip()

    # Remove proficiency keywords from lang_part
    # e.g. "conversational german" → "german"
    for keyword in PROFICIENCY_LEVELS:
        lang_part = lang_part.replace(keyword, "").strip()

    if not lang_part:
        logger.warning("Could not extract language name from: '%s'", text)
        return text, level

    # Normalize using langcodes
    try:
        lang      = langcodes.find(lang_part)
        canonical = lang.display_name().lower()
        logger.debug(
            "Normalized '%s' → '%s' (level %d)",
            text, canonical, level
        )
        return canonical, level

    except Exception:
        logger.warning(
            "langcodes could not normalize '%s' — using as-is",
            lang_part
        )
        return lang_part, level


# ---------------------------------------------------------------------------
# Scorer
# ---------------------------------------------------------------------------

def score_languages(resume: dict, jd: dict) -> float:
    """
    Match candidate languages against JD required languages.

    Per-language scoring:
        100 — present at B1+ or level unspecified (benefit of doubt)
         50 — present but below B1
          0 — missing entirely

    Final score = average of per-language scores.

    Args:
        resume (dict): Extracted resume data
        jd     (dict): Extracted JD data

    Returns:
        float: Language score 0-100
    """
    required_raw = [l for l in jd.get("languages", []) if l]

    # --- Edge case: no language requirements ---
    if not required_raw:
        logger.info(
            "No language requirements in JD — returning neutral %.1f",
            NO_REQUIREMENT_SCORE
        )
        return NO_REQUIREMENT_SCORE

    # --- Parse required and candidate languages ---
    required_parsed  = [_normalize_language(l) for l in required_raw]
    candidate_parsed = [
        _normalize_language(l)
        for l in resume.get("languages", []) if l
    ]

    # Candidate lookup — language name → proficiency level
    candidate_map = {lang: level for lang, level in candidate_parsed}

    logger.info("Required languages  : %s", required_parsed)
    logger.info("Candidate languages : %s", candidate_map)

    # --- Score each required language ---
    per_language_scores = []

    for req_lang, _ in required_parsed:

        if req_lang not in candidate_map:
            logger.warning("Required language '%s' missing from resume", req_lang)
            per_language_scores.append(0.0)
            continue

        candidate_level = candidate_map[req_lang]

        if candidate_level == 0:
            # Level unspecified — benefit of doubt
            logger.info(
                "Language '%s' present, level unspecified — full score",
                req_lang
            )
            per_language_scores.append(100.0)

        elif candidate_level >= MIN_ACCEPTABLE_LEVEL:
            # Meets minimum level requirement
            logger.info(
                "Language '%s' at level %d — meets requirement",
                req_lang, candidate_level
            )
            per_language_scores.append(100.0)

        else:
            # Present but below minimum
            logger.warning(
                "Language '%s' at level %d — below minimum %d, partial credit",
                req_lang, candidate_level, MIN_ACCEPTABLE_LEVEL
            )
            per_language_scores.append(PARTIAL_CREDIT_SCORE)

    # --- Final score ---
    score = round(
        sum(per_language_scores) / len(per_language_scores), 1
    )

    logger.info("Language score: %s", score)
    return score