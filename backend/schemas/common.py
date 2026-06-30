# schemas/common.py
"""Shared request/response types used across multiple routes."""

from pydantic import BaseModel


class OkResponse(BaseModel):
    ok: bool
