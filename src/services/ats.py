# src/services/ats.py
"""
ATS Maker service.

Standalone pipeline - no dependency on the Analyzer having run first.
Takes raw resume text + resume JSON + JD JSON and produces:
  - exact keyword coverage before and after optimisation
  - section heading flags (standard ATS-expected headings)
  - formatting flags (patterns ATS parsers commonly fail on)
  - rewritten bullets with exact JD keywords injected

ATS systems do string matching, not semantic matching, so semantic
similarity from the matcher is not enough - the exact term must appear.
"""

import json
import re
from collections import defaultdict

from src.utils.router import call_llm
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

    # Email and phone present check (common ATS rejection reason)
    if not re.search(r"[\w.+-]+@[\w-]+\.\w+", resume_text):
        flags.append(
            "No email address detected in the extracted text - ensure your email is in plain text, not inside a header image or text box."
        )

    return flags


def inject_keywords(
    resume_json: dict, jd_json: dict, missing_exact: list[str]
) -> list[dict]:
    """
    Rewrite resume experience bullets to embed missing exact JD keywords.

    Only processes experience_entries - that is where ATS keyword density
    matters most. Education and certs are left as-is.

    Returns a list of {role, company, items: [{before, after, changed}]}.
    Empty list when there are no bullets or no missing keywords.
    """
    if not missing_exact:
        logger.info("inject_keywords: no missing exact keywords - skipping LLM call")
        return []

    experience = resume_json.get("experience_entries", [])[:3]
    if not experience:
        logger.info("inject_keywords: no experience entries found")
        return []

    role_title = jd_json.get("job", {}).get("title", "this role")
    keywords_str = ", ".join(missing_exact[:12])

    # Flatten bullets with role context
    flat: list[dict] = []
    for exp in experience:
        bullets = [
            b
            for b in exp.get("responsibilities", [])
            if isinstance(b, str) and len(b.strip()) > 10
        ][:5]
        for b in bullets:
            flat.append(
                {
                    "id": f"i{len(flat)}",
                    "role": exp.get("title", ""),
                    "company": exp.get("company", ""),
                    "text": b,
                }
            )

    if not flat:
        logger.info("inject_keywords: no bullet text found in experience entries")
        return []

    lines = "\n".join(f'- id:{item["id"]} bullet:"{item["text"]}"' for item in flat)

    prompt = f"""You are optimising a resume for ATS (Applicant Tracking System) keyword matching.

ROLE: {role_title}
MISSING EXACT KEYWORDS (these strings must appear verbatim to pass ATS filters): {keywords_str}

For each bullet, rewrite to naturally embed as many of the missing keywords as possible.
Rules:
- Use the EXACT keyword spelling from the list - ATS does literal string matching
- Only inject a keyword if it is genuinely relevant to what the bullet describes
- Keep each bullet under 25 words
- Stay grounded in what the candidate actually did - do not invent experience
- Plain hyphens only, no em-dashes
- If no listed keywords are relevant to a bullet, return it unchanged

Bullets:
{lines}

Return ONLY a valid JSON array, one object per bullet:
[{{"id": "...", "bullet": "..."}}]"""

    logger.info(
        "inject_keywords: sending %d bullets for keyword injection (role=%s)",
        len(flat),
        role_title,
    )
    _res = call_llm(prompt)
    response = _res.text if (_res and _res.text) else None

    if not response:
        logger.warning("inject_keywords: LLM returned no response")
        return []

    arr = re.search(r"\[[\s\S]*\]", response)
    if not arr:
        logger.warning("inject_keywords: no JSON array in LLM response")
        return []

    try:
        out = json.loads(arr.group())
    except Exception:
        logger.warning("inject_keywords: JSON parse error")
        return []

    bullet_map = {
        r["id"]: r.get("bullet", "").strip()
        for r in out
        if isinstance(r, dict) and "id" in r
    }

    groups: dict[tuple, list] = defaultdict(list)
    for item in flat:
        after = bullet_map.get(item["id"], "")
        before = item["text"]
        changed = bool(after) and after.lower() != before.lower()
        groups[(item["role"], item["company"])].append(
            {
                "before": before,
                "after": after if after else before,
                "changed": changed,
            }
        )

    return [
        {"role": role, "company": company, "items": items_list}
        for (role, company), items_list in groups.items()
    ]


def ats_optimise(
    resume_text: str,
    resume_json: dict,
    jd_json: dict,
) -> dict:
    """
    Full ATS optimisation pipeline.

    Steps:
      1. Exact keyword coverage before rewrite
      2. Section heading flags
      3. Formatting flags
      4. Inject missing keywords into experience bullets (LLM)
      5. Recalculate coverage using the rewritten bullets

    Returns:
      {
        coverage_before: {matched, missing, total, pct},
        coverage_after:  {matched, missing, total, pct},
        section_flags:   [{name, found, suggestion}],
        formatting_flags: [str],
        rewrites:        [{role, company, items: [{before, after, changed}]}],
      }
    """
    required = jd_json.get("required_skills", [])

    cov_before = exact_coverage(resume_text, required)
    sec_flags = section_flags(resume_text)
    fmt_flags = formatting_flags(resume_text)

    # Only ask LLM to inject keywords that are genuinely missing verbatim
    rewrites = inject_keywords(resume_json, jd_json, cov_before["missing"])

    # Approximate coverage after: check rewritten bullets against required skills
    rewritten_text = resume_text
    for group in rewrites:
        for item in group["items"]:
            if item.get("changed") and item.get("after"):
                rewritten_text += " " + item["after"]

    cov_after = exact_coverage(rewritten_text, required)

    logger.info(
        "ats_optimise: coverage %d%% -> %d%% (%d/%d keywords)",
        cov_before["pct"],
        cov_after["pct"],
        len(cov_after["matched"]),
        cov_after["total"],
    )

    return {
        "coverage_before": cov_before,
        "coverage_after": cov_after,
        "section_flags": sec_flags,
        "formatting_flags": fmt_flags,
        "rewrites": rewrites,
    }


def ats_check(resume_text: str) -> dict:
    """
    Lightweight scan - no LLM, no keyword injection.
    Returns section flags and formatting flags only.
    Used by POST /api/ats/check for a quick scan without running the full pipeline.
    """
    return {
        "section_flags": section_flags(resume_text),
        "formatting_flags": formatting_flags(resume_text),
    }
