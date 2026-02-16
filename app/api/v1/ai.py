"""
Day 4 Step 1 — Test endpoint for Gemini: POST /ai/complete.
"""
from fastapi import APIRouter, HTTPException, status

from app.schemas.ai import CompleteRequest, CompleteResponse
from app.services.ai_service import generate_text, GeminiQuotaExceededError

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/complete", response_model=CompleteResponse)
async def complete(body: CompleteRequest):
    """Send a prompt to Gemini and return the reply. Requires GEMINI_API_KEY in .env."""
    try:
        text = await generate_text(body.prompt)
        return CompleteResponse(text=text)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except GeminiQuotaExceededError as e:
        headers = None
        if e.retry_after_seconds is not None:
            headers = {"Retry-After": str(int(e.retry_after_seconds) + 1)}
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
            headers=headers,
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
