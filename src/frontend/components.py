# src/frontend/components.py
# Pure HTML string builders - no NiceGUI, no state
# All functions take data in, return HTML strings out


from src.utils.config import THRESHOLDS


# Colour helpers
def score_col(v):
    """
    Map score to CSS colour variable.

    Args:
        v (float): Score 0-100

    Returns:
        str: CSS var string
    """
    if v >= THRESHOLDS["excellent"]:
        return "var(--green)"
    if v >= THRESHOLDS["good"]:
        return "var(--blue)"
    if v >= THRESHOLDS["partial"]:
        return "var(--amber)"
    return "var(--red)"


def prog_grad(v):
    """
    Map score to CSS gradient for progress bar fill.

    Args:
        v (float): Score 0-100

    Returns:
        str: CSS gradient string
    """
    if v >= THRESHOLDS["excellent"]:
        return "linear-gradient(90deg,var(--green),#5ae89a)"
    if v >= THRESHOLDS["good"]:
        return "linear-gradient(90deg,var(--blue),#7ac8ff)"
    if v >= THRESHOLDS["partial"]:
        return "linear-gradient(90deg,var(--amber),#f5ca6a)"
    return "linear-gradient(90deg,var(--red),#ff8878)"


# Safety
def safe_html(s):
    """
    Escape string for safe HTML insertion.

    Args:
        s (str): Raw string

    Returns:
        str: HTML-escaped string
    """
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# Steps indicator
def make_steps(current):
    """
    Build 4-step progress indicator HTML.

    Steps: Upload → Job Description → Analysing → Results
    current = active step number (1-4)

    Args:
        current (int): Active step 1-4

    Returns:
        str: Steps HTML
    """
    labels = ["Upload", "Job Description", "Analysing", "Results"]
    parts = []

    for i, lbl in enumerate(labels, 1):
        if i < current:
            nc, lc, txt = "s-done", "sl-done", "✓"
        elif i == current:
            nc, lc, txt = "s-act", "sl-act", str(i)
        else:
            nc, lc, txt = "s-todo", "sl-todo", str(i)

        parts.append(
            f'<div class="step-pill">'
            f'<div class="step-num {nc}">{txt}</div>'
            f'<span class="step-lbl {lc}">{lbl}</span>'
            f"</div>"
        )

        if i < 4:
            parts.append('<div class="step-sep"></div>')

    return f'<div class="steps">{"".join(parts)}</div>'


def clamp_score(v):
    """Ensure score stays between 0 and 100."""
    try:
        v = float(v)
    except Exception:
        return 0
    return max(0, min(100, round(v, 1)))


# Progress bar
def make_prog(label, val):
    """
    Build a single labelled progress bar row.

    Args:
        label (str):  Display label
        val   (float): Score 0-100

    Returns:
        str: Progress bar HTML
    """
    val = clamp_score(val)

    return (
        f'<div class="prog-row">'
        f'<div class="prog-head">'
        f'<span class="prog-lbl">{label}</span>'
        f'<span class="prog-pct">{val}%</span>'
        f"</div>"
        f'<div class="prog-track">'
        f'<div class="prog-fill" style="width:{val}%;background:{prog_grad(val)};"></div>'
        f"</div>"
        f"</div>"
    )


# Skill tags
def make_tags(items, css):
    """
    Build a row of skill tag chips.

    Args:
        items (list): Skill strings
        css   (str):  Tag colour class e.g. tg, tr, ta, tb

    Returns:
        str: Tags HTML or em-dash if empty
    """
    if not items:
        return '<span style="font-size:12px;color:var(--t3);">-</span>'

    return "".join(f'<span class="tag {css}">{safe_html(i)}</span>' for i in items)
