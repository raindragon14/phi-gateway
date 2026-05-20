"""Agent memory models — conversations and messages for persistent chat sessions.

Provides structured storage for multi-turn agent conversations with
tool call history and token tracking.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from phi_gateway.models.base import Base


class Conversation(Base):
    """A named conversation session tied to an API key.

    Conversations group messages together and track a session ID
    for client-side correlation. Titles can be set manually or
    auto-generated.

    Attributes:
        id: UUID primary key.
        api_key_id: Foreign key to the owning API key.
        session_id: Client-specified session identifier string.
        title: Optional human-readable title.
        created_at: Timestamp of conversation creation (server default).
        updated_at: Timestamp of last message or metadata change.
    """

    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    api_key_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("api_keys.id"), nullable=False
    )
    session_id: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class Message(Base):
    """A single message within a conversation.

    Supports all chat roles (user, assistant, system, tool) and
    can store tool call JSON and token consumption metadata.

    Attributes:
        id: UUID primary key.
        conversation_id: Foreign key to the parent conversation.
        role: Message role — ``"user"``, ``"assistant"``, ``"system"``,
            or ``"tool"``.
        content: Message body text.
        tool_calls: Optional JSON array of tool call objects.
        token_count: Number of tokens consumed by this message.
        created_at: Timestamp of message creation (server default).
    """

    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("conversations.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tool_calls: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
