# src/extractor/ssummary.py
# Generates a concise candidate summary using LLM
# Called after scoring — uses score data for accurate narrative

import json
from src.utils.router import call_llm


def generate_summary(resume_json, jd_json, results):
    """
    Generate a concise candidate summary using LLM.
    Called after scoring so narrative includes score data.

    Args:
        resume_json (dict): Extracted resume data
        jd_json     (dict): Extracted JD data
        results     (dict): get_match_score() output

    Returns:
        str: 3-4 sentence summary or fallback text
    """
    # Build focused context — no raw text, only structured data
    context = {
        "score":            results.get("final_score", 0),
        "label":            results.get("label", ""),
        "matched_skills":   results.get("matched_required", []),
        "missing_skills" :  results.get("missing_required", []),
        "matched_pref" :    results.get("matched_preferred", []),
        "missing_pref":     results.get("missing_preferred", []),
        "candidate_years":  results.get("candidate_years", 0),
        "required_years":   results.get("required_years", 0),
        "breakdown": {
            "required_skills":  results.get("scores", {}).get("required_skills", 0),
            "responsibilities": results.get("scores", {}).get("responsibilities", 0),
            "experience":       results.get("scores", {}).get("experience", 0),
            "education":        results.get("scores", {}).get("education", 0),
        },
        "candidate": {
            "title": resume_json.get("current_title", ""),
            "years": resume_json.get("total_years_experience", 0),
            "education": [
                f"{e.get('degree','')} {e.get('field','')}"
                for e in resume_json.get("education", [])
            ],
            "languages": resume_json.get("languages", []),
            "skills":    _flatten_skills(resume_json.get("skills", {})),
        },
        "role": {
            "title":           jd_json.get("job_title", "this role"),
            "required_skills": jd_json.get("required_skills", []),
            "required_years":  jd_json.get("required_years_experience", 0),
            "required_edu":    jd_json.get("required_education", {}),
        },
    }

    prompt = f"""You are a career advisor. Write a concise professional summary evaluating this candidate against the job.

CANDIDATE VS JOB DATA:
{json.dumps(context, indent=2)}

RULES:
- Write exactly 3-5 sentences
- Mention the match score and label in first sentence
- Mention 1-2 key strengths in second sentence
- Mention 1-2 key gaps or concerns in third sentence
- Give a clear recommendation in final sentence
- Be specific — use actual skill names, years, scores from the data
- Do NOT invent information not present in the data
- Write in third person — refer to candidate as "The candidate"
- Return ONLY the paragraph — no headers, no bullet points, no extra text

EXAMPLE STYLE:
The candidate achieves a 73% Good Match for this Data Engineer role. Strong Python and SQL skills directly address the core technical requirements, and 3 years of relevant experience demonstrates practical capability. However, missing Spark and Kafka experience represents a notable gap for this pipeline-heavy role, and the responsibilities alignment score of 34% suggests CV language needs tailoring. Overall a strong candidate worth pursuing — addressing the Spark gap through a short course would make this a near-perfect match.

SUMMARY:"""

    response = call_llm(prompt)

    if response and len(response.strip()) > 50:
        return response.strip()

    # Fallback — rule based if LLM fails
    return _fallback_summary(context)


def _flatten_skills(skills_dict):
    """Flatten skills dict into a single list."""
    all_skills = []
    for category_skills in skills_dict.values():
        if isinstance(category_skills, list):
            all_skills.extend(category_skills)
    return all_skills[:15]  # cap to avoid token waste


def _fallback_summary(ctx):
    """
    Rule-based fallback summary if LLM call fails.

    Args:
        ctx (dict): Structured context

    Returns:
        str: Plain text summary
    """
    score    = ctx["score"]
    label    = ctx["label"]
    matched  = ctx["matched_skills"]
    missing  = ctx["missing_skills"]
    c_yrs    = ctx["candidate_years"]
    r_yrs    = ctx["required_years"]
    title    = ctx["candidate"]["title"]

    strengths = ", ".join(matched[:3]) if matched else "relevant skills"
    gaps      = ", ".join(missing[:3]) if missing else "none identified"
    exp_note  = (
        f"meets the {r_yrs} year experience requirement"
        if r_yrs and c_yrs >= r_yrs
        else f"has {c_yrs} years vs {r_yrs} required"
        if r_yrs
        else f"brings {c_yrs} years of experience"
    )

    return (
        f"The candidate achieves a {score}% {label} for this role. "
        f"Key strengths include {strengths}, and the candidate {exp_note}. "
        f"{'Notable gaps include: ' + gaps + '.' if missing else 'No critical skill gaps identified.'} "
        f"{'Consider applying with a tailored CV.' if score >= 60 else 'Significant upskilling recommended before applying.'}"
    )