# src/matcher/scores/languages.py
"""
Language scoring for JOBsFitAI.

Compares candidate languages against JD required languages, including
proficiency levels from both sides.

Scoring per required language:
    100 - language present AND candidate level >= JD required level
    100 - language present, level unspecified on either side (benefit of doubt)
     50 - language present but candidate level < JD required level (weak point)
      0 - language missing entirely

Final score = average of per-language scores.
Weak languages (score=50) are collected so callers can surface them as gaps.
"""

import langcodes

from src.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Proficiency level map
# ---------------------------------------------------------------------------

PROFICIENCY_LEVELS = {
    # C2 - mastery
    "c2": 6,
    "mastery": 6,
    "native": 6,
    "muttersprache": 6,
    "mother tongue": 6,
    "first language": 6,
    # C1 - advanced
    "c1": 5,
    "fluent": 5,
    "fließend": 5,
    "advanced": 5,
    "proficient": 5,
    "verhandlungssicher": 5,
    # B2 - upper intermediate
    "b2": 4,
    "upper intermediate": 4,
    "professional": 4,
    "business": 4,
    "working proficiency": 4,
    # B1 - intermediate
    "b1": 3,
    "intermediate": 3,
    "conversational": 3,
    "konversation": 3,
    # A2 - elementary
    "a2": 2,
    "elementary": 2,
    "basic": 2,
    "grundkenntnisse": 2,
    "beginner": 2,
    # A1 - starter
    "a1": 1,
    "anfänger": 1,
    "starter": 1,
}

# Neutral score when JD has no language requirements
NO_REQUIREMENT_SCORE = 60.0

# Partial credit when language matches but proficiency is below what JD requires
WEAK_MATCH_SCORE = 50.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_level(text: str) -> int:
    """
    Extract proficiency level from a text string.
    Checks longest keywords first to avoid partial matches.
    Returns 0 if no level found.
    """
    sorted_keywords = sorted(PROFICIENCY_LEVELS.keys(), key=len, reverse=True)
    for keyword in sorted_keywords:
        if keyword in text:
            return PROFICIENCY_LEVELS[keyword]
    return 0


def _normalize_language(text: str) -> tuple[str, int]:
    """
    Parse a raw language string into (canonical_english_name, proficiency_level).
    Level 0 means not specified.
    """
    text = text.lower().strip()
    level = _extract_level(text)

    lang_part = text.split("(")[0].split(",")[0].strip()
    for keyword in PROFICIENCY_LEVELS:
        lang_part = lang_part.replace(keyword, "").strip()

    if not lang_part:
        return text, level

    try:
        lang = langcodes.find(lang_part)
        return lang.display_name().lower(), level
    except Exception:
        logger.warning("langcodes could not normalize '%s' - using as-is", lang_part)
        return lang_part, level


def _parse_lang_entry(entry) -> tuple[str, int]:
    """
    Handle both formats:
      - dict: {"language": "german", "proficiency": "B1"}  (new schema)
      - str:  "german (B1)"                                 (legacy)

    Returns (canonical_name, proficiency_level).
    """
    if isinstance(entry, dict):
        lang_str = (entry.get("language") or "").strip()
        prof_str = (entry.get("proficiency") or "").lower().strip()
        if not lang_str:
            return "", 0
        level = _extract_level(prof_str)
        try:
            canonical = langcodes.find(lang_str.lower()).display_name().lower()
        except Exception:
            canonical = lang_str.lower()
        return canonical, level
    return _normalize_language(str(entry))


# ---------------------------------------------------------------------------
# Scorer
# ---------------------------------------------------------------------------


def score_languages(resume: dict, jd: dict) -> tuple[float, list[str], list[str]]:
    """
    Match candidate languages against JD required languages with proficiency.

    Per-language scoring:
        100 - candidate level >= JD required level (or either side unspecified)
         50 - language present but candidate level < JD required level
          0 - language missing from resume

    Returns:
        (score, matched_languages, weak_languages)
        weak_languages are languages present but below required proficiency.
    """
    raw_required = [e for e in jd.get("languages", []) if e]

    if not raw_required:
        logger.info(
            "No language requirements in JD - returning neutral %.1f",
            NO_REQUIREMENT_SCORE,
        )
        return NO_REQUIREMENT_SCORE, [], []

    required_parsed = [_parse_lang_entry(e) for e in raw_required]
    candidate_parsed = [_parse_lang_entry(e) for e in resume.get("languages", []) if e]

    # candidate lookup: language name -> proficiency level
    candidate_map: dict[str, int] = {}
    for lang, level in candidate_parsed:
        if lang:
            candidate_map[lang] = level

    logger.info("Required  : %s", required_parsed)
    logger.info("Candidate : %s", candidate_map)

    per_scores: list[float] = []
    matched: list[str] = []
    weak: list[str] = []

    for req_lang, req_level in required_parsed:
        if req_lang not in candidate_map:
            logger.warning("Required language '%s' missing from resume", req_lang)
            per_scores.append(0.0)
            continue

        cand_level = candidate_map[req_lang]

        if req_level == 0 or cand_level == 0:
            # Either side unspecified - benefit of doubt, full score
            logger.info(
                "Language '%s': level unspecified on %s - full score",
                req_lang,
                "JD" if req_level == 0 else "resume",
            )
            per_scores.append(100.0)
            matched.append(req_lang)

        elif cand_level >= req_level:
            logger.info(
                "Language '%s': candidate %d >= required %d - full score",
                req_lang,
                cand_level,
                req_level,
            )
            per_scores.append(100.0)
            matched.append(req_lang)

        else:
            logger.warning(
                "Language '%s': candidate level %d < required %d - weak match",
                req_lang,
                cand_level,
                req_level,
            )
            per_scores.append(WEAK_MATCH_SCORE)
            weak.append(
                f"{req_lang} (have: level {cand_level}, need: level {req_level})"
            )

    score = round(sum(per_scores) / len(per_scores), 1)
    logger.info("Language score: %.1f  matched=%s  weak=%s", score, matched, weak)
    return score, matched, weak
