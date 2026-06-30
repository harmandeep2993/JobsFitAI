# schemas/analyzer.py
"""Request/response models for the analyzer endpoints."""

from pydantic import BaseModel
from typing import Dict, List, Optional


class AnalyzeRequest(BaseModel):
    jd: str
    tmp: Optional[str] = None
    resume_id: Optional[str] = None


class ResumePreviewRequest(BaseModel):
    tmp: Optional[str] = None
    resume_id: Optional[str] = None


class SectionBreakdown(BaseModel):
    score: float
    matched: List[str]
    missing: List[str]


class AnalyzeSummary(BaseModel):
    profile: List[str]
    strengths: List[str]
    gaps: List[str]
    focus: List[str]


class AnalyzeResponse(BaseModel):
    ok: bool
    cached: bool = False
    score: float
    label: str
    summary: AnalyzeSummary
    breakdown: Dict[str, SectionBreakdown]
    keywords: Dict[str, List[str]]
