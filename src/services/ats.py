# src/services/ats.py
"""
ATS Maker service.

Standalone pipeline - no dependency on the Analyzer having run first.
Takes raw resume text + resume JSON + JD JSON and produces a complete
ATS-optimised resume: professional summary, rewritten experience bullets
with exact JD keywords injected verbatim, matched skills section, and
clean education section.

ATS systems do string matching, not semantic matching - the exact term
must appear in the text. This is why we inject required skills verbatim
rather than relying on semantic similarity from the matcher.

Secondary outputs: keyword coverage before/after, section heading flags,
and formatting warnings for any patterns ATS parsers commonly fail on.
"""

import json
import re

from src.utils.logger import get_logger
from src.utils.router import call_llm

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


def _cert_name(cert: object) -> str:
    """Extract a string name from a cert that may be a str or a dict."""
    if isinstance(cert, str):
        return cert
    if isinstance(cert, dict):
        return cert.get("name", "") or cert.get("title", "") or str(cert)
    return str(cert)


def _llm_generate_resume(resume_json: dict, jd_json: dict) -> dict:
    """
    Call the LLM once to produce a complete ATS-optimised resume.

    Caps inputs to stay within the 6000 token budget:
    - 3 experience roles, 5 bullets each
    - 3 education entries
    - 30 skills
    - 5 certifications
    - 3 projects

    Returns {summary, experience, skills, education} or a passthrough
    of the original data if the LLM call fails.
    """
    job = jd_json.get("job", {})
    role_title = job.get("title", "the role")

    # Combine required and nice-to-have, cap at 20 for prompt size
    required = (
        jd_json.get("required_skills", []) + jd_json.get("nice_to_have_skills", [])
    )[:20]

    # Cap and shape experience input
    exp_input = []
    for exp in resume_json.get("experience_entries", [])[:3]:
        bullets = [
            b
            for b in exp.get("responsibilities", [])
            if isinstance(b, str) and len(b.strip()) > 5
        ][:5]
        exp_input.append(
            {
                "title": exp.get("title", ""),
                "company": exp.get("company", ""),
                "dates": exp.get("dates", ""),
                "bullets": bullets,
            }
        )

    # Cap and shape education input
    edu_input = []
    for edu in resume_json.get("education_entries", [])[:3]:
        edu_input.append(
            {
                "degree": edu.get("degree", "") or edu.get("field", ""),
                "institution": edu.get("institution", "") or edu.get("school", ""),
                "year": edu.get("year", "") or edu.get("graduation_year", ""),
            }
        )

    skills = resume_json.get("skills", [])[:30]
    certs = [_cert_name(c) for c in resume_json.get("certifications", [])[:5]]
    projects = [
        p.get("title", "") if isinstance(p, dict) else str(p)
        for p in resume_json.get("projects", [])[:3]
    ]
    name = resume_json.get("name", "Candidate")

    prompt = f"""You are an expert ATS resume writer. Generate a complete, ATS-optimised resume for the candidate applying to this specific role.

TARGET ROLE: {role_title}
REQUIRED SKILLS (embed these EXACT strings verbatim - ATS uses string matching, not semantic): {", ".join(required)}

CANDIDATE DATA:
Name: {name}
Experience: {json.dumps(exp_input, ensure_ascii=False)}
Education: {json.dumps(edu_input, ensure_ascii=False)}
Skills: {json.dumps(skills, ensure_ascii=False)}
Certifications: {json.dumps(certs, ensure_ascii=False)}
Projects: {json.dumps(projects, ensure_ascii=False)}

RULES:
- Professional Summary: 2-3 sentences, open with the exact target role title, mirror the JD language
- Work Experience: rewrite bullets to naturally embed as many EXACT required skills as possible
- Keep each bullet under 25 words, start with an action verb, plain hyphens only
- Skills: include ALL required skills the candidate genuinely has plus their existing skills, use exact JD terminology
- Education: copy as-is, clean format
- Stay grounded - do not invent experience the candidate does not have
- No em-dashes, no special characters

Return ONLY valid JSON (no markdown, no explanation):
{{"summary": "...", "experience": [{{"title": "...", "company": "...", "dates": "...", "bullets": ["..."]}}], "skills": ["..."], "education": [{{"degree": "...", "institution": "...", "year": "..."}}]}}"""

    logger.info(
        "generate_ats_resume: calling LLM for full resume generation (role=%s, keywords=%d)",
        role_title,
        len(required),
    )

    _res = call_llm(prompt)
    response = _res.text if (_res and _res.text) else None

    if not response:
        logger.warning(
            "generate_ats_resume: LLM returned no response - using passthrough"
        )
        return _passthrough_resume(resume_json)

    obj_match = re.search(r"\{[\s\S]*\}", response)
    if not obj_match:
        logger.warning(
            "generate_ats_resume: no JSON object in LLM response - using passthrough"
        )
        return _passthrough_resume(resume_json)

    try:
        out = json.loads(obj_match.group())
    except Exception:
        logger.warning("generate_ats_resume: JSON parse error - using passthrough")
        return _passthrough_resume(resume_json)

    return {
        "summary": out.get("summary", ""),
        "experience": out.get("experience", exp_input),
        "skills": out.get("skills", skills),
        "education": out.get("education", edu_input),
    }


def _passthrough_resume(resume_json: dict) -> dict:
    """
    Return the original resume data structured for the output without LLM.
    Used when the LLM call fails so the UI always has something to show.
    """
    exp_out = []
    for exp in resume_json.get("experience_entries", [])[:3]:
        bullets = [b for b in exp.get("responsibilities", []) if isinstance(b, str)][:5]
        exp_out.append(
            {
                "title": exp.get("title", ""),
                "company": exp.get("company", ""),
                "dates": exp.get("dates", ""),
                "bullets": bullets,
            }
        )
    edu_out = []
    for edu in resume_json.get("education_entries", [])[:3]:
        edu_out.append(
            {
                "degree": edu.get("degree", "") or edu.get("field", ""),
                "institution": edu.get("institution", "") or edu.get("school", ""),
                "year": edu.get("year", "") or edu.get("graduation_year", ""),
            }
        )
    return {
        "summary": "",
        "experience": exp_out,
        "skills": resume_json.get("skills", [])[:30],
        "education": edu_out,
    }


def _build_plain_text(resume: dict) -> str:
    """
    Build a plain-text resume from the structured LLM output.

    This is the string returned to the frontend for the "Copy full resume"
    button. Clean ATS-readable format with standard section headings.
    """
    parts: list[str] = []

    if resume.get("summary"):
        parts.append("PROFESSIONAL SUMMARY")
        parts.append("")
        parts.append(resume["summary"])
        parts.append("")

    if resume.get("experience"):
        parts.append("WORK EXPERIENCE")
        parts.append("")
        for role in resume["experience"]:
            header = " | ".join(
                p
                for p in [
                    role.get("title", ""),
                    role.get("company", ""),
                    role.get("dates", ""),
                ]
                if p
            )
            if header:
                parts.append(header)
            for bullet in role.get("bullets", []):
                if bullet:
                    parts.append(f"- {bullet}")
            parts.append("")

    if resume.get("skills"):
        parts.append("SKILLS")
        parts.append("")
        parts.append(", ".join(resume["skills"]))
        parts.append("")

    if resume.get("education"):
        parts.append("EDUCATION")
        parts.append("")
        for edu in resume["education"]:
            entry = " | ".join(
                p
                for p in [
                    edu.get("degree", ""),
                    edu.get("institution", ""),
                    edu.get("year", ""),
                ]
                if p
            )
            if entry:
                parts.append(entry)
        parts.append("")

    return "\n".join(parts).strip()


def generate_ats_resume(
    resume_text: str,
    resume_json: dict,
    jd_json: dict,
) -> dict:
    """
    Full ATS resume generation pipeline.

    Steps:
      1. Exact keyword coverage against original resume text
      2. Section heading flags
      3. Formatting flags
      4. LLM generates complete ATS-optimised resume
      5. Recalculate coverage from the generated plain text

    Returns:
      {
        resume:          {summary, experience, skills, education},
        coverage_before: {matched, missing, total, pct},
        coverage_after:  {matched, missing, total, pct},
        section_flags:   [{name, found, suggestion}],
        formatting_flags: [str],
        plain_text:      str,
      }
    """
    required = jd_json.get("required_skills", [])

    cov_before = exact_coverage(resume_text, required)
    sec_flags = section_flags(resume_text)
    fmt_flags = formatting_flags(resume_text)

    generated = _llm_generate_resume(resume_json, jd_json)
    plain_text = _build_plain_text(generated)

    # Coverage after is measured against the full generated plain text
    cov_after = exact_coverage(plain_text, required) if plain_text else cov_before

    logger.info(
        "generate_ats_resume: coverage %d%% -> %d%% (%d/%d keywords)",
        cov_before["pct"],
        cov_after["pct"],
        len(cov_after["matched"]),
        cov_after["total"],
    )

    score_before = ats_score(cov_before["pct"], sec_flags, fmt_flags)
    # After generation formatting issues are resolved, so fmt_flags = []
    score_after = ats_score(cov_after["pct"], sec_flags, [])

    return {
        "resume": generated,
        "coverage_before": cov_before,
        "coverage_after": cov_after,
        "section_flags": sec_flags,
        "formatting_flags": fmt_flags,
        "plain_text": plain_text,
        "ats_score_before": score_before,
        "ats_score_after": score_after,
    }


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
