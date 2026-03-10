# src.matcher/utils.py

from src.utils.config import THRESHOLDS


def get_all_skills(skills_dict):
    """
    Flatten categorised skills dict into one list.
    Combines all categories for comparison.
    Handles categorisation errors from LLM
    e.g. Pandas in tools instead of frameworks.

    Args:
        skills_dict (dict): Skills by category

    Returns:
        list: All skills in lowercase
    """
    all_skills = []

    for category in skills_dict.values():
        if isinstance(category, list):
            all_skills.extend([
                s.lower().strip()
                for s in category
                if s
            ])

    return list(set(all_skills))


def get_score_label(score):
    """
    Convert numeric score to human readable label.

    Args:
        score (float): Match score 0-100

    Returns:
        str: Label with emoji
    """
    if score >= THRESHOLDS["excellent"]:
        return "Excellent Match 🟢"
    if score >= THRESHOLDS["good"]:
        return "Good Match 🟡"
    if score >= THRESHOLDS["partial"]:
        return "Partial Match 🟠"
    return "Poor Match 🔴"