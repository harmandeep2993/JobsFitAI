# services/matcher/scoring_utils.py
"""
Matcher utility functions.
Shared helpers for scoring, labeling, and section text preparation.
"""

from sentence_transformers import util
from core.config import THRESHOLDS
from core.logger import get_logger
from services.matcher.embedding_model import load_model

logger = get_logger(__name__)


def get_all_skills(skills: list) -> list:
    """
    Normalize and deduplicate a skill list.

    Args:
        skills (list): Raw skills list

    Returns:
        list: Lowercased, stripped, deduplicated skills
    """
    if not skills:
        return []

    cleaned = []
    for skill in skills:
        if isinstance(skill, str):
            s = skill.lower().strip()
            if s:
                cleaned.append(s)

    # Preserve insertion order while deduplicating
    return list(dict.fromkeys(cleaned))


def get_score_label(score: float) -> str:
    """
    Convert numeric score to human readable label.

    Args:
        score (float): Match score 0-100

    Returns:
        str: Label with emoji indicator
    """
    if score >= THRESHOLDS["excellent"]:
        return "Excellent Match 🟢"

    if score >= THRESHOLDS["good"]:
        return "Good Match 🟡"

    if score >= THRESHOLDS["partial"]:
        return "Partial Match 🟠"

    return "Poor Match 🔴"


def get_resume_sections(resume: dict) -> dict:
    """
    Convert extracted resume dict into embeddable text strings per section.
    Each section is joined into a single string for embedding.

    Args:
        resume (dict): Extracted resume data

    Returns:
        dict: Section name -> text string mapping
    """
    # Skills - flat list joined
    skills = " ".join(get_all_skills(resume.get("skills", [])))

    # Experience - all responsibilities across all entries joined
    experience_parts = []
    for entry in resume.get("experience_entries", []):
        experience_parts.extend(entry.get("responsibilities", []))
    experience = " ".join(experience_parts)

    # Projects - title + description combined
    project_parts = []
    for project in resume.get("projects", []):
        title = project.get("title", "")
        desc = project.get("description", "")
        techs = " ".join(project.get("technologies", []))
        project_parts.append(f"{title} {desc} {techs}")
    projects = " ".join(project_parts)

    # Education - degree + field + institution
    education_parts = []
    for edu in resume.get("education", []):
        education_parts.append(
            f"{edu.get('degree', '')} {edu.get('field', '')} {edu.get('institution', '')}"
        )
    education = " ".join(education_parts)

    # Languages + certifications
    languages = " ".join(resume.get("languages", []))
    certifications = " ".join(resume.get("certifications", []))

    return {
        "skills": skills.strip(),
        "experience": experience.strip(),
        "projects": projects.strip(),
        "education": education.strip(),
        "languages": languages.strip(),
        "certifications": certifications.strip(),
    }


def get_jd_sections(jd: dict) -> dict:
    """
    Convert extracted JD dict into embeddable text strings per section.
    Each section is joined into a single string for embedding.

    Args:
        jd (dict): Extracted JD data

    Returns:
        dict: Section name -> text string mapping
    """
    # Required + preferred skills combined for skills section
    required = " ".join(jd.get("required_skills", []))
    preferred = " ".join(jd.get("preferred_skills", []))
    skills = f"{required} {preferred}".strip()

    # Responsibilities
    experience = " ".join(jd.get("responsibilities", []))

    # Experience + education requirements as projects proxy
    projects = " ".join(jd.get("experience_requirements", []))

    # Education requirements
    education = " ".join(jd.get("education_requirements", []))

    # Languages + certifications
    languages = " ".join(jd.get("languages", []))
    certifications = " ".join(jd.get("certifications", []))

    return {
        "skills": skills.strip(),
        "experience": experience.strip(),
        "projects": projects.strip(),
        "education": education.strip(),
        "languages": languages.strip(),
        "certifications": certifications.strip(),
    }


# Calibration band for raw cosine similarities. Sentence-transformer cosines
# for genuinely equivalent sentences cluster around 0.6-0.8, never near 1.0,
# so using raw cosine x 100 as a score structurally caps sections at ~75 and
# reads honest matches as mediocre. Similarities are mapped linearly:
# <= CALIBRATION_LOW -> 0 (noise), >= CALIBRATION_HIGH -> 100 (full match).
CALIBRATION_LOW = 0.35
CALIBRATION_HIGH = 0.75


def calibrate_similarity(sim: float) -> float:
    """Map a raw cosine similarity onto a 0-100 score via the calibration band."""
    if sim <= CALIBRATION_LOW:
        return 0.0
    if sim >= CALIBRATION_HIGH:
        return 100.0
    return round(
        (sim - CALIBRATION_LOW) / (CALIBRATION_HIGH - CALIBRATION_LOW) * 100, 1
    )


def _cosine_score(text_a: str, text_b: str) -> float:
    """
    Calibrated cosine similarity between two text strings. Returns 0-100.

    Args:
        text_a (str): First text
        text_b (str): Second text

    Returns:
        float: Calibrated similarity score 0-100
    """
    if not text_a or not text_b:
        return 0.0

    model = load_model()
    vecs = model.encode([text_a, text_b], convert_to_tensor=True)
    sim = util.cos_sim(vecs[0], vecs[1]).item()

    return calibrate_similarity(sim)


def _best_match_score(source_list: list, target_list: list) -> float:
    """
    For each target item find the best matching source item.
    Returns the average of calibrated best matches - 0-100.

    Args:
        source_list (list): Candidate items (resume)
        target_list (list): Required items (JD)

    Returns:
        float: Average calibrated best-match score 0-100
    """
    if not source_list or not target_list:
        return 0.0

    model = load_model()
    source_vecs = model.encode(source_list, convert_to_tensor=True)
    target_vecs = model.encode(target_list, convert_to_tensor=True)

    sim_matrix = util.cos_sim(target_vecs, source_vecs)
    best_per_target = sim_matrix.max(dim=1).values
    calibrated = [calibrate_similarity(float(v)) for v in best_per_target]

    return round(sum(calibrated) / len(calibrated), 1)
