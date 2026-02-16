"""
Chat storage in MongoDB.
One collection: conversations. Each document = one conversation with embedded messages.
"""
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId

from app.core.mongo import get_database

COLLECTION = "conversations"


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def create_conversation(user_id: int) -> str:
    """Create a new conversation for the user. Returns the conversation id (hex string)."""
    db = get_database()
    if db is None:
        raise RuntimeError("MongoDB not initialized")
    doc = {
        "user_id": user_id,
        "created_at": _now(),
        "updated_at": _now(),
        "messages": [],
    }
    result = await db[COLLECTION].insert_one(doc)
    return str(result.inserted_id)


async def get_conversation(conversation_id: str, user_id: int) -> dict[str, Any] | None:
    """Get a conversation by id. Returns None if not found or not owned by user."""
    db = get_database()
    if db is None:
        raise RuntimeError("MongoDB not initialized")
    try:
        oid = ObjectId(conversation_id)
    except Exception:
        return None
    doc = await db[COLLECTION].find_one({"_id": oid, "user_id": user_id})
    if doc is None:
        return None
    doc["id"] = str(doc["_id"])
    return doc


async def append_messages(
    conversation_id: str,
    user_id: int,
    new_messages: list[dict[str, str]],
) -> dict[str, Any] | None:
    """
    Append messages to a conversation. Each item: {"role": "user"|"model", "content": "..."}.
    Returns updated conversation doc or None if not found.
    """
    db = get_database()
    if db is None:
        raise RuntimeError("MongoDB not initialized")
    try:
        oid = ObjectId(conversation_id)
    except Exception:
        return None
    result = await db[COLLECTION].find_one_and_update(
        {"_id": oid, "user_id": user_id},
        {
            "$push": {"messages": {"$each": new_messages}},
            "$set": {"updated_at": _now()},
        },
        return_document=True,
    )
    if result is None:
        return None
    result["id"] = str(result["_id"])
    return result


async def list_conversations(
    user_id: int,
    limit: int = 20,
    skip: int = 0,
) -> list[dict[str, Any]]:
    """List conversations for a user, most recent first. Paginated via skip/limit."""
    db = get_database()
    if db is None:
        raise RuntimeError("MongoDB not initialized")
    cursor = (
        db[COLLECTION]
        .find({"user_id": user_id})
        .sort("updated_at", -1)
        .skip(skip)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)
    for doc in docs:
        doc["id"] = str(doc["_id"])
    return docs


async def get_messages(
    conversation_id: str,
    user_id: int,
    limit: int = 50,
    skip: int = 0,
) -> tuple[list[dict[str, str]], bool]:
    """Get a page of messages. Returns (messages_slice, has_more)."""
    conv = await get_conversation(conversation_id, user_id)
    if conv is None:
        return [], False
    messages = conv.get("messages") or []
    total = len(messages)
    slice_msgs = messages[skip : skip + limit]
    has_more = skip + len(slice_msgs) < total
    return slice_msgs, has_more


async def delete_conversation(conversation_id: str, user_id: int) -> bool:
    """Delete a conversation. Returns True if deleted, False if not found."""
    db = get_database()
    if db is None:
        raise RuntimeError("MongoDB not initialized")
    try:
        oid = ObjectId(conversation_id)
    except Exception:
        return False
    result = await db[COLLECTION].delete_one({"_id": oid, "user_id": user_id})
    return result.deleted_count > 0
