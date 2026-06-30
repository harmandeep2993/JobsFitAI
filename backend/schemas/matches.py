# schemas/matches.py
"""Request/response models for job match endpoints."""

from pydantic import BaseModel
from typing import Optional


class MatchResumeRequest(BaseModel):
    tmp: str
    name: Optional[str] = "resume"


class AppliedRequest(BaseModel):
    id: str
    applied: bool


class AppStatusRequest(BaseModel):
    id: str
    status: str


class ScoreJdRequest(BaseModel):
    id: str
    jd_text: str


class SchedulerRequest(BaseModel):
    enabled: Optional[bool] = None
    interval: Optional[int] = None


class DeleteJobRequest(BaseModel):
    id: str
