"""Pydantic schemas for agent memory : conversations and messages."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CreateConversationRequest(BaseModel):
    """Request body to create a new conversation.

    Attributes:
        session_id: Client-specified session identifier.
        title: Optional human-readable title.
    """

    session_id: str
    title: Optional[str] = None


class ConversationResponse(BaseModel):
    """Public representation of a conversation.

    Attributes:
        id: UUID of the conversation.
        session_id: Client-specified session identifier.
        title: Optional title.
        created_at: Timestamp of creation.
        updated_at: Timestamp of last update.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AddMessageRequest(BaseModel):
    """Request body to add a message to a conversation.

    Attributes:
        role: ``"user"``, ``"assistant"``, ``"system"``, or ``"tool"``.
        content: Message body text (default empty).
        tool_calls: Optional list of tool call dicts.
        token_count: Token count for this message (default 0).
    """

    role: str  # "user" | "assistant" | "system" | "tool"
    content: str = ""
    tool_calls: Optional[list[dict]] = None
    token_count: int = 0


class MessageResponse(BaseModel):
    """Public representation of a message.

    Attributes:
        id: UUID of the message.
        conversation_id: UUID of the parent conversation.
        role: Message role string.
        content: Message body text.
        tool_calls: Optional tool call data.
        token_count: Token count.
        created_at: Timestamp of creation.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    role: str
    content: str
    tool_calls: Optional[list[dict]] = None
    token_count: int
    created_at: datetime
