# schemas/ats.py
"""Request/response models for ATS Maker endpoints."""

from typing import Optional

from pydantic import BaseModel


class AtsCheckRequest(BaseModel):
    resume_id: Optional[str] = None
    tmp: Optional[str] = None
    jd: Optional[str] = None


class AtsOptimiseRequest(BaseModel):
    resume_id: Optional[str] = None
    tmp: Optional[str] = None
    jd: str


class AtsDocxRequest(BaseModel):
    resume: dict
