"""
Step 6 — Async Redis client for rate limiting.
Single shared client; init at startup, close on shutdown.
"""
from redis.asyncio import Redis

from app.config import settings

_redis: Redis | None = None


def get_redis() -> Redis | None:
    """Return the shared Redis client, or None if not initialized or unavailable."""
    return _redis


async def init_redis() -> None:
    """Create the shared Redis connection. Call once at app startup."""
    global _redis
    _redis = Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )


async def close_redis() -> None:
    """Close the Redis connection. Call on app shutdown."""
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
