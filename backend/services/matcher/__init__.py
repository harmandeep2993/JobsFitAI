# services/matcher/__init__.py

from .matcher import match

get_match_score = match

__all__ = ["match", "get_match_score"]
