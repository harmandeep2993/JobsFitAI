# src/extractor/sections.py

# SECTION EXTRACTOR
# Core idea:
#   Resumes have named sections (SKILLS, EXPERIENCE etc)
#   Instead of sending full resume to LLM
#   We find the relevant section first
#   Then send only that focused content
#
# Only section HEADER NAMES are defined here
# Not skill names, not job titles, not content
# This works for any resume structure


# Section header names across different resume formats
# These are structural labels — not content
# Adding more languages or formats here extends coverage

SECTION_HEADERS = {
    "skills": [
        "skills", "technical skills", "core skills", "competencies", "expertise", "technologies",
        "technical competencies", "key skills", "tools & technologies", "tools and technologies",
        "technical expertise", "kenntnisse", "fähigkeiten",
    ],
    "experience": [
        "experience", "work experience", "employment", "professional experience", "career history",
        "work history", "berufserfahrung", "erfahrung",
    ],
    "education": [
        "education", "academic background", "qualifications", "academic qualifications",
        "bildung", "ausbildung",
    ],
    "languages": [
        "languages", "language skills", "sprachen",
    ],
    "projects": [
        "projects", "personal projects", "key projects", "notable projects", "projekte",
    ],
    "certifications": [
        "certifications", "certificates", "professional certifications",
        "licenses", "zertifikate",
    ],
    "summary": [
        "summary", "profile", "about me", "professional summary", "objective",
        "career objective", "profil",
    ],
}

# All section names flattened into one list
# Used to detect when one section ends and the next begins
ALL_SECTION_NAMES = [
    name
    for names in SECTION_HEADERS.values()
    for name in names
]


def extract_section(text, section_key):
    """
    Find a named section in resume text and return its content.

    How it works:
      1. Split resume into lines
      2. Find line matching target section name
      3. Collect lines until next section header
      4. Return collected content

    No content hardcoding — only structural labels.
    Works for any resume format or language.

    Args:
        text        (str): Full resume text
        section_key (str): Key from SECTION_HEADERS
                           e.g. "skills", "experience"

    Returns:
        str: Section content or "" if not found
    """
    if not text or section_key not in SECTION_HEADERS:
        return ""

    target_names  = SECTION_HEADERS[section_key]
    lines         = text.split("\n")
    section_start = None
    section_end   = None

    for i, line in enumerate(lines):
        line_clean = line.strip().lower()

        if not line_clean:
            continue

        # Look for target section header
        if section_start is None:
            if any(
                line_clean == name or
                line_clean.startswith(name + ":") or
                line_clean.startswith(name + " ") or
                line_clean.endswith(" " + name)
                for name in target_names
            ):
                section_start = i
                continue

        # Once section found — look for next section header
        else:
            is_next_section = any(
                line_clean == name or
                line_clean.startswith(name + ":") or
                line_clean.startswith(name + " ")
                for name in ALL_SECTION_NAMES
                if name not in target_names
            )
            if is_next_section:
                section_end = i
                break

    if section_start is None:
        return ""

    end_idx = section_end if section_end else len(lines)
    return "\n".join(lines[section_start:end_idx]).strip()