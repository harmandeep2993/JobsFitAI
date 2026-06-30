# services/matcher/__init__.py

from .engine import match

get_match_score = match

__all__ = ["match", "get_match_score"]
