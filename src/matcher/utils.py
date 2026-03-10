# src.matcher/utils.py
from src.utils.config import THRESHOLDS


def get_all_skills(skills_dict):
    """Flatten skill categories into single list."""
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
    """Convert numeric score into label."""
    if score >= THRESHOLDS["excellent"]:
        return "Excellent Match 🟢"
    if score >= THRESHOLDS["good"]:
        return "Good Match 🟡"
    if score >= THRESHOLDS["partial"]:
        return "Partial Match 🟠"
    return "Poor Match 🔴"