# schemas/resume.py
"""Request/response models for resume endpoints."""

from pydantic import BaseModel


class LabelRequest(BaseModel):
    label: str


class RecommendRequest(BaseModel):
    jd: str


class UseForMatchingResponse(BaseModel):
    ok: bool
    rescored: int
    cached: bool
