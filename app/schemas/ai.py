"""
Day 4 — Pydantic schemas for AI endpoints.
"""
from pydantic import BaseModel, Field


class CompleteRequest(BaseModel):
    """Request body for POST /ai/complete (test endpoint)."""
    prompt: str = Field(..., min_length=1, max_length=32_000)


class CompleteResponse(BaseModel):
    """Response for POST /ai/complete."""
    text: str
