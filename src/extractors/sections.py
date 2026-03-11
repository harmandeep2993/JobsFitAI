# src/extractors/sections.py

"""
SECTION EXTRACTOR

Detect resume sections (skills, experience, education, etc.)
and return only the relevant text for LLM extraction.

Only section header names are defined here.
No skills, job titles, or domain content are hardcoded.
"""

import re


SECTION_HEADERS = {
    "skills": [
        'technical competencies', 'kenntnisse', 'core competencies', 'technical stack', 'core skills', 
     'skills & tools', 'technologies', 'skills', 'professional skills', 'fähigkeiten', 'expertise', 
     'technical expertise', 'technical skills', 'competencies', 'key qualifications', 'tools and technologies', 
     'key skills', 'tools & technologies'
    ],
    
    "experience": [
        "experience", "work experience", "employment", "professional experience", "career history",
        "work history", "professional background", "employment history", "berufserfahrung", "erfahrung"
    ],

    "education": [
        "education", "academic background", "qualifications", "academic qualifications",
        "education & training", "bildung", "ausbildung"
    ],

    "languages": ["languages", "language skills", "sprachen"],

    "projects": ["projects", "personal projects", "key projects", "notable projects", "projekte"],

    "certifications": [
        "certifications", "certificates", "professional certifications", "licenses", "zertifikate"
    ],

    "summary": [
        "summary", "profile", "about me", "professional summary", "career summary",
        "objective", "career objective", "profil"
    ],
}


ALL_SECTION_NAMES = [
    name for names in SECTION_HEADERS.values() for name in names
]


def is_header(line, header_list):
    """Check if a line matches any section header."""
    for header in header_list:
        if re.search(rf"\b{re.escape(header)}\b", line) or header in line:
            return True
    return False


def extract_section(text, section_key, max_lines=80):
    """
    Extract a named section from resume text.

    Args:
        text (str): Full resume text
        section_key (str): Section name (skills, experience, etc.)
        max_lines (int): Maximum lines to return

    Returns:
        str: Section content or "" if not found
    """

    if not text or section_key not in SECTION_HEADERS:
        return ""

    target_headers = SECTION_HEADERS[section_key]
    lines = text.split("\n")

    section_start = None
    section_end = None

    for i, line in enumerate(lines):
        line_clean = line.strip().lower()

        if not line_clean:
            continue

        if section_start is None:
            if is_header(line_clean, target_headers):
                section_start = i
                continue
        else:
            if is_header(line_clean, ALL_SECTION_NAMES):
                section_end = i
                break

    if section_start is None:
        return ""

    end_index = section_end if section_end else len(lines)

    content = lines[section_start + 1:end_index]

    if len(content) > max_lines:
        content = content[:max_lines]

    return "\n".join(content).strip()