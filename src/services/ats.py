# src/services/ats.py
"""
ATS Score service.

Checks a resume against a job description using only deterministic
string matching - no LLM required. Reports keyword coverage (the only
metric real ATS systems use), section heading presence, and formatting
warnings. No resume content is generated or modified.
"""

import re

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Standard section headings ATS parsers reliably recognise
_EXPECTED_SECTIONS = [
    {
        "name": "Work Experience",
        "keywords": [
            "experience",
            "work experience",
            "professional experience",
            "employment",
            "work history",
            "career history",
        ],
        "suggestion": "Use 'Work Experience' or 'Professional Experience' as your heading",
    },
    {
        "name": "Education",
        "keywords": [
            "education",
            "academic background",
            "qualifications",
            "academic history",
        ],
        "suggestion": "Use 'Education' as your heading",
    },
    {
        "name": "Skills",
        "keywords": [
            "skills",
            "technical skills",
            "core competencies",
            "expertise",
            "competencies",
        ],
        "suggestion": "Use 'Skills' or 'Technical Skills' as your heading",
    },
    {
        "name": "Contact Information",
        "keywords": ["email", "phone", "@", "linkedin", "contact"],
        "suggestion": "Include email, phone, and LinkedIn URL at the top of your resume",
    },
    {
        "name": "Summary / Profile",
        "keywords": [
            "summary",
            "profile",
            "objective",
            "about me",
            "professional summary",
        ],
        "suggestion": "Add a 2-3 line Professional Summary at the top below contact details",
    },
]


def ats_score(
    coverage_pct: int | None,
    sec_flags: list[dict],
    fmt_flags: list[str],
) -> dict:
    """
    ATS score = keyword coverage % only (0-100).

    Real ATS systems score on exact keyword matches. Sections and formatting
    are pass/fail gates - missing sections or bad formatting causes parsing
    failures, not point deductions. We report them separately as checklists.

    Returns score=None when no JD is provided (cannot score without keywords).
    """
    return {
        "score": coverage_pct,
        "has_jd": coverage_pct is not None,
    }


def exact_coverage(resume_text: str, required_skills: list[str]) -> dict:
    """
    Count how many required skills appear VERBATIM in the resume text.

    Case-insensitive string match - mirrors how most ATS systems score
    keyword presence. Semantic similarity does not count here.

    Returns {matched, missing, total, pct}.
    """
    text_lower = resume_text.lower()
    matched = [s for s in required_skills if s.lower() in text_lower]
    missing = [s for s in required_skills if s.lower() not in text_lower]
    total = len(required_skills)
    pct = round(len(matched) / total * 100) if total else 0
    return {"matched": matched, "missing": missing, "total": total, "pct": pct}


def section_flags(resume_text: str) -> list[dict]:
    """
    Check for ATS-expected section headings in the resume text.

    Returns a list of {name, found, suggestion} - suggestion is None when
    the section is present. Missing sections are flagged for the user to add.
    """
    text_lower = resume_text.lower()
    flags = []
    for sec in _EXPECTED_SECTIONS:
        found = any(kw in text_lower for kw in sec["keywords"])
        flags.append(
            {
                "name": sec["name"],
                "found": found,
                "suggestion": None if found else sec["suggestion"],
            }
        )
    return flags


def formatting_flags(resume_text: str) -> list[str]:
    """
    Detect patterns in the extracted plain text that commonly cause ATS
    parse failures. Works on the text layer only - cannot catch graphical
    elements (images, icons, header/footer boxes) that disappeared during
    extraction, but flags what survives.
    """
    flags = []

    # Box-drawing / table characters - signs a table was used
    if re.search(r"[│├─┼┤┌┐└┘╔╗╚╝║═]", resume_text):
        flags.append(
            "Table or box-drawing characters detected - ATS parsers often skip table content entirely. Use plain bullet points."
        )

    # Heavy decorative symbols
    if re.search(r"[★●◆▶►◄▲▼□■✓✗✔✘]", resume_text):
        flags.append(
            "Decorative symbols detected - replace with plain hyphens (-) or asterisks (*) for reliable ATS parsing."
        )

    # Non-ASCII runs that may confuse parsers
    non_ascii = re.findall(r"[^\x00-\x7F]{2,}", resume_text)
    if len(non_ascii) > 5:
        flags.append(
            "Extended Unicode characters detected - some ATS systems cannot parse them. Use plain ASCII where possible."
        )

    # All-caps overuse (common in styled resumes; some ATS miss them)
    caps_count = len(re.findall(r"\b[A-Z]{5,}\b", resume_text))
    if caps_count > 10:
        flags.append(
            "Heavy use of ALL CAPS text - some ATS systems fail to normalise it for keyword matching. Use mixed case."
        )

    # Very long lines suggest multi-column layout
    long_lines = [ln for ln in resume_text.split("\n") if len(ln) > 130]
    if len(long_lines) > 4:
        flags.append(
            "Multiple very long lines detected - likely indicates a multi-column layout. ATS parsers read left-to-right and will scramble column content."
        )

    # Email present check (common ATS rejection reason)
    if not re.search(r"[\w.+-]+@[\w-]+\.\w+", resume_text):
        flags.append(
            "No email address detected in the extracted text - ensure your email is in plain text, not inside a header image or text box."
        )

    return flags


def ats_check(resume_text: str, required_skills: list[str] | None = None) -> dict:
    """
    Lightweight scan - no LLM, no resume generation.
    Returns section flags, formatting flags, and a composite ATS score.
    When required_skills is provided (JD was pasted), keyword coverage is
    included in the score calculation.
    """
    sec_flags = section_flags(resume_text)
    fmt_flags = formatting_flags(resume_text)
    coverage = exact_coverage(resume_text, required_skills) if required_skills else None
    score = ats_score(coverage["pct"] if coverage else None, sec_flags, fmt_flags)
    return {
        "section_flags": sec_flags,
        "formatting_flags": fmt_flags,
        "coverage": coverage,
        "ats_score": score,
    }
