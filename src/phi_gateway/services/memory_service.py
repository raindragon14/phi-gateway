"""Conversation memory service — CRUD, pagination, and auto-trimming.

Manages persistent multi-turn agent conversations with context
window enforcement and truncation signalling.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from phi_gateway.core.exceptions import NotFoundError
from phi_gateway.models.api_key import ApiKey
from phi_gateway.models.memory import Conversation, Message
from phi_gateway.schemas.memory import (
    AddMessageRequest,
    ConversationResponse,
    CreateConversationRequest,
    MessageResponse,
)

# Context window limit — single default value.
# Per-model limits can be derived from models_catalog.MODELS if needed later.
CONTEXT_LIMIT_DEFAULT = 128_000

TRUNCATION_WARNING = "X-Context-Truncated"


async def create_conversation(
    body: CreateConversationRequest,
    api_key: ApiKey,
    db: AsyncSession,
) -> ConversationResponse:
    """Create a new conversation.

    Args:
        body: Request body with session_id and optional title.
        api_key: The authenticated API key owning the conversation.
        db: Async database session.

    Returns:
        The newly created ``ConversationResponse``.
    """
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
    """List all conversations for this API key.

    Args:
        api_key: The authenticated API key.
        db: Async database session.

    Returns:
        List of ``ConversationResponse`` ordered by most recently
        updated first.
    """
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
    """Add a message to a conversation.

    Enforces context window limits by trimming oldest messages when
    total token count exceeds the configured threshold.

    Args:
        conversation_id: UUID of the target conversation.
        body: Request body with role, content, and optional metadata.
        api_key: The authenticated API key (must own the conversation).
        db: Async database session.

    Returns:
        Tuple of ``(message_response, was_truncated)``. The second
        element is ``True`` if oldest messages were trimmed to fit
        the context window.

    Raises:
        HTTPException: 404 if the conversation does not exist or is
            not owned by the caller.
    """
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
    """Get conversation history with cursor-based pagination.

    Args:
        conversation_id: UUID of the conversation.
        api_key: The authenticated API key (must own the conversation).
        db: Async database session.
        limit: Maximum number of messages to return (default 50).
        before_id: Optional cursor — return messages older than this
            message UUID.

    Returns:
        List of ``MessageResponse`` in chronological order.

    Raises:
        HTTPException: 404 if the conversation does not exist or is
            not owned by the caller.
    """
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
    """Delete a conversation and all its messages.

    Args:
        conversation_id: UUID of the conversation to delete.
        api_key: The authenticated API key (must own the conversation).
        db: Async database session.

    Raises:
        HTTPException: 404 if the conversation does not exist or is
            not owned by the caller.
    """
    conv = await _get_owned_conversation(conversation_id, api_key, db)

    # Delete messages first
    await db.execute(
        delete(Message).where(Message.conversation_id == conversation_id),
    )
    await db.delete(conv)
    await db.commit()


async def _get_owned_conversation(
    conversation_id: UUID,
    api_key: ApiKey,
    db: AsyncSession,
) -> Conversation:
    """Fetch a conversation by ID, ensuring the caller owns it.

    Args:
        conversation_id: UUID of the conversation.
        api_key: The authenticated API key.
        db: Async database session.

    Returns:
        The ``Conversation`` instance.

    Raises:
        HTTPException: 404 if the conversation does not exist or is
            not owned by the caller.
    """
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.api_key_id == api_key.id,
        )
    )
    conv = result.scalar_one_or_none()
    if conv is None:
        raise NotFoundError("Conversation", str(conversation_id))
    return conv


async def _trim_if_needed(conv: Conversation, db: AsyncSession) -> bool:
    """Trim oldest messages if total token count exceeds context limit.

    Removes messages from the start of the conversation until usage
    drops to 80% of the limit. Always preserves the most recent
    message.

    Args:
        conv: The conversation to potentially trim.
        db: Async database session.

    Returns:
        ``True`` if any messages were removed.
    """
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conv.id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()

    total_tokens = sum(m.token_count or 0 for m in messages)
    limit = CONTEXT_LIMIT_DEFAULT

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
