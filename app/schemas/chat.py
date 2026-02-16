"""
Day 4 Step 3 — Pydantic schemas for Chat API.
"""
from datetime import datetime
from pydantic import BaseModel, Field


class CreateConversationResponse(BaseModel):
    """Response after creating a conversation."""
    id: str


class SendMessageRequest(BaseModel):
    """Body for POST /conversations/{id}/messages."""
    content: str = Field(..., min_length=1, max_length=32_000)


class MessageItem(BaseModel):
    """One message in a conversation."""
    role: str  # "user" | "model"
    content: str


class SendMessageResponse(BaseModel):
    """Response after sending a message: the user message and the model reply."""
    user_message: MessageItem
    model_message: MessageItem


class ConversationItem(BaseModel):
    """Summary of a conversation in list."""
    id: str
    updated_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True


class ListConversationsResponse(BaseModel):
    """Paginated list of conversations."""
    conversations: list[ConversationItem]
    has_more: bool


class GetMessagesResponse(BaseModel):
    """Paginated message history."""
    messages: list[MessageItem]
    has_more: bool
