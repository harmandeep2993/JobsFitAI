# src/prompts/__init__.py

"""
Prompts for extracting structured information from resume and job description.
"""

from .resume_prompt import get_resume_prompt
from .jd_prompt import get_jd_prompt

# Export all functions
__all__ = ["get_resume_prompt", "get_jd_prompt"]