"""
Day 4 Step 2 — Async MongoDB client for chat storage.
Motor = async driver for MongoDB. Init at startup, close on shutdown.
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings

_client: AsyncIOMotorClient | None = None
_db_name: str = "edgechat"


def get_database() -> AsyncIOMotorDatabase | None:
    """Return the MongoDB database instance, or None if not initialized."""
    global _client
    if _client is None:
        return None
    return _client[_db_name]


async def init_mongo() -> None:
    """Create the MongoDB connection. Call once at app startup."""
    global _client
    _client = AsyncIOMotorClient(
        settings.MONGODB_URL,
        serverSelectionTimeoutMS=5000,
    )


async def close_mongo() -> None:
    """Close the MongoDB connection. Call on app shutdown."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
