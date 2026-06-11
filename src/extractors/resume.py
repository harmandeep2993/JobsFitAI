# src/extractors/resume.py
"""
Resume extraction module.

Uses an LLM to extract structured information from resume text.
Includes light post-processing to normalize all string values to lowercase.
"""

import re
import datetime as dt

from src.utils.router import call_llm, parse_json_response
from src.utils.config import RESUME_MAX_CHARS
from src.prompts import get_resume_prompt
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Words that mean "still ongoing" across the languages we support.
_PRESENT_WORDS = {
    "present", "current", "now", "ongoing", "to date", "till date",
    "heute", "aktuell", "laufend", "actuel", "actuellement", "présent",
    "actual", "presente", "attuale",
}

_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _parse_month_year(value) -> dt.date | None:
    """
    Parse a normalized resume date into a date (day = 1).

    Handles "YYYY-MM", "YYYY/MM", "YYYY", month-name forms like
    "mar 2020", and "present"/current-role words. Returns None when the
    value can't be parsed.
    """
    if not value or not isinstance(value, str):
        return None

    s = value.strip().lower()
    if not s:
        return None

    if s in _PRESENT_WORDS or s.startswith("present") or s.startswith("current"):
        return dt.date.today()

    # YYYY-MM / YYYY/MM / YYYY.MM (optionally with a day after)
    m = re.match(r"^(\d{4})[-/.](\d{1,2})", s)
    if m:
        year, month = int(m.group(1)), int(m.group(2))
        if 1900 <= year <= 2100:
            return dt.date(year, month if 1 <= month <= 12 else 1, 1)
        return None

    # MM/YYYY or M/YYYY (month-first, 4-digit year) — the common resume format.
    m = re.match(r"^(\d{1,2})[-/.](\d{4})$", s)
    if m:
        month, year = int(m.group(1)), int(m.group(2))
        if 1900 <= year <= 2100:
            return dt.date(year, month if 1 <= month <= 12 else 1, 1)
        return None

    # DD/MM/YYYY (day-month-year) — take the month and year.
    m = re.match(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})$", s)
    if m:
        month, year = int(m.group(2)), int(m.group(3))
        if 1900 <= year <= 2100:
            return dt.date(year, month if 1 <= month <= 12 else 1, 1)
        return None

    # Any 4-digit year, plus an optional month name anywhere in the string.
    ym = re.search(r"(\d{4})", s)
    if ym:
        year = int(ym.group(1))
        if not (1900 <= year <= 2100):
            return None
        month = 1
        mm = re.search(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)", s)
        if mm:
            month = _MONTHS[mm.group(1)]
        return dt.date(year, month, 1)

    return None


def _entry_duration_years(entry: dict) -> float:
    """Years between an entry's start and end dates, rounded to 1 decimal."""
    start = _parse_month_year(entry.get("start_date", ""))
    end   = _parse_month_year(entry.get("end_date", ""))
    if not start or not end or end < start:
        return 0.0
    return round((end - start).days / 365.25, 1)


def _total_experience_years(entries: list) -> float:
    """
    Total years of experience as the union of all date ranges.

    Merging overlapping ranges avoids double-counting concurrent roles
    (the source of inflated, inconsistent totals).
    """
    intervals = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        start = _parse_month_year(entry.get("start_date", ""))
        end   = _parse_month_year(entry.get("end_date", ""))
        if start and end and end >= start:
            intervals.append((start, end))

    if not intervals:
        return 0.0

    intervals.sort()
    merged = [list(intervals[0])]
    for start, end in intervals[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])

    total_days = sum((end - start).days for start, end in merged)
    return round(total_days / 365.25, 1)


def _compute_experience_durations(result: dict) -> dict:
    """
    Fill duration_years per entry and meta.total_experience_years in Python.

    Deterministic — the same dates always yield the same numbers — and
    overrides whatever the LLM put in those fields.
    """
    entries = result.get("experience_entries", [])

    if isinstance(entries, list):
        for entry in entries:
            if isinstance(entry, dict):
                entry["duration_years"] = _entry_duration_years(entry)
        total = _total_experience_years(entries)
    else:
        total = 0.0

    meta = result.setdefault("meta", {})
    if isinstance(meta, dict):
        meta["total_experience_years"] = total

    logger.debug("Computed total experience: %.1f years", total)
    return result


# Only these list fields are lowercased — they feed exact-match comparisons.
# All other fields (candidate name, titles, company names, etc.) keep original casing
# so the UI displays them correctly.
_COMPARISON_LIST_FIELDS = ("skills", "languages", "certifications")


def _lowercase_comparison_fields(data: dict) -> dict:
    """Lowercase only list fields used for text comparison; preserve all display fields."""
    for key in _COMPARISON_LIST_FIELDS:
        val = data.get(key)
        if isinstance(val, list):
            data[key] = [
                v.lower().strip() if isinstance(v, str) else v
                for v in val
            ]
    return data


_RESUME_FIELD_TYPES: dict = {
    "candidate":          dict,
    "experience_entries": list,
    "projects":           list,
    "education":          list,
    "skills":             list,
    "languages":          list,
    "certifications":     list,
    "meta":               dict,
}

_RESUME_DEFAULTS: dict = {
    "candidate":          {},
    "experience_entries": [],
    "projects":           [],
    "education":          [],
    "skills":             [],
    "languages":          [],
    "certifications":     [],
    "meta":               {},
}


def _validate_resume_schema(result: dict) -> dict:
    """Ensure all required resume fields exist with correct types; fill gaps with safe defaults."""
    for field, expected_type in _RESUME_FIELD_TYPES.items():
        val = result.get(field)
        if val is None:
            logger.debug("Resume field '%s' missing — using default", field)
            result[field] = _RESUME_DEFAULTS[field]
        elif not isinstance(val, expected_type):
            logger.warning(
                "Resume field '%s' has unexpected type %s (expected %s) — using default",
                field, type(val).__name__, expected_type.__name__,
            )
            result[field] = _RESUME_DEFAULTS[field]
    return result


def _is_empty(value) -> bool:
    """
    Check if an extracted field value is considered empty.

    Args:
        value: Any extracted field value

    Returns:
        bool: True if value is empty, False otherwise
    """
    return value in ("", None, [], {}, [""]) or value == [None]


def extract_resume(resume_text: str) -> dict:
    """
    Extract structured resume data from raw text using an LLM.

    Pipeline:
        1. Truncate input to RESUME_MAX_CHARS
        2. Build prompt
        3. Call LLM
        4. Parse JSON response
        5. Normalize all values to lowercase

    Args:
        resume_text (str): Raw resume text

    Returns:
        dict: Structured resume data with all string values lowercased

    Raises:
        ValueError: If LLM response is not a valid dict
    """
    if not resume_text or not resume_text.strip():
        logger.warning("Empty resume text received — returning empty dict")
        return {}

    # Truncate to max allowed chars — safeguard for LLM input limits
    if len(resume_text) > RESUME_MAX_CHARS:
        logger.warning(
            "Resume text truncated from %d to %d characters",
            len(resume_text), RESUME_MAX_CHARS
        )
        resume_text = resume_text[:RESUME_MAX_CHARS]

    prompt   = get_resume_prompt(resume_text)
    response = call_llm(prompt)
    result   = parse_json_response(response)

    if not isinstance(result, dict):
        logger.error("LLM response is not a dict: %s", result)
        raise ValueError("Invalid LLM response format")

    result = _validate_resume_schema(result)
    # Durations are computed here (deterministically), not by the LLM.
    result = _compute_experience_durations(result)
    result = _lowercase_comparison_fields(result)

    empty_keys = [k for k, v in result.items() if _is_empty(v)]
    if empty_keys:
        logger.debug("Empty resume fields: %s", empty_keys)

    skills = result.get("skills", [])
    n_skills = (len(skills) if isinstance(skills, list)
                else sum(len(v) for v in skills.values() if isinstance(v, list))
                if isinstance(skills, dict) else 0)
    n_roles = len(result.get("experience_entries", []))
    years   = result.get("meta", {}).get("total_experience_years", 0)
    logger.info("Resume extracted: %d skills, %d roles, %.1fy experience",
                n_skills, n_roles, years)
    return result