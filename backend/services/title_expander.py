# services/title_expander.py
"""
Entry-level search expansion and keyword gate for the Job Matches funnel.

Combines the user's role titles with the configured entry keywords at fetch
time ("ml engineer" -> "junior ml engineer", "ml engineer intern", ...) and
provides the deterministic exclude-keyword check that blocks seniority and
student markers when the entry-only filter is active. Both keyword lists
live in config.yaml (job_search.entry_keywords / exclude_keywords).
"""

from core.config import ENTRY_KEYWORDS, EXCLUDE_KEYWORDS

# Student-style markers within EXCLUDE_KEYWORDS. Blocked by default in
# entry-only mode, but kept when the user's own titles ask for them.
STUDENT_TERMS = ("werkstudent", "working student", "praktikum", "praktikant")


def _norm(text: str) -> str:
    return (text or "").strip().lower()


def has_entry_qualifier(title: str) -> bool:
    """True when the title already names a level (junior, intern, werkstudent...)."""
    t = _norm(title)
    return any(k in t for k in [_norm(k) for k in ENTRY_KEYWORDS] + list(STUDENT_TERMS))


def entry_search_queries(titles: list[str]) -> list[str]:
    """Combine plain titles with every configured entry keyword.

    Titles the user already qualified are searched exactly as typed:
        'ml engineer'        -> ['ml engineer', 'junior ml engineer',
                                 'entry ml engineer', ..., 'intern ml engineer']
        'junior ml engineer' -> ['junior ml engineer']

    The plain title stays in the list so postings without an explicit level
    marker ("ML Engineer (m/w/d)") are still found - the keyword and LLM
    gates decide their level afterwards.
    """
    queries: list[str] = []
    seen: set[str] = set()

    def _add(q: str) -> None:
        q = _norm(q)
        if q and q not in seen:
            seen.add(q)
            queries.append(q)

    for t in titles:
        _add(t)
        if not has_entry_qualifier(t):
            for k in ENTRY_KEYWORDS:
                _add(f"{k} {t}")
    return queries


def exclude_terms(titles: list[str], entry_only: bool) -> list[str]:
    """Keyword blocklist for the current run.

    Empty when entry-only is off. Seniority markers are always blocked in
    entry-only mode. Student markers (werkstudent, praktikum) are blocked
    too, unless one of the user's own titles asks for them - someone
    searching 'junior ml engineer' wants junior roles, not student posts,
    while someone searching 'werkstudent ml' gets them.
    """
    if not entry_only:
        return []
    wants_student = any(s in _norm(t) for t in titles for s in STUDENT_TERMS)
    if wants_student:
        return [k for k in EXCLUDE_KEYWORDS if _norm(k) not in STUDENT_TERMS]
    return list(EXCLUDE_KEYWORDS)


def title_blocked(title: str, terms: list[str]) -> bool:
    """True when the job title contains any blocklisted keyword."""
    t = _norm(title)
    return any(_norm(k) in t for k in terms)
