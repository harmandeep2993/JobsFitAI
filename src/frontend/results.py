# src/frontend/results.py
"""
Renders full results view.
Called after match() returns results dict.
"""

from src.utils import session
from src.frontend.components import score_col, make_prog, make_tags, safe_html


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
    "certifications":   "Certifications",
}


def render_metrics(score, matched_req, missing_req, c_yrs):
    """
    Build metrics cards HTML.

    Args:
        score       (float): Overall match score
        matched_req (list):  Matched required skills
        missing_req (list):  Missing required skills
        c_yrs       (float): Candidate total experience years
    """
    sc           = score_col(score)
    d_cls, d_txt = get_direction(score)
    total_req    = len(matched_req) + len(missing_req)
    exp_note     = f"{c_yrs} yrs experience"

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
    """
    Build match breakdown tab panel HTML with progress bars.

    Args:
        scores (dict): Section scores from matcher
    """
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
    """
    Build skills gap tab panel HTML.

    Args:
        matched_req  (list): Matched required skills
        missing_req  (list): Missing required skills
        matched_pref (list): Matched preferred skills
        missing_pref (list): Missing preferred skills
    """
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
    """
    Build languages tab panel HTML.

    Args:
        c_langs (list): Candidate languages
        r_langs (list): Required languages from JD
    """
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


def render_recommendations(score, missing_req, missing_pref, c_yrs,
                            c_edu, r_edu_list, scores):
    """
    Build recommendations panel HTML.
    Rule-based — no LLM needed.

    Args:
        score        (float): Final match score
        missing_req  (list):  Missing required skills
        missing_pref (list):  Missing preferred skills
        c_yrs        (float): Candidate years experience
        c_edu        (list):  Candidate education list
        r_edu_list   (list):  JD education requirements list
        scores       (dict):  Section scores
    """
    items = []

    # Skills gap
    if missing_req:
        skills_str = ", ".join(
            f"<span class='tag tr'>{safe_html(s)}</span>"
            for s in missing_req[:6]
        )
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
        pref_str = ", ".join(
            f"<span class='tag ta'>{safe_html(s)}</span>"
            for s in missing_pref[:5]
        )
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
              Rewrite your bullet points using keywords from the job description.
              Mirror the JD language — ATS systems reward this.
            </div>
          </div>
        </div>
        """)

    # Education gap — r_edu_list is now a list of strings
    if r_edu_list and c_edu:
        r_edu_text = " ".join(r_edu_list).lower()
        deg_hierarchy = ["phd", "msc", "bsc", "bachelor", "diploma"]

        r_level = next(
            (i for i, d in enumerate(deg_hierarchy) if d in r_edu_text),
            99
        )
        c_degrees = [e.get("degree", "").lower() for e in c_edu]
        c_level = min(
            (i for i, d in enumerate(deg_hierarchy)
             if any(d in cd for cd in c_degrees)),
            default=99
        )

        if c_level > r_level:
            items.append(f"""
            <div class="reco-card reco-low">
              <div class="reco-icon">🎓</div>
              <div class="reco-body">
                <div class="reco-title">Education Requirement</div>
                <div class="reco-text">
                  Role requires: {safe_html(r_edu_list[0])}.
                  Emphasise relevant coursework or certifications to compensate.
                </div>
              </div>
            </div>
            """)

    # Good score
    if score >= 80:
        items.append(f"""
        <div class="reco-card reco-good">
          <div class="reco-icon">🎯</div>
          <div class="reco-body">
            <div class="reco-title">Strong Match — Apply Now</div>
            <div class="reco-text">
              Your profile is a strong match. Customise your cover letter
              and submit with confidence.
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
              You meet the core requirements. Address preferred skills
              gap in your cover letter.
            </div>
          </div>
        </div>
        """)

    # LLM narrative placeholder
    items.append(f"""
    <div class="reco-card reco-info" style="margin-top:8px;">
      <div class="reco-icon">🤖</div>
      <div class="reco-body">
        <div class="reco-title">AI Narrative — Coming Soon</div>
        <div class="reco-text">
          Personalised LLM-generated career advice will appear here.
        </div>
      </div>
    </div>
    """)

    cards = "".join(items) if items else (
        "<p style='color:var(--t3);font-size:13px;'>No recommendations — great match!</p>"
    )

    return f'<div id="jf-reco" class="jf-panel" style="display:none;">{cards}</div>'


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


def build_results_html(results: dict, resume_json: dict, jd_json: dict, summary: str = "") -> str:
    """
    Build full results HTML string for JS injection.

    Args:
        results     (dict): match() output
        resume_json (dict): Extracted resume data
        jd_json     (dict): Extracted JD data
        summary     (str):  LLM generated summary text

    Returns:
        str: Complete results HTML
    """
    # New key names from matcher.py
    score        = results.get("overall_score", 0)
    label        = results.get("label", "")
    scores       = results.get("section_scores", {})
    matched_req  = results.get("matched_required", [])
    missing_req  = results.get("missing_required", [])
    matched_pref = results.get("matched_preferred", [])
    missing_pref = results.get("missing_preferred", [])

    # From resume/jd directly — not in results dict
    c_yrs     = resume_json.get("meta", {}).get("total_experience_years", 0)
    c_langs   = resume_json.get("languages", [])
    r_langs   = jd_json.get("languages", [])
    c_edu     = resume_json.get("education", [])
    r_edu_list = jd_json.get("education_requirements", [])

    return (
        render_metrics(score, matched_req, missing_req, c_yrs)
        + render_breakdown(scores)
        + render_summary(summary)
        + render_skills_gap(matched_req, missing_req, matched_pref, missing_pref)
        + render_languages(c_langs, r_langs)
        + render_recommendations(
            score, missing_req, missing_pref,
            c_yrs, c_edu, r_edu_list, scores
        )
        + '<div class="divider"></div>'
        + """<div class="callout">
          <span>ℹ️</span>
          <span>Results generated by AI + sentence-transformers.
          Scores are probabilistic — use as a guide, not a definitive judgement.</span>
        </div>"""
        + """<div style="margin-top:24px;">
          <button class="btn-ghost" onclick="location.reload()">↩ Analyse Another</button>
        </div>"""
        + f'<div class="foot-note">{score}% · {label} · {session.get_model()} · paraphrase-multilingual-MiniLM-L12-v2</div>'
    )


