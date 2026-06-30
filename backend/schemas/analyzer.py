# schemas/analyzer.py
"""Request/response models for the analyzer endpoints."""

from pydantic import BaseModel
from typing import Optional


class AnalyzeRequest(BaseModel):
    jd: str
    tmp: Optional[str] = None
    resume_id: Optional[str] = None


class ResumePreviewRequest(BaseModel):
    tmp: Optional[str] = None
    resume_id: Optional[str] = None
