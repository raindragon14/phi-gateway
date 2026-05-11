import json
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from phi_gateway.core.llm_proxy import route_chat_stream
from phi_gateway.database import get_db
from phi_gateway.dependencies import get_api_key
from phi_gateway.models.api_key import ApiKey
from phi_gateway.schemas.chat import ChatCompletionRequest, ChatCompletionResponse
from phi_gateway.services.llm_service import chat_completion

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["LLM Proxy"])


@router.post("/chat/completions")
async def create_chat_completion(
    body: ChatCompletionRequest,
    api_key: ApiKey = Depends(get_api_key),
    db: AsyncSession = Depends(get_db),
):
    """OpenAI-compatible chat completions endpoint.

    Supports both streaming (SSE) and non-streaming responses.
    Routes to the appropriate provider based on the model name.
    """
    if body.stream:
        return await _stream_chat(body, api_key, db)

    response = await chat_completion(body, api_key, db)
    return response


async def _stream_chat(
    body: ChatCompletionRequest,
    api_key: ApiKey,
    db: AsyncSession,
) -> StreamingResponse:
    """Handle streaming chat completion via Server-Sent Events."""

    async def event_generator():
        try:
            async for sse_event in route_chat_stream(
                model=body.model,
                messages=[m.model_dump() for m in body.messages],
                temperature=body.temperature,
                max_tokens=body.max_tokens,
                tools=body.tools,
            ):
                if sse_event:
                    yield sse_event
            # The stream is finished by route_chat_stream sending data: [DONE]
        except ValueError as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        except Exception as e:
            logger.exception("Streaming error")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
