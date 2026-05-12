from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from phi_gateway.database import get_db
from phi_gateway.dependencies import get_api_key
from phi_gateway.models.api_key import ApiKey
from phi_gateway.schemas.memory import (
    AddMessageRequest,
    ConversationResponse,
    CreateConversationRequest,
    MessageResponse,
)
from phi_gateway.services.memory_service import (
    TRUNCATION_WARNING,
    add_message,
    create_conversation,
    delete_conversation,
    get_messages,
    list_conversations,
)

router = APIRouter(prefix="/v1/memory", tags=["Agent Memory"])


@router.post("/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation_endpoint(
    body: CreateConversationRequest,
    api_key: ApiKey = Depends(get_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Create a new conversation."""
    return await create_conversation(body, api_key, db)


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations_endpoint(
    api_key: ApiKey = Depends(get_api_key),
    db: AsyncSession = Depends(get_db),
):
    """List all conversations for this API key."""
    return await list_conversations(api_key, db)


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages_endpoint(
    conversation_id: UUID,
    api_key: ApiKey = Depends(get_api_key),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    before_id: UUID | None = None,
):
    """Get conversation history."""
    return await get_messages(conversation_id, api_key, db, limit, before_id)


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse, status_code=201)
async def add_message_endpoint(
    conversation_id: UUID,
    body: AddMessageRequest,
    api_key: ApiKey = Depends(get_api_key),
    db: AsyncSession = Depends(get_db),
    response: Response = None,  # type: ignore[assignment]
):
    """Add a message to a conversation."""
    msg, was_truncated = await add_message(conversation_id, body, api_key, db)
    if was_truncated and response:
        response.headers[TRUNCATION_WARNING] = "true"
    return msg


@router.delete("/conversations/{conversation_id}")
async def delete_conversation_endpoint(
    conversation_id: UUID,
    api_key: ApiKey = Depends(get_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Delete a conversation and all its messages."""
    await delete_conversation(conversation_id, api_key, db)
    return {"status": "deleted", "id": str(conversation_id)}
