# schemas/matches.py
"""Request/response models for job match endpoints."""

from pydantic import BaseModel
from typing import List, Optional, Union


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


class FiltersRequest(BaseModel):
    target_titles: Optional[List[str]] = None
    countries: Optional[Union[List[str], str]] = None
    location: Optional[str] = None
    entry_only: Optional[bool] = None
    arbeitnow_limit: Optional[int] = None
    bundesagentur_limit: Optional[int] = None
