# services/prompts/__init__.py

from .jd_prompt import get_jd_prompt
from .resume_prompt import get_resume_prompt

__all__ = ["get_jd_prompt", "get_resume_prompt"]
