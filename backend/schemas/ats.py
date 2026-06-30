# schemas/ats.py
"""Request/response models for ATS Maker endpoints."""

from pydantic import BaseModel
from typing import Optional


class AtsCheckRequest(BaseModel):
    resume_id: str
    jd: Optional[str] = None


class AtsOptimiseRequest(BaseModel):
    resume_id: str
    jd: str
