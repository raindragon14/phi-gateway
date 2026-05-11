from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CreateConversationRequest(BaseModel):
    session_id: str
    title: Optional[str] = None


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AddMessageRequest(BaseModel):
    role: str  # "user" | "assistant" | "system" | "tool"
    content: str = ""
    tool_calls: Optional[list[dict]] = None
    token_count: int = 0


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    role: str
    content: str
    tool_calls: Optional[list[dict]] = None
    token_count: int
    created_at: datetime
