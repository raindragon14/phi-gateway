from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from phi_gateway.models.api_key import ApiKey
from phi_gateway.models.memory import Conversation, Message
from phi_gateway.schemas.memory import (
    AddMessageRequest,
    ConversationResponse,
    CreateConversationRequest,
    MessageResponse,
)

# Context window limits per model (approximate — Phase 3 improvement: use provider-specific values)
CONTEXT_LIMITS = {
    "default": 128_000,
    "gpt-5-nano": 400_000,
    "gpt-5-mini": 400_000,
    "claude-haiku-4.5": 200_000,
    "groq/llama-3.3-70b": 128_000,
}

TRUNCATION_WARNING = "X-Context-Truncated"


async def create_conversation(
    body: CreateConversationRequest,
    api_key: ApiKey,
    db: AsyncSession,
) -> ConversationResponse:
    """Create a new conversation."""
    conv = Conversation(
        api_key_id=api_key.id,
        session_id=body.session_id,
        title=body.title,
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return ConversationResponse.model_validate(conv)


async def list_conversations(
    api_key: ApiKey,
    db: AsyncSession,
) -> list[ConversationResponse]:
    """List all conversations for this API key."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.api_key_id == api_key.id)
        .order_by(Conversation.updated_at.desc())
    )
    convs = result.scalars().all()
    return [ConversationResponse.model_validate(c) for c in convs]


async def add_message(
    conversation_id: UUID,
    body: AddMessageRequest,
    api_key: ApiKey,
    db: AsyncSession,
) -> tuple[MessageResponse, bool]:
    """Add a message to a conversation. Returns (message, was_truncated)."""
    conv = await _get_owned_conversation(conversation_id, api_key, db)

    msg = Message(
        conversation_id=conv.id,
        role=body.role,
        content=body.content,
        tool_calls=body.tool_calls if body.tool_calls else None,
        token_count=body.token_count,
    )
    db.add(msg)

    # Update conversation timestamp
    conv.updated_at = datetime.now(timezone.utc)

    # Context window management (T3.3)
    was_truncated = await _trim_if_needed(conv, db)

    await db.commit()
    await db.refresh(msg)

    return MessageResponse.model_validate(msg), was_truncated


async def get_messages(
    conversation_id: UUID,
    api_key: ApiKey,
    db: AsyncSession,
    limit: int = 50,
    before_id: UUID | None = None,
) -> list[MessageResponse]:
    """Get conversation history with pagination."""
    conv = await _get_owned_conversation(conversation_id, api_key, db)

    query = (
        select(Message)
        .where(Message.conversation_id == conv.id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )

    if before_id:
        result = await db.execute(query)
        messages = result.scalars().all()
        # Filter after loading if before_id provided
        filtered = []
        found = False
        for m in reversed(messages):
            if found:
                filtered.append(m)
            if m.id == before_id:
                found = True
        messages = filtered
    else:
        result = await db.execute(query)
        messages = result.scalars().all()

    # Return in chronological order
    return [MessageResponse.model_validate(m) for m in reversed(messages)]


async def delete_conversation(
    conversation_id: UUID,
    api_key: ApiKey,
    db: AsyncSession,
) -> None:
    """Delete a conversation and all its messages."""
    conv = await _get_owned_conversation(conversation_id, api_key, db)

    # Delete messages first
    await db.execute(
        text("DELETE FROM messages WHERE conversation_id = :cid"),
        {"cid": str(conversation_id)},
    )
    await db.delete(conv)
    await db.commit()


async def _get_owned_conversation(
    conversation_id: UUID,
    api_key: ApiKey,
    db: AsyncSession,
) -> Conversation:
    """Fetch a conversation by ID, ensuring the caller owns it."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.api_key_id == api_key.id,
        )
    )
    conv = result.scalar_one_or_none()
    if conv is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conv


async def _trim_if_needed(conv: Conversation, db: AsyncSession) -> bool:
    """Trim oldest messages if total token count exceeds context limit.

    Returns True if any messages were truncated.
    """
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conv.id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()

    total_tokens = sum(m.token_count or 0 for m in messages)
    limit = CONTEXT_LIMITS.get("default", 128_000)

    if total_tokens <= limit:
        return False

    # Remove oldest messages until under 80% of limit
    trimmed = 0
    for m in messages[:-1]:  # keep the most recent message
        total_tokens -= m.token_count or 0
        await db.delete(m)
        trimmed += 1
        if total_tokens <= limit * 0.8:
            break

    return trimmed > 0
