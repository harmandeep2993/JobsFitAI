# src/matcher/utils.py

from src.utils.config import THRESHOLDS


def get_all_skills(skills):
    """
    Normalize and deduplicate skill list.

    Args:
        skills (list): Skills extracted from resume

    Returns:
        list: Cleaned skill list
    """

    if not skills:
        return []

    cleaned = []

    for skill in skills:
        if isinstance(skill, str):
            s = skill.lower().strip()
            if s:
                cleaned.append(s)

    # remove duplicates while preserving order
    return list(dict.fromkeys(cleaned))


def get_score_label(score):
    """
    Convert numeric score to human readable label.

    Args:
        score (float): Match score 0–100

    Returns:
        str
    """

    if score >= THRESHOLDS["excellent"]:
        return "Excellent Match 🟢"

    if score >= THRESHOLDS["good"]:
        return "Good Match 🟡"

    if score >= THRESHOLDS["partial"]:
        return "Partial Match 🟠"

    return "Poor Match 🔴"