"""
Day 4 Step 3 — Chat API: conversations and messages with Gemini.
"""
from fastapi import APIRouter, HTTPException, status

from app.dependencies import CurrentUserDep
from app.schemas.chat import (
    ConversationItem,
    CreateConversationResponse,
    GetMessagesResponse,
    ListConversationsResponse,
    MessageItem,
    SendMessageRequest,
    SendMessageResponse,
)
from app.services.ai_service import generate_chat, GeminiQuotaExceededError
from app.services import chat_storage

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/conversations", response_model=CreateConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(current_user: CurrentUserDep):
    """Start a new conversation. Returns the conversation id."""
    conv_id = await chat_storage.create_conversation(current_user.id)
    return CreateConversationResponse(id=conv_id)


@router.get("/conversations", response_model=ListConversationsResponse)
async def list_conversations(
    current_user: CurrentUserDep,
    limit: int = 20,
    skip: int = 0,
):
    """List your conversations, most recent first. Paginated."""
    limit = min(max(1, limit), 100)
    skip = max(0, skip)
    docs = await chat_storage.list_conversations(current_user.id, limit=limit, skip=skip)
    items = [
        ConversationItem(
            id=doc["id"],
            updated_at=doc["updated_at"],
            message_count=len(doc.get("messages", [])),
        )
        for doc in docs
    ]
    has_more = len(docs) == limit
    return ListConversationsResponse(conversations=items, has_more=has_more)


@router.post("/conversations/{conversation_id}/messages", response_model=SendMessageResponse)
async def send_message(
    conversation_id: str,
    body: SendMessageRequest,
    current_user: CurrentUserDep,
):
    """Send a message and get the AI reply. Conversation history is sent as context to Gemini."""
    conv = await chat_storage.get_conversation(conversation_id, current_user.id)
    if conv is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    user_msg = {"role": "user", "content": body.content}
    history = conv.get("messages") or []
    try:
        reply_text = await generate_chat(history + [user_msg])
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
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    model_msg = {"role": "model", "content": reply_text}
    updated = await chat_storage.append_messages(
        conversation_id,
        current_user.id,
        [user_msg, model_msg],
    )
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return SendMessageResponse(
        user_message=MessageItem(role="user", content=body.content),
        model_message=MessageItem(role="model", content=reply_text),
    )


@router.get("/conversations/{conversation_id}/messages", response_model=GetMessagesResponse)
async def get_messages(
    conversation_id: str,
    current_user: CurrentUserDep,
    limit: int = 50,
    skip: int = 0,
):
    """Get message history for a conversation. Paginated."""
    limit = min(max(1, limit), 100)
    skip = max(0, skip)
    messages, has_more = await chat_storage.get_messages(
        conversation_id,
        current_user.id,
        limit=limit,
        skip=skip,
    )
    if not messages and skip == 0:
        conv = await chat_storage.get_conversation(conversation_id, current_user.id)
        if conv is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    items = [MessageItem(role=m["role"], content=m["content"]) for m in messages]
    return GetMessagesResponse(messages=items, has_more=has_more)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user: CurrentUserDep,
):
    """Delete a conversation and all its messages."""
    deleted = await chat_storage.delete_conversation(conversation_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
