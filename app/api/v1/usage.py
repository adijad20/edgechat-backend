"""
Day 4 Step 7 — GET /usage/me: current user's API usage stats.
"""
from fastapi import APIRouter

from app.dependencies import CurrentUserDep, SessionDep
from app.services.usage_service import get_usage_stats

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("/me")
async def usage_me(current_user: CurrentUserDep, session: SessionDep):
    """Return the current user's API usage: total_requests, requests_last_24h, requests_last_7d."""
    stats = await get_usage_stats(session, current_user.id)
    return stats
