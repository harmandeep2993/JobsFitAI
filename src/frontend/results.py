# src/frontend/results.py
# Renders full results view into a NiceGUI container element
# Called after get_match_score() returns

from nicegui import ui

from src.utils.config import LLM_MODEL
from src.frontend.components import (
    score_col, make_prog, make_tags, safe_html
)


def get_direction(score):
    if score >= 80: return "cg", "▲ Strong match"
    if score >= 60: return "cb", "◆ Good match"
    if score >= 40: return "ca", "◆ Partial match"
    return "cr", "▼ Poor match"


PROG_LABELS = {
    "required_skills":  "Required Skills",
    "responsibilities": "Responsibilities",
    "experience":       "Experience",
    "education":        "Education",
    "preferred_skills": "Preferred Skills",
    "languages":        "Languages",
}


def render_metrics(score, matched_req, missing_req, c_yrs, r_yrs):
    sc           = score_col(score)
    d_cls, d_txt = get_direction(score)
    exp_note     = f"{c_yrs} yrs vs {r_yrs} req." if r_yrs else f"{c_yrs} yrs found"
    total_req    = len(matched_req) + len(missing_req)

    return f"""
    <div class="metrics-grid fade-in">
      <div class="m-card">
        <div class="m-lbl">Match Score</div>
        <div class="m-val" style="color:{sc};">
          {score}<span class="m-den">/100</span>
        </div>
        <div class="m-sub {d_cls}">{d_txt}</div>
      </div>
      <div class="m-card">
        <div class="m-lbl">Required Skills</div>
        <div class="m-val cg">
          {len(matched_req)}<span class="m-den">/{total_req}</span>
        </div>
        <div class="m-sub cg">matched</div>
      </div>
      <div class="m-card">
        <div class="m-lbl">Experience</div>
        <div class="m-val cb">
          {c_yrs}<span class="m-den"> yrs</span>
        </div>
        <div class="m-sub">{exp_note}</div>
      </div>
    </div>
    """



def render_summary(summary_text):
    """
    Build summary tab panel HTML.

    Args:
        summary_text (str): LLM generated summary

    Returns:
        str: Summary panel HTML
    """
    text = safe_html(summary_text) if summary_text else "Summary not available."
    return f'''<div id="jf-summary" class="jf-panel fade-in">
      <div class="summary-card">
        <div class="summary-icon">🤖</div>
        <div class="summary-text">{text}</div>
      </div>
    </div>'''


def render_breakdown(scores):
    progs = "".join(
        make_prog(PROG_LABELS[k], v)
        for k, v in scores.items()
        if k in PROG_LABELS
    )

    return f"""
    <div class="tab-row" id="jf-tab-row">
      <div class="tab-item active" onclick="jfTab(this,'jf-summary')">📋 Summary</div>
      <div class="tab-item"        onclick="jfTab(this,'jf-breakdown')">Match Breakdown</div>
      <div class="tab-item"        onclick="jfTab(this,'jf-skills')">Skills Gap</div>
      <div class="tab-item"        onclick="jfTab(this,'jf-languages')">Languages</div>
      <div class="tab-item"        onclick="jfTab(this,'jf-reco')">💡 Recommendations</div>
    </div>
    <div id="jf-breakdown" class="jf-panel" style="display:none;">{progs}</div>
    """


def render_skills_gap(matched_req, missing_req, matched_pref, missing_pref):
    sections = [
        ("Required — Matched",  matched_req,  "tg"),
        ("Required — Missing",  missing_req,  "tr"),
        ("Preferred — Matched", matched_pref, "tg"),
        ("Preferred — Missing", missing_pref, "ta"),
    ]

    blocks = "".join(
        f'<div class="gap-block">'
        f'<div class="gap-lbl">{safe_html(lbl)}</div>'
        f'<div class="tags-row">{make_tags(items, css)}</div>'
        f'</div>'
        for lbl, items, css in sections
    )

    return f'<div id="jf-skills" class="jf-panel" style="display:none;">{blocks}</div>'


def render_languages(c_langs, r_langs):
    c_str = ", ".join(c_langs) if c_langs else "—"
    r_str = ", ".join(r_langs) if r_langs else "None specified"

    return f"""
    <div id="jf-languages" class="jf-panel" style="display:none;">
      <div style="font-size:13px;color:var(--t2);margin-bottom:5px;">
        Candidate &nbsp;
        <span style="color:var(--t1);font-weight:500;">{safe_html(c_str)}</span>
      </div>
      <div style="font-size:13px;color:var(--t2);">
        Required &nbsp;&nbsp;
        <span style="color:var(--t1);font-weight:500;">{safe_html(r_str)}</span>
      </div>
    </div>
    """


def render_recommendations(score, missing_req, missing_pref, c_yrs, r_yrs,
                            c_edu, r_edu, scores):
    """
    Build recommendations panel HTML.
    Rule-based — no LLM needed.
    Backend LLM narrative will replace placeholder later.

    Args:
        score       (float): Final match score
        missing_req (list):  Missing required skills
        missing_pref(list):  Missing preferred skills
        c_yrs       (float): Candidate years experience
        r_yrs       (float): Required years experience
        c_edu       (list):  Candidate education list
        r_edu       (dict):  Required education
        scores      (dict):  Individual scores
    """
    items = []

    # Skills gap recommendations
    if missing_req:
        skills_str = ", ".join(f"<span class='tag tr'>{safe_html(s)}</span>" for s in missing_req[:6])
        items.append(f"""
        <div class="reco-card reco-high">
          <div class="reco-icon">🚨</div>
          <div class="reco-body">
            <div class="reco-title">Fill Critical Skill Gaps</div>
            <div class="reco-text">
              These required skills are missing from your profile:
              <div class="tags-row" style="margin-top:8px;">{skills_str}</div>
            </div>
          </div>
        </div>
        """)

    if missing_pref:
        pref_str = ", ".join(f"<span class='tag ta'>{safe_html(s)}</span>" for s in missing_pref[:5])
        items.append(f"""
        <div class="reco-card reco-med">
          <div class="reco-icon">💼</div>
          <div class="reco-body">
            <div class="reco-title">Build Domain Knowledge</div>
            <div class="reco-text">
              These preferred skills would strengthen your application:
              <div class="tags-row" style="margin-top:8px;">{pref_str}</div>
            </div>
          </div>
        </div>
        """)

    # Experience gap
    if r_yrs and c_yrs < r_yrs:
        gap = round(r_yrs - c_yrs, 1)
        items.append(f"""
        <div class="reco-card reco-med">
          <div class="reco-icon">⏱️</div>
          <div class="reco-body">
            <div class="reco-title">Experience Gap: {gap} Years</div>
            <div class="reco-text">
              Role requires {r_yrs} years, you have {c_yrs} years.
              Highlight project work, freelance, or bootcamp experience to bridge the gap.
            </div>
          </div>
        </div>
        """)

    # Responsibilities score low
    resp_score = scores.get("responsibilities", 100)
    if resp_score < 50:
        items.append(f"""
        <div class="reco-card reco-med">
          <div class="reco-icon">📝</div>
          <div class="reco-body">
            <div class="reco-title">Tailor Your CV Language</div>
            <div class="reco-text">
              Your responsibilities score is low ({resp_score}%).
              Rewrite your bullet points using keywords and phrases from the job description.
              Mirror the JD language — ATS systems reward this.
            </div>
          </div>
        </div>
        """)

    # Education gap
    r_deg = r_edu.get("degree", "").lower() if isinstance(r_edu, dict) else ""
    c_degrees = [e.get("degree", "").lower() for e in c_edu] if c_edu else []
    deg_hierarchy = ["phd", "msc", "bsc", "diploma"]

    if r_deg and r_deg in deg_hierarchy:
        r_level = deg_hierarchy.index(r_deg)
        c_level = min((deg_hierarchy.index(d) for d in c_degrees if d in deg_hierarchy), default=99)
        if c_level > r_level:
            items.append(f"""
            <div class="reco-card reco-low">
              <div class="reco-icon">🎓</div>
              <div class="reco-body">
                <div class="reco-title">Education Requirement</div>
                <div class="reco-text">
                  Role prefers {r_deg.upper()} level education.
                  Emphasise relevant coursework, certifications, or self-study to compensate.
                </div>
              </div>
            </div>
            """)

    # Good score — positive reinforcement
    if score >= 80:
        items.append(f"""
        <div class="reco-card reco-good">
          <div class="reco-icon">🎯</div>
          <div class="reco-body">
            <div class="reco-title">Strong Match — Apply Now</div>
            <div class="reco-text">
              Your profile is a strong match for this role.
              Customise your cover letter to highlight your top matching skills and submit with confidence.
            </div>
          </div>
        </div>
        """)
    elif score >= 60 and not missing_req:
        items.append(f"""
        <div class="reco-card reco-good">
          <div class="reco-icon">✅</div>
          <div class="reco-body">
            <div class="reco-title">Good Match — Worth Applying</div>
            <div class="reco-text">
              You meet the core requirements. Address the preferred skills gap in your cover letter
              and explain how your experience transfers.
            </div>
          </div>
        </div>
        """)

    # Placeholder for future LLM narrative
    items.append(f"""
    <div class="reco-card reco-info" style="margin-top:8px;">
      <div class="reco-icon">🤖</div>
      <div class="reco-body">
        <div class="reco-title">AI Narrative — Coming Soon</div>
        <div class="reco-text">
          Personalised LLM-generated career advice based on your full profile will appear here.
        </div>
      </div>
    </div>
    """)

    cards = "".join(items) if items else "<p style='color:var(--t3);font-size:13px;'>No recommendations — great match!</p>"

    return f'<div id="jf-reco" class="jf-panel" style="display:none;">{cards}</div>'


# Tab switching JS — injected once with results
TAB_JS = """
<script>
function jfTab(el, panelId) {
  document.querySelectorAll('#jf-tab-row .tab-item').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.jf-panel').forEach(p => p.style.display = 'none');
  el.classList.add('active');
  var panel = document.getElementById(panelId);
  if (panel) panel.style.display = 'block';
}
</script>
"""


def render_results(container, results, resume_json, jd_json):
    score        = results.get("final_score", 0)
    label        = results.get("label", "")
    scores       = results.get("scores", {})
    matched_req  = results.get("matched_required", [])
    missing_req  = results.get("missing_required", [])
    matched_pref = results.get("matched_preferred", [])
    missing_pref = results.get("missing_preferred", [])
    c_yrs        = results.get("candidate_years", 0)
    r_yrs        = results.get("required_years", 0)
    c_langs      = results.get("candidate_langs", [])
    r_langs      = results.get("required_langs", [])
    c_edu        = resume_json.get("education", [])
    r_edu        = jd_json.get("required_education", {})

    container.clear()

    with container:
        ui.html(TAB_JS)
        ui.html(render_metrics(score, matched_req, missing_req, c_yrs, r_yrs))
        ui.html(render_breakdown(scores))
        ui.html(render_skills_gap(matched_req, missing_req, matched_pref, missing_pref))
        ui.html(render_languages(c_langs, r_langs))
        ui.html(render_recommendations(
            score, missing_req, missing_pref,
            c_yrs, r_yrs, c_edu, r_edu, scores
        ))
        ui.html('<div class="divider"></div>')
        ui.html("""
        <div class="callout">
          <span>ℹ️</span>
          <span>Results generated by AI + sentence-transformers.
          Scores are probabilistic — use as a guide, not a definitive judgement.</span>
        </div>
        """)
        ui.html("""
        <div style="margin-top:24px;">
          <button class="btn-ghost" onclick="location.reload()">↩ Analyse Another</button>
        </div>
        """)
        ui.html(f'<div class="foot-note">{score}% · {label} · {LLM_MODEL} · all-MiniLM-L6-v2</div>')


def build_results_html(results, resume_json, jd_json, summary=''):
    """
    Build full results HTML string — no NiceGUI elements.
    Used when injecting results via JS innerHTML.
    """
    from src.utils.config import LLM_MODEL

    score        = results.get("final_score", 0)
    label        = results.get("label", "")
    scores       = results.get("scores", {})
    matched_req  = results.get("matched_required", [])
    missing_req  = results.get("missing_required", [])
    matched_pref = results.get("matched_preferred", [])
    missing_pref = results.get("missing_preferred", [])
    c_yrs        = results.get("candidate_years", 0)
    r_yrs        = results.get("required_years", 0)
    c_langs      = results.get("candidate_langs", [])
    r_langs      = results.get("required_langs", [])
    c_edu        = resume_json.get("education", [])
    r_edu        = jd_json.get("required_education", {})

    return (
        TAB_JS
        + render_metrics(score, matched_req, missing_req, c_yrs, r_yrs)
        + render_breakdown(scores)
        + render_summary(summary)
        + render_skills_gap(matched_req, missing_req, matched_pref, missing_pref)
        + render_languages(c_langs, r_langs)
        + render_recommendations(score, missing_req, missing_pref, c_yrs, r_yrs, c_edu, r_edu, scores)
        + '<div class="divider"></div>'
        + """<div class="callout">
          <span>ℹ️</span>
          <span>Results generated by AI + sentence-transformers.
          Scores are probabilistic — use as a guide, not a definitive judgement.</span>
        </div>"""
        + """<div style="margin-top:24px;">
          <button class="btn-ghost" onclick="location.reload()">↩ Analyse Another</button>
        </div>"""
        + f'<div class="foot-note">{score}% · {label} · {LLM_MODEL} · all-MiniLM-L6-v2</div>'
    )