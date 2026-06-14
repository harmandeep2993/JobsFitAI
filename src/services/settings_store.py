# src/services/settings_store.py
"""
User-editable search settings, persisted in SQLite so they survive restarts.

- target_titles: the role keywords the LLM funnel screens against (editable
  from the UI; defaults to config.yaml's list).
- countries: Adzuna country codes to search (entered as country NAMES in the
  UI, e.g. "germany, netherlands"); defaults to the config country.
- location: optional city/region filter (Adzuna `where`); blank = whole country.
"""

import json

from src.services import db
from src.utils.config import TARGET_TITLES, SEARCH_COUNTRY, AUTO_FETCH_MINUTES
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Country name -> Adzuna country code (Adzuna has per-country endpoints).
COUNTRY_CODES = {
    "germany": "de",
    "deutschland": "de",
    "de": "de",
    "netherlands": "nl",
    "holland": "nl",
    "nl": "nl",
    "belgium": "be",
    "belgique": "be",
    "be": "be",
    "austria": "at",
    "österreich": "at",
    "at": "at",
    "switzerland": "ch",
    "schweiz": "ch",
    "ch": "ch",
    "france": "fr",
    "fr": "fr",
    "united kingdom": "gb",
    "uk": "gb",
    "gb": "gb",
    "england": "gb",
    "spain": "es",
    "es": "es",
    "italy": "it",
    "it": "it",
    "poland": "pl",
    "pl": "pl",
    "ireland": "ie",
    "ie": "ie",
}
_CODE_TO_NAME = {
    "de": "germany",
    "nl": "netherlands",
    "be": "belgium",
    "at": "austria",
    "ch": "switzerland",
    "fr": "france",
    "gb": "uk",
    "es": "spain",
    "it": "italy",
    "pl": "poland",
    "ie": "ireland",
}


def _get(key, default):
    with db.connect() as conn:
        r = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    if r and r["value"]:
        try:
            return json.loads(r["value"])
        except (ValueError, TypeError):
            pass
    return default


def _set(key, value) -> None:
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, json.dumps(value)),
        )


# --- Target titles ---
def get_titles() -> list[str]:
    return _get("target_titles", list(TARGET_TITLES))


def set_titles(titles: list[str]) -> None:
    cleaned, seen = [], set()
    for t in titles:
        t = (t or "").strip().lower()
        if t and t not in seen:
            seen.add(t)
            cleaned.append(t)
    _set("target_titles", cleaned)
    logger.info("Target titles updated: %d", len(cleaned))


# --- Countries (codes) / location ---
def get_countries() -> list[str]:
    return _get("countries", [SEARCH_COUNTRY])


def set_countries(names: list[str]) -> None:
    codes = []
    for n in names:
        code = COUNTRY_CODES.get((n or "").strip().lower())
        if code and code not in codes:
            codes.append(code)
    _set("countries", codes or [SEARCH_COUNTRY])
    logger.info("Countries updated: %s", codes or [SEARCH_COUNTRY])


def country_names() -> list[str]:
    """Country codes as display names, for the UI."""
    return [_CODE_TO_NAME.get(c, c) for c in get_countries()]


def get_location() -> str:
    return _get("location", "")


def set_location(loc: str) -> None:
    _set("location", (loc or "").strip())


# --- Background scheduler ---
def get_scheduler_enabled() -> bool:
    # Defaults to on only if config seeded a positive interval.
    return bool(_get("scheduler_enabled", AUTO_FETCH_MINUTES > 0))


def set_scheduler_enabled(value: bool) -> None:
    _set("scheduler_enabled", bool(value))
    logger.info("Scheduler %s", "enabled" if value else "disabled")


def get_scheduler_interval() -> int:
    default = AUTO_FETCH_MINUTES if AUTO_FETCH_MINUTES > 0 else 60
    return int(_get("scheduler_interval", default))


def set_scheduler_interval(minutes: int) -> None:
    _set("scheduler_interval", max(5, int(minutes)))
