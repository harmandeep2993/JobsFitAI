# schemas/improve.py
"""Request/response models for the resume improve endpoint."""

from pydantic import BaseModel
from typing import List


class ImproveResumeRequest(BaseModel):
    jd: str
    gaps: List[str] = []
    strengths: List[str] = []
