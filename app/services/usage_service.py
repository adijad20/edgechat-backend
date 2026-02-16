"""
Log API usage and return stats for /usage/me.
"""
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usage import ApiUsage
from app.dependencies import async_session_factory


async def log_usage(user_id: int, path: str, method: str) -> None:
    """Append one row to api_usage. Call from middleware for authenticated requests."""
    async with async_session_factory() as session:
        try:
            session.add(ApiUsage(user_id=user_id, path=path, method=method))
            await session.commit()
        except Exception:
            await session.rollback()


async def get_usage_stats(session: AsyncSession, user_id: int) -> dict:
    """Return total_requests, requests_last_24h, requests_last_7d for the user."""
    now = datetime.utcnow()
    day_ago = now - timedelta(hours=24)
    week_ago = now - timedelta(days=7)

    total = await session.execute(
        select(func.count()).select_from(ApiUsage).where(ApiUsage.user_id == user_id)
    )
    last_24h = await session.execute(
        select(func.count()).select_from(ApiUsage).where(
            ApiUsage.user_id == user_id,
            ApiUsage.created_at >= day_ago,
        )
    )
    last_7d = await session.execute(
        select(func.count()).select_from(ApiUsage).where(
            ApiUsage.user_id == user_id,
            ApiUsage.created_at >= week_ago,
        )
    )

    return {
        "total_requests": total.scalar() or 0,
        "requests_last_24h": last_24h.scalar() or 0,
        "requests_last_7d": last_7d.scalar() or 0,
    }
