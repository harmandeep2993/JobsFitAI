# src/frontend/results.py
"""
Renders full results view.
Called after match() returns results dict.
"""

import math

from src.frontend.components import make_tags, prog_grad, safe_html, score_col
from src.utils import session

_GAUGE_R = 17
_GAUGE_CIRC = round(2 * math.pi * _GAUGE_R, 2)  # 106.81


# --- Error panel ---


def render_error_panel(title: str, message: str) -> str:
    """Render a user-facing error inside the results nb-card style.

    Returned HTML is injected into #jf-results by analysis.js when the
    server returns ok=false with an html field (user-fixable errors only).
    System errors (LLM unavailable, 500s) still use the toast path.
    """
    return f"""
<div class="res-section">
  <div class="nb-card" style="border-color:var(--red-bd);overflow:hidden;">
    <div style="display:flex;align-items:flex-start;gap:14px;padding:28px 24px;background:var(--red-bg);">
      <svg width="22" height="22" viewBox="0 0 16 16" fill="none"
           stroke="var(--red)" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"
           style="flex-shrink:0;margin-top:1px;">
        <path d="M8 2L1.5 14h13L8 2z"/>
        <line x1="8" y1="7" x2="8" y2="10"/>
        <circle cx="8" cy="12.5" r=".6" fill="var(--red)" stroke="none"/>
      </svg>
      <div>
        <div style="font-weight:600;color:var(--red);margin-bottom:5px;">{safe_html(title)}</div>
        <div style="color:var(--t2);font-size:.92rem;line-height:1.5;">{safe_html(message)}</div>
      </div>
    </div>
  </div>
</div>"""


# --- SVG icon helpers ---
def _ico(d, s=16):
    return (
        f'<svg width="{s}" height="{s}" viewBox="0 0 16 16" fill="none" '
        f'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" '
        f'stroke-linejoin="round">{d}</svg>'
    )


_ICO_CHECK_CIRCLE = _ico(
    '<circle cx="8" cy="8" r="6"/><polyline points="5,8.5 7,10.5 11,5.5"/>'
)
_ICO_INFO_CIRCLE = _ico(
    '<circle cx="8" cy="8" r="6"/><line x1="8" y1="5.5" x2="8" y2="9"/><circle cx="8" cy="11" r=".6" fill="currentColor" stroke="none"/>'
)
_ICO_ALERT = _ico(
    '<path d="M8 2L1.5 14h13L8 2z"/><line x1="8" y1="7" x2="8" y2="10"/><circle cx="8" cy="12.5" r=".6" fill="currentColor" stroke="none"/>'
)
_ICO_BRIEFCASE = _ico(
    '<rect x="2" y="6" width="12" height="8" rx="1.5"/><path d="M5.5 6V4.5A1.5 1.5 0 0 1 7 3h2a1.5 1.5 0 0 1 1.5 1.5V6"/><line x1="2" y1="10" x2="14" y2="10"/>'
)
_ICO_PENCIL = _ico(
    '<path d="M11.5 2.5l2 2-8 8H3.5V10.5l8-8z"/><line x1="9.5" y1="4.5" x2="11.5" y2="6.5"/>'
)
_ICO_SCHOOL = _ico(
    '<polygon points="8,2.5 1,7 8,11.5 15,7"/><path d="M5 9.5V12c0 1 1.3 1.5 3 1.5s3-.5 3-1.5V9.5"/>'
)
_ICO_SEND = _ico(
    '<line x1="14" y1="2" x2="2" y2="8"/><line x1="14" y1="2" x2="8" y2="14"/><line x1="14" y1="2" x2="6" y2="10"/>'
)
_ICO_MATCH_SM = _ico('<polyline points="3,8.5 6,11.5 13,4.5"/>', s=13)
_ICO_GAP_SM = _ico(
    '<line x1="3" y1="3" x2="13" y2="13"/><line x1="13" y1="3" x2="3" y2="13"/>', s=13
)


def get_direction(score):
    if score >= 80:
        return "cg", "▲ Strong match"
    if score >= 60:
        return "cb", "◆ Good match"
    if score >= 40:
        return "ca", "◆ Partial match"
    return "cr", "▼ Poor match"


PROG_LABELS = {
    "required_skills": "Required Skills",
    "responsibilities": "Responsibilities",
    "experience": "Experience",
    "education": "Education",
    "preferred_skills": "Preferred Skills",
    "languages": "Languages",
    "certifications": "Certifications",
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
    sc = score_col(score)
    d_cls, d_txt = get_direction(score)
    total_req = len(matched_req) + len(missing_req)
    exp_note = f"{c_yrs} yrs experience"

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


_SUM_SECTIONS = [
    ("profile", "Your Profile", _ICO_BRIEFCASE, "sum-sec--profile"),
    ("strengths", "Strengths for This Role", _ICO_CHECK_CIRCLE, "sum-sec--strengths"),
]


def render_summary(summary_text, score=0, label="", matched_req=None, missing_req=None):
    """
    Render the Summary tab panel: gauge ring, score pill, profile/strengths columns.

    Args:
        summary_text: JSON string from generate_summary() or plain fallback text.
        score: overall match score 0-100.
        label: tier label e.g. "Good Match".
        matched_req: list of matched required skill strings.
        missing_req: list of missing required skill strings.

    Returns:
        str: HTML string for the #jf-summary panel.
    """
    import json as _json

    tier = score_tier(score)
    gauge = _gauge(score, tier)

    # Try to parse JSON (new LLM format)
    sections = None
    if summary_text:
        try:
            data = _json.loads(summary_text)
            if isinstance(data, dict) and "profile" in data:
                sections = data
        except (ValueError, TypeError):
            pass

    # Hero card - gauge ring + verdict label
    hero = (
        '<div class="sum-hero">' + gauge + f'<div class="sum-hero-info">'
        f'<div class="sum-hero-label {tier}">{safe_html(label)}</div>'
        f'<div class="sum-hero-sub">{score}% overall match</div>'
        f"</div>"
        f"</div>"
    )

    if sections:
        cards = []
        for key, heading, ico, mod in _SUM_SECTIONS:
            bullets = sections.get(key, [])
            if not bullets:
                continue
            items_html = "".join(f"<li>{b}</li>" for b in bullets)
            cards.append(
                f'<div class="sum-sec {mod}">'
                f'<div class="sum-sec-hd">'
                f'<span class="sum-sec-ico">{ico}</span>'
                f'<span class="sum-sec-ttl">{heading}</span>'
                f"</div>"
                f'<ul class="sum-sec-list">{items_html}</ul>'
                f"</div>"
            )
        body = "".join(cards)
    else:
        # Legacy plain-text fallback
        text = summary_text if summary_text else "<p>Summary not available.</p>"
        body = f'<div class="sum-body">{text}</div>'

    return '<div id="jf-summary" class="jf-panel fade-in">' + hero + body + "</div>"


SCORE_ORDER = [
    "required_skills",
    "responsibilities",
    "experience",
    "education",
    "preferred_skills",
    "languages",
    "certifications",
]


def _gauge(v, tier):
    offset = round(_GAUGE_CIRC * (1 - max(0, min(100, v)) / 100), 2)
    return (
        f'<div class="jt-score">'
        f'<svg class="jt-gauge" viewBox="0 0 44 44" aria-hidden="true">'
        f'<circle class="jt-gauge-bg" cx="22" cy="22" r="{_GAUGE_R}"/>'
        f'<circle class="jt-gauge-arc {tier}" cx="22" cy="22" r="{_GAUGE_R}"'
        f' stroke-dasharray="{_GAUGE_CIRC}" stroke-dashoffset="{_GAUGE_CIRC}"'
        f' data-offset="{offset}"/>'
        f"</svg>"
        f'<span class="jt-score-val {tier}">{v}%</span>'
        f"</div>"
    )


def _bd_why(k, v, c_yrs=0):
    if k == "responsibilities":
        if v >= 80:
            return "Your CV language closely mirrors the role's day-to-day duties"
        if v >= 60:
            return "Decent keyword overlap. A few more JD phrases would strengthen this further"
        if v >= 40:
            return "Limited overlap with job duties. Mirror the JD wording in your bullet points"
        return "Low alignment. Rewrite bullet points to reflect the role's language and responsibilities"
    if k == "experience":
        yrs = f"{c_yrs} yr{'s' if c_yrs != 1 else ''}"
        if v >= 80:
            return f"Your {yrs} of experience aligns well with what this role expects"
        if v >= 60:
            return f"Your {yrs} meets most requirements; the role may expect more seniority"
        if v >= 40:
            return (
                f"Your {yrs} is below typical expectations. Focus on impact over tenure"
            )
        return f"Significant experience gap. This role expects considerably more than {yrs}"
    if k == "education":
        if v >= 80:
            return "Your educational background meets or exceeds the role's stated requirements"
        if v >= 60:
            return (
                "Education partially meets requirements. Emphasise relevant coursework"
            )
        if v >= 40:
            return "Education may fall short. Certifications or projects can compensate"
        return "Education gap. The role specifies qualifications not visible in your profile"
    if k == "certifications":
        if v >= 80:
            return "Your certifications cover what this role requires"
        if v >= 60:
            return (
                "Some certifications match. The role may expect additional credentials"
            )
        if v >= 40:
            return (
                "Limited certification match. Check for specific credentials required"
            )
        return "Missing certifications that this role may require"
    return ""


def _bd_tag_row(label, items, css):
    if not items:
        return ""
    return (
        f'<div class="bd-tag-row">'
        f'<span class="bd-tag-lbl">{label}</span>'
        f'<div class="tags-row">{make_tags(items, css)}</div>'
        f"</div>"
    )


_ICO_CHEVRON = (
    '<svg class="bd-chevron-ico" width="14" height="14" viewBox="0 0 16 16" fill="none" '
    'stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
    '<polyline points="4,6 8,10 12,6"/></svg>'
)


def render_breakdown(
    scores,
    matched_req,
    missing_req,
    matched_pref,
    missing_pref,
    c_langs,
    r_langs,
    c_yrs=0,
):
    """
    Render the Breakdown tab: one collapsible accordion row per scoring section.

    Each row shows a mini gauge ring, score, matched/missing skill tags, and
    a progress bar. Rows are collapsed by default; JS toggles them on click.

    Returns:
        str: HTML string for the #jf-breakdown panel.
    """
    items = []

    for k in SCORE_ORDER:
        if k not in scores:
            continue
        v = int(round(scores[k]))
        lbl = PROG_LABELS.get(k, k)
        tier = score_tier(v)
        grd = prog_grad(v)
        gauge = _gauge(v, tier)

        # Detail content (shown on expand)
        if k == "required_skills":
            detail = _bd_tag_row("Matched", matched_req, "tg") + _bd_tag_row(
                "Missing", missing_req, "tr"
            )
        elif k == "preferred_skills":
            detail = _bd_tag_row("Have", matched_pref, "tg") + _bd_tag_row(
                "Missing", missing_pref, "ta"
            )
        elif k == "languages":
            c_lower = {lang.lower() for lang in c_langs}
            lang_matched = [lang for lang in r_langs if lang.lower() in c_lower]
            lang_missing = [lang for lang in r_langs if lang.lower() not in c_lower]
            detail = (
                _bd_tag_row("Candidate", c_langs, "tg")
                + _bd_tag_row("Matched", lang_matched, "tg")
                + _bd_tag_row("Missing", lang_missing, "tr")
            )
        else:
            why = _bd_why(k, v, c_yrs)
            detail = f'<p class="bd-reason">{safe_html(why)}</p>' if why else ""

        detail_html = (
            (
                f'<div class="bd-item-detail">'
                f'<div class="bd-item-detail-inner">{detail}</div>'
                f"</div>"
            )
            if detail
            else ""
        )

        items.append(
            f'<div class="bd-item" data-open="false">'
            # Header row - always visible, click to toggle
            f'<div class="bd-item-hd" onclick="bdToggle(this.closest(\'.bd-item\'))">'
            f'<div class="bd-item-left">'
            f'<span class="bd-dot {tier}"></span>'
            f'<span class="bd-item-lbl">{safe_html(lbl)}</span>'
            f"</div>"
            f'<div class="bd-item-right">'
            + gauge
            + (f'<span class="bd-chevron">{_ICO_CHEVRON}</span>' if detail else "")
            + f"</div>"
            f"</div>"
            # Progress bar - always visible
            f'<div class="bd-item-bar">'
            f'<div class="bd-bar"><div class="bd-bar-fill" style="width:{v}%;background:{grd};"></div></div>'
            f"</div>" + detail_html + "</div>"
        )

    return (
        '<div class="tab-row" id="jf-tab-row">'
        '<div class="tab-item active" onclick="jfTab(this,\'jf-summary\')">Summary</div>'
        '<div class="tab-item"        onclick="jfTab(this,\'jf-breakdown\')">Breakdown</div>'
        '<div class="tab-item"        onclick="jfTab(this,\'jf-keywords\')">Keywords</div>'
        '<div class="tab-item"        onclick="jfTab(this,\'jf-reco\')">Recommendations</div>'
        "</div>"
        '<div id="jf-breakdown" class="jf-panel" style="display:none;">'
        '<div class="bd-panel-hd">'
        '<span class="bd-panel-title">Score Breakdown</span>'
        '<button class="bd-expand-all" onclick="bdToggleAll(this)">Expand all</button>'
        "</div>"
        '<div class="bd-list">' + "".join(items) + "</div>"
        "</div>"
    )


def render_keywords(matched_req, missing_req, matched_pref, missing_pref):
    """
    Render the Keywords tab: coverage bar + colour-coded skill tag sections.

    Green tags = matched skills present in the resume.
    Red tags = skills the JD requires but not found in the resume.

    Returns:
        str: HTML string for the #jf-keywords panel.
    """
    total = len(matched_req) + len(missing_req) + len(matched_pref) + len(missing_pref)
    covered = len(matched_req) + len(matched_pref)

    if total == 0:
        return (
            '<div id="jf-keywords" class="jf-panel" style="display:none;">'
            '<p class="kw-empty">No keyword data extracted from this job description.</p>'
            "</div>"
        )

    pct = round((covered / total) * 100)
    tier = score_tier(pct)
    grd = prog_grad(pct)

    coverage = (
        f'<div class="kw-card kw-coverage">'
        f'<div class="kw-coverage-hd">'
        f'<span class="kw-coverage-lbl">Keyword Coverage</span>'
        f'<span class="kw-coverage-pct {tier}">{covered} of {total} keywords matched</span>'
        f"</div>"
        f'<div class="bd-bar"><div class="bd-bar-fill" style="width:{pct}%;background:{grd};"></div></div>'
        f"</div>"
    )

    def kw_section(heading, matched, missing, miss_css="tr"):
        if not matched and not missing:
            return ""
        matched_tags = "".join(
            f'<span class="tag tg">{safe_html(s)}</span>' for s in matched
        )
        missing_tags = "".join(
            f'<span class="tag {miss_css}">{safe_html(s)}</span>' for s in missing
        )
        return (
            f'<div class="kw-card">'
            f'<div class="kw-section-hd">{heading}</div>'
            f'<div class="kw-tags">{matched_tags}{missing_tags}</div>'
            f"</div>"
        )

    return (
        '<div id="jf-keywords" class="jf-panel kw-panel" style="display:none;">'
        + coverage
        + kw_section("Required Skills", matched_req, missing_req, "tr")
        + kw_section("Preferred Skills", matched_pref, missing_pref, "ta")
        + "</div>"
    )


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
        ("Required - Matched", matched_req, "tg"),
        ("Required - Missing", missing_req, "tr"),
        ("Preferred - Matched", matched_pref, "tg"),
        ("Preferred - Missing", missing_pref, "ta"),
    ]

    blocks = "".join(
        f'<div class="gap-block">'
        f'<div class="gap-lbl">{safe_html(lbl)}</div>'
        f'<div class="tags-row">{make_tags(items, css)}</div>'
        f"</div>"
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
    c_str = ", ".join(c_langs) if c_langs else "None"
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


def render_recommendations(
    score, missing_req, missing_pref, c_yrs, c_edu, r_edu_list, scores
):
    """
    Build recommendations panel HTML.
    Rule-based - no LLM needed.

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

    def _rcard(level, icon, title, body):
        return (
            f'<div class="reco-card reco-{level}">'
            f'<div class="reco-icon">{icon}</div>'
            f'<div class="reco-body">'
            f'<div class="reco-title">{title}</div>'
            f'<div class="reco-text">{body}</div>'
            f"</div>"
            f"</div>"
        )

    # Required skills gap - highest priority
    if missing_req:
        tags = "".join(
            f"<span class='tag tr'>{safe_html(s)}</span>" for s in missing_req[:6]
        )
        items.append(
            _rcard(
                "high",
                _ICO_ALERT,
                "Acquire the Missing Required Skills",
                f"These skills appear in the job requirements but are not visible in your profile. "
                f"Closing these gaps directly raises your match score and helps pass ATS screening."
                f'<div class="tags-row" style="margin-top:8px;">{tags}</div>',
            )
        )

    # Preferred skills gap
    if missing_pref:
        tags = "".join(
            f"<span class='tag ta'>{safe_html(s)}</span>" for s in missing_pref[:5]
        )
        items.append(
            _rcard(
                "med",
                _ICO_BRIEFCASE,
                "Strengthen with Preferred Skills",
                f"These are listed as nice-to-have. Adding any of them increases your "
                f"competitiveness over candidates who only meet the bare minimum."
                f'<div class="tags-row" style="margin-top:8px;">{tags}</div>',
            )
        )

    # CV language alignment
    resp_score = scores.get("responsibilities", 100)
    if resp_score < 50:
        items.append(
            _rcard(
                "med",
                _ICO_PENCIL,
                "Mirror the Job Description Language",
                "Your CV phrasing does not closely match the role's requirements. "
                "Rewrite your bullet points to use the same verbs and terms the JD uses. "
                "ATS systems score candidates higher when language aligns.",
            )
        )

    # Education gap
    if r_edu_list and c_edu:
        r_edu_text = " ".join(r_edu_list).lower()
        deg_hierarchy = ["phd", "msc", "bsc", "bachelor", "diploma"]
        r_level = next((i for i, d in enumerate(deg_hierarchy) if d in r_edu_text), 99)
        c_degrees = [e.get("degree", "").lower() for e in c_edu]
        c_level = min(
            (
                i
                for i, d in enumerate(deg_hierarchy)
                if any(d in cd for cd in c_degrees)
            ),
            default=99,
        )
        if c_level > r_level:
            items.append(
                _rcard(
                    "low",
                    _ICO_SCHOOL,
                    "Compensate for the Education Gap",
                    f"The role specifies {safe_html(r_edu_list[0])} as a requirement. "
                    "Emphasise relevant certifications, self-study, or project work "
                    "that demonstrates equivalent knowledge and practical ability.",
                )
            )

    # Positive outcome cards
    if score >= 80:
        items.append(
            _rcard(
                "good",
                _ICO_SEND,
                "Your Profile is a Strong Fit",
                "You meet the core requirements well. Write a focused cover letter that ties "
                "your specific experience directly to the role's needs, then apply with confidence.",
            )
        )
    elif score >= 60 and not missing_req:
        items.append(
            _rcard(
                "good",
                _ICO_CHECK_CIRCLE,
                "A Good Fit - Apply and Address Gaps in Your Cover Letter",
                "You meet the essential requirements. Use your cover letter to speak directly "
                "to any preferred skills you are working toward.",
            )
        )

    if not items:
        return (
            '<div id="jf-reco" class="jf-panel" style="display:none;">'
            '<p class="reco-empty">No specific gaps identified. Review the Breakdown tab for detail.</p>'
            "</div>"
        )

    word = f'recommendation{"s" if len(items) != 1 else ""}'
    header = (
        f'<div class="reco-panel-hd">'
        f'<span class="reco-panel-count">{len(items)}</span>'
        f" {word}"
        f"</div>"
    )

    return (
        '<div id="jf-reco" class="jf-panel" style="display:none;">'
        + header
        + "".join(items)
        + "</div>"
    )


def render_swot(swot):
    """Build SWOT analysis tab panel HTML."""
    if not swot:
        return (
            '<div id="jf-swot" class="jf-panel" style="display:none;">'
            '<p style="color:var(--t3);font-size:13px;">SWOT analysis unavailable.</p>'
            "</div>"
        )

    def quad(title, items, mod, icon):
        bullets = "".join(
            f'<li class="swot-item">{safe_html(item)}</li>' for item in items
        )
        return (
            f'<div class="swot-quad swot-{mod}">'
            f'<div class="swot-quad-hd"><span class="swot-icon">{icon}</span>{safe_html(title)}</div>'
            f'<ul class="swot-list">{bullets}</ul>'
            f"</div>"
        )

    grid = (
        quad("Strengths", swot.get("strengths", []), "s", "💪")
        + quad("Weaknesses", swot.get("weaknesses", []), "w", "⚠️")
        + quad("Opportunities", swot.get("opportunities", []), "o", "🚀")
        + quad("Threats", swot.get("threats", []), "t", "🎯")
    )

    return (
        f'<div id="jf-swot" class="jf-panel" style="display:none;">'
        f'<div class="swot-grid">{grid}</div>'
        f"</div>"
    )


def score_tier(score):
    if score >= 80:
        return "sc-exc"
    if score >= 60:
        return "sc-good"
    if score >= 40:
        return "sc-partial"
    return "sc-poor"


def _bd_items_html(
    scores,
    matched_req,
    missing_req,
    matched_pref,
    missing_pref,
    c_langs,
    r_langs,
    c_yrs=0,
):
    items = []
    for k in SCORE_ORDER:
        if k not in scores:
            continue
        v = int(round(scores[k]))
        lbl = PROG_LABELS.get(k, k)
        tier = score_tier(v)
        grd = prog_grad(v)
        gauge = _gauge(v, tier)

        if k == "required_skills":
            detail = _bd_tag_row("Matched", matched_req, "tg") + _bd_tag_row(
                "Missing", missing_req, "tr"
            )
        elif k == "preferred_skills":
            detail = _bd_tag_row("Have", matched_pref, "tg") + _bd_tag_row(
                "Missing", missing_pref, "ta"
            )
        elif k == "languages":
            c_lower = {lang.lower() for lang in c_langs}
            lang_matched = [lang for lang in r_langs if lang.lower() in c_lower]
            lang_missing = [lang for lang in r_langs if lang.lower() not in c_lower]
            detail = (
                _bd_tag_row("Candidate", c_langs, "tg")
                + _bd_tag_row("Matched", lang_matched, "tg")
                + _bd_tag_row("Missing", lang_missing, "tr")
            )
        else:
            why = _bd_why(k, v, c_yrs)
            detail = f'<p class="bd-reason">{safe_html(why)}</p>' if why else ""

        detail_html = (
            (
                f'<div class="bd-item-detail"><div class="bd-item-detail-inner">{detail}</div></div>'
            )
            if detail
            else ""
        )

        items.append(
            f'<div class="bd-item" data-open="false">'
            f'<div class="bd-item-hd" onclick="bdToggle(this.closest(\'.bd-item\'))">'
            f'<div class="bd-item-left">'
            f'<span class="bd-dot {tier}"></span>'
            f'<span class="bd-item-lbl">{safe_html(lbl)}</span>'
            f"</div>"
            f'<div class="bd-item-right">'
            + gauge
            + (f'<span class="bd-chevron">{_ICO_CHEVRON}</span>' if detail else "")
            + f"</div></div>"
            f'<div class="bd-item-bar">'
            f'<div class="bd-bar"><div class="bd-bar-fill" style="width:{v}%;background:{grd};"></div></div>'
            f"</div>" + detail_html + "</div>"
        )
    return "".join(items)


def _reco_cards_html(
    score, missing_req, missing_pref, c_yrs, c_edu, r_edu_list, scores
):
    def _rc(level, icon, title, body):
        return (
            f'<div class="reco-card reco-{level}">'
            f'<div class="reco-icon">{icon}</div>'
            f'<div class="reco-body">'
            f'<div class="reco-title">{title}</div>'
            f'<div class="reco-text">{body}</div>'
            f"</div></div>"
        )

    cards = []

    if missing_req:
        tags = "".join(
            f"<span class='tag tr'>{safe_html(s)}</span>" for s in missing_req[:6]
        )
        cards.append(
            _rc(
                "high",
                _ICO_ALERT,
                "Acquire the Missing Required Skills",
                f"These skills appear in the job requirements but are absent from your profile. "
                f'<div class="tags-row" style="margin-top:8px;">{tags}</div>',
            )
        )

    if missing_pref:
        tags = "".join(
            f"<span class='tag ta'>{safe_html(s)}</span>" for s in missing_pref[:5]
        )
        cards.append(
            _rc(
                "med",
                _ICO_BRIEFCASE,
                "Strengthen with Preferred Skills",
                f"Nice-to-have skills that increase competitiveness over minimum-qualified candidates."
                f'<div class="tags-row" style="margin-top:8px;">{tags}</div>',
            )
        )

    if scores.get("responsibilities", 100) < 50:
        cards.append(
            _rc(
                "med",
                _ICO_PENCIL,
                "Mirror the Job Description Language",
                "Rewrite bullet points to use the same verbs and terms the JD uses. "
                "ATS systems score candidates higher when language aligns.",
            )
        )

    if r_edu_list and c_edu:
        r_edu_text = " ".join(r_edu_list).lower()
        deg_hier = ["phd", "msc", "bsc", "bachelor", "diploma"]
        r_level = next((i for i, d in enumerate(deg_hier) if d in r_edu_text), 99)
        c_degrees = [e.get("degree", "").lower() for e in c_edu]
        c_level = min(
            (i for i, d in enumerate(deg_hier) if any(d in cd for cd in c_degrees)),
            default=99,
        )
        if c_level > r_level:
            cards.append(
                _rc(
                    "low",
                    _ICO_SCHOOL,
                    "Compensate for the Education Gap",
                    f"The role specifies {safe_html(r_edu_list[0])}. "
                    "Emphasise certifications, self-study, or projects that demonstrate equivalent knowledge.",
                )
            )

    if score >= 80:
        cards.append(
            _rc(
                "good",
                _ICO_SEND,
                "Your Profile is a Strong Fit",
                "Write a focused cover letter and apply with confidence.",
            )
        )
    elif score >= 60 and not missing_req:
        cards.append(
            _rc(
                "good",
                _ICO_CHECK_CIRCLE,
                "A Good Fit - Apply and Address Gaps in Your Cover Letter",
                "Use your cover letter to speak directly to preferred skills you are working toward.",
            )
        )

    if not cards:
        return '<p class="rv2-empty">No specific gaps identified - review the Breakdown for detail.</p>'
    return "".join(cards)


def _render_summary_panel(score, label, tier, summary_data):
    gauge = _gauge(score, tier)
    hero = (
        '<div class="sum-hero">' + gauge + f'<div class="sum-hero-info">'
        f'<div class="sum-hero-label {tier}">{safe_html(label)}</div>'
        f'<div class="sum-hero-sub">{score}% overall match</div>'
        f"</div>"
        f"</div>"
    )

    secs = ""
    for key, css, icon, title in [
        ("profile", "sum-sec--profile", _ICO_BRIEFCASE, "Your Profile"),
        ("strengths", "sum-sec--strengths", _ICO_CHECK_CIRCLE, "Strengths"),
    ]:
        pts = summary_data.get(key, [])
        if not pts:
            continue
        items = "".join(f"<li>{safe_html(p)}</li>" for p in pts)
        secs += (
            f'<div class="sum-sec {css}">'
            f'<div class="sum-sec-hd">'
            f'<span class="sum-sec-ico">{icon}</span>'
            f'<span class="sum-sec-ttl">{safe_html(title)}</span>'
            f"</div>"
            f'<ul class="sum-sec-list">{items}</ul>'
            f"</div>"
        )

    if not secs:
        secs = (
            '<div class="sum-sec sum-sec--profile">'
            '<div class="sum-sec-hd"><span class="sum-sec-ttl">Profile</span></div>'
            '<ul class="sum-sec-list"><li style="color:var(--t3)">Summary not available - run the analysis first.</li></ul>'
            "</div>"
        )

    return f'<div id="jf-summary" class="jf-panel">{hero}{secs}</div>'


def _render_breakdown_panel(
    scores,
    matched_req,
    missing_req,
    matched_pref,
    missing_pref,
    c_langs,
    r_langs,
    c_yrs,
):
    ctrl = (
        '<div class="bd-panel-hd">'
        '<span class="bd-panel-title">Score breakdown</span>'
        '<button class="bd-expand-all" onclick="bdToggleAll(this)">Expand all</button>'
        "</div>"
    )
    items = _bd_items_html(
        scores,
        matched_req,
        missing_req,
        matched_pref,
        missing_pref,
        c_langs,
        r_langs,
        c_yrs,
    )
    return (
        f'<div id="jf-breakdown" class="jf-panel" style="display:none;">'
        f'{ctrl}<div class="bd-list">{items}</div>'
        f"</div>"
    )


def _render_keywords_panel(matched_req, missing_req, matched_pref, missing_pref):
    kw_total = (
        len(matched_req) + len(missing_req) + len(matched_pref) + len(missing_pref)
    )
    kw_covered = len(matched_req) + len(matched_pref)
    kw_pct = round((kw_covered / kw_total) * 100) if kw_total > 0 else 0
    tier = score_tier(kw_pct)
    grd = prog_grad(kw_pct)

    def _section(title, items, tag_css):
        if not items:
            return ""
        tags = "".join(
            f'<span class="tag {tag_css}">{safe_html(s)}</span>' for s in items
        )
        return (
            f'<div class="kw-section-hd">{title}</div><div class="kw-tags">{tags}</div>'
        )

    coverage = (
        f'<div class="kw-coverage">'
        f'<div class="kw-coverage-hd">'
        f'<span class="kw-coverage-lbl">Overall keyword coverage</span>'
        f'<span class="kw-coverage-pct {tier}">{kw_pct}%</span>'
        f"</div>"
        f'<div class="bd-bar"><div class="bd-bar-fill" style="width:{kw_pct}%;background:{grd};"></div></div>'
        f"</div>"
    )
    sections = (
        _section("Required - matched", matched_req, "tg")
        + _section("Required - missing", missing_req, "tr")
        + _section("Preferred - matched", matched_pref, "tg")
        + _section("Preferred - missing", missing_pref, "ta")
    )
    return (
        f'<div id="jf-keywords" class="jf-panel" style="display:none;">'
        f'<div class="kw-panel"><div class="kw-card">{coverage}{sections}</div></div>'
        f"</div>"
    )


def build_results_html(
    results: dict, resume_json: dict, jd_json: dict, summary: str = ""
) -> str:
    """
    Assemble the full analysis results HTML injected into #jf-results.

    Combines all tab panels (Summary, Breakdown, Keywords, Recommendations)
    into a single .nb-card with the shared tab-row header and export footer.

    Args:
        results: output of match() - scores, labels, matched/missing skills.
        resume_json: extracted resume data dict.
        jd_json: extracted job description data dict.
        summary: JSON string from generate_summary(); empty string on failure.

    Returns:
        str: Full HTML string ready for innerHTML injection.
    """
    import json as _json

    score = results.get("overall_score", 0)
    label = results.get("label", "")
    scores = results.get("section_scores", {})
    matched_req = results.get("matched_required", [])
    missing_req = results.get("missing_required", [])
    matched_pref = results.get("matched_preferred", [])
    missing_pref = results.get("missing_preferred", [])

    c_yrs = resume_json.get("meta", {}).get("total_experience_years", 0)
    c_langs = resume_json.get("languages", [])
    r_langs = jd_json.get("languages", [])
    c_edu = resume_json.get("education", [])
    r_edu_list = jd_json.get("education_requirements", [])

    tier = score_tier(score)

    summary_data = {}
    if summary:
        try:
            d = _json.loads(summary)
            if isinstance(d, dict):
                summary_data = d
        except (ValueError, TypeError):
            pass

    tab_row = (
        '<div class="tab-row" id="jf-tab-row">'
        '<div class="tab-item active" onclick="jfTab(this,\'jf-summary\')">Summary</div>'
        '<div class="tab-item" onclick="jfTab(this,\'jf-breakdown\')">Breakdown</div>'
        '<div class="tab-item" onclick="jfTab(this,\'jf-keywords\')">Keywords</div>'
        '<div class="tab-item" onclick="jfTab(this,\'jf-reco\')">Recommendations</div>'
        '<div class="tab-item" onclick="jfTab(this,\'jf-rewrite\');rwEnsureLoaded()">Improve</div>'
        "</div>"
    )

    summary_panel = _render_summary_panel(score, label, tier, summary_data)
    breakdown_panel = _render_breakdown_panel(
        scores,
        matched_req,
        missing_req,
        matched_pref,
        missing_pref,
        c_langs,
        r_langs,
        c_yrs,
    )
    keywords_panel = _render_keywords_panel(
        matched_req, missing_req, matched_pref, missing_pref
    )
    reco_panel = (
        '<div id="jf-reco" class="jf-panel" style="display:none;">'
        + _reco_cards_html(
            score, missing_req, missing_pref, c_yrs, c_edu, r_edu_list, scores
        )
        + "</div>"
    )

    callout = (
        '<div class="callout">'
        '<span class="callout-icon">'
        + _ICO_INFO_CIRCLE
        + "</span><span>Results are AI-generated. Scores are probabilistic - use as a guide, not a definitive judgement.</span>"
        "</div>"
    )
    export_row = (
        '<div class="res-export-row">'
        '<span class="foot-note">'
        + str(score)
        + "% &middot; "
        + label
        + " &middot; "
        + session.get_model()
        + "</span>"
        '<div class="res-export-btns">'
        '<button class="res-export-btn" onclick="copyResults()" title="Copy summary to clipboard">'
        '<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        '<rect x="5" y="1" width="9" height="11" rx="1.5"/>'
        '<rect x="1" y="4" width="9" height="11" rx="1.5"/>'
        "</svg>"
        "Copy</button>"
        '<button class="res-export-btn" onclick="window.print()" title="Print report">'
        '<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M4 6V1h8v5"/>'
        '<rect x="1" y="6" width="14" height="7" rx="1"/>'
        '<path d="M4 10h8M4 13h5"/>'
        "</svg>"
        "Print</button>"
        "</div>"
        "</div>"
    )

    rewrite_panel = (
        '<div id="jf-rewrite" class="jf-panel" style="display:none;">'
        '<div class="rw-intro">'
        '<div class="rw-intro-text">'
        "Generate JD-aligned bullets from all your stored resumes. "
        "Existing bullets are rewritten to match the role's language; "
        "roles with no bullets get suggested starting points."
        "</div>"
        '<button class="rw-run-btn" id="rw-run-btn" onclick="rwGenerate()">'
        '<svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" '
        'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="margin-right:6px;">'
        '<polygon points="3,2 13,8 3,14"/>'
        "</svg>"
        "Generate Improved Bullets"
        "</button>"
        "</div>"
        '<div id="rw-output"></div>'
        "</div>"
    )

    return (
        '<div class="res-section">'
        '<div class="nb-card">'
        + tab_row
        + summary_panel
        + breakdown_panel
        + keywords_panel
        + reco_panel
        + rewrite_panel
        + "</div>"
        + callout
        + export_row
        + "</div>"
    )
