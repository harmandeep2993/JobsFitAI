# fetchers/enrich.py
"""
Full job-description enrichment.

Adzuna's search API only returns a ~500-char snippet, which is too thin to
score well. Its detail page, however, embeds a JSON-LD JobPosting with the
full description. This module fetches that page and extracts the full text
so the matcher scores against the complete JD.
"""

import html
import json
import re
import time

import requests

from core.logger import get_logger

logger = get_logger(__name__)

_TAG_RE = re.compile(r"<[^>]+>")
_LD_RE = re.compile(
    r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
    re.DOTALL,
)
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobsFitAI/1.0)"}


def _clean(text: str) -> str:
    return " ".join(html.unescape(_TAG_RE.sub(" ", text)).split())


def _iter_ld_objects(page: str):
    """Yield every JSON-LD object on the page, flattening @graph wrappers."""
    for block in _LD_RE.findall(page):
        try:
            data = json.loads(block)
        except (ValueError, TypeError):
            continue
        items = data if isinstance(data, list) else [data]
        for it in items:
            if not isinstance(it, dict):
                continue
            if isinstance(it.get("@graph"), list):
                yield from (g for g in it["@graph"] if isinstance(g, dict))
            else:
                yield it


def fetch_full_description(url: str) -> str:
    """
    Return the full job description from a posting's detail page, or "".

    Looks for a JSON-LD JobPosting; falls back to the longest JSON-LD
    'description' string. Never raises - returns "" on any failure.
    """
    if not url:
        return ""

    resp = None
    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=15, headers=_HEADERS)
            if resp.status_code in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(1.0 * (attempt + 1))
                continue
            break
        except requests.RequestException as e:
            if attempt < 2:
                time.sleep(1.0 * (attempt + 1))
                continue
            logger.warning("Full-JD fetch failed (%s): %s", url[:60], e)
            return ""

    if resp is None or resp.status_code != 200:
        return ""

    best = ""
    for obj in _iter_ld_objects(resp.text):
        desc = obj.get("description")
        if not isinstance(desc, str):
            continue
        if obj.get("@type") == "JobPosting":
            return _clean(desc)
        cleaned = _clean(desc)
        if len(cleaned) > len(best):
            best = cleaned

    return best
