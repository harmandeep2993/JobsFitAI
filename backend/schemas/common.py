# schemas/common.py
"""Shared request/response types used across multiple routes."""

from pydantic import BaseModel


class OkResponse(BaseModel):
    ok: bool


class LlmSettingsRequest(BaseModel):
    provider: str
    model: str


class LlmKeyRequest(BaseModel):
    provider: str
    api_key: str
