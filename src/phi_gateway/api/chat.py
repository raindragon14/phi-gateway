import json
import logging
import time
import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from phi_gateway.core.cost_tracker import calculate_cost
from phi_gateway.core.llm_proxy import route_chat_stream
from phi_gateway.database import get_db
from phi_gateway.dependencies import get_api_key
from phi_gateway.models.api_key import ApiKey
from phi_gateway.models.llm_request import LLMRequest
from phi_gateway.schemas.chat import ChatCompletionRequest
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

    Args:
        body: Validated chat completion request body.
        api_key: Authenticated API key (from dependency injection).
        db: Async database session (from dependency injection).

    Returns:
        ``ChatCompletionResponse`` for non-streaming, or a
        ``StreamingResponse`` with SSE events for streaming.
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
    """Handle streaming chat completion via Server-Sent Events.

    Tracks token usage from SSE events and persists cost/usage
    logging when the stream completes.

    Args:
        body: Validated chat completion request body.
        api_key: Authenticated API key.
        db: Async database session.

    Returns:
        A ``StreamingResponse`` with ``text/event-stream`` media type.
    """

    async def _log_stream_result(
        input_tokens: int,
        output_tokens: int,
        latency_ms: int,
        status: str,
        error_message: str | None = None,
    ) -> None:
        """Write an LLMRequest log entry for the stream.

        Args:
            input_tokens: Number of prompt tokens consumed.
            output_tokens: Number of completion tokens generated.
            latency_ms: Round-trip latency in milliseconds.
            status: ``"success"`` or ``"error"``.
            error_message: Optional error detail for failed streams.
        """
        cost_micro = calculate_cost(body.model, input_tokens, output_tokens)
        log_entry = LLMRequest(
            id=uuid.uuid4(),
            api_key_id=api_key.id,
            provider="unknown",
            model=body.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd_micro=cost_micro,
            latency_ms=latency_ms,
            status=status,
            error_message=error_message,
        )
        db.add(log_entry)
        await db.commit()

    async def event_generator():
        """Yield SSE events from the LLM stream and log usage on completion."""
        input_tokens = 0
        output_tokens = 0
        start = time.perf_counter()
        error_message: str | None = None

        try:
            async for sse_event in route_chat_stream(
                model=body.model,
                messages=[m.model_dump() for m in body.messages],
                temperature=body.temperature,
                max_tokens=body.max_tokens,
                tools=body.tools,
            ):
                if sse_event:
                    # Extract token usage from SSE events (OpenAI
                    # sends usage as the final chunk when
                    # stream_options={"include_usage": True})
                    if sse_event.startswith("data: ") and not sse_event.startswith("data: [DONE]"):
                        try:
                            data = json.loads(sse_event.removeprefix("data: ").strip())
                            usage = data.get("usage")
                            if usage:
                                input_tokens = usage.get("prompt_tokens", input_tokens) or input_tokens
                                output_tokens = usage.get("completion_tokens", output_tokens) or output_tokens
                        except (json.JSONDecodeError, KeyError):
                            pass
                    yield sse_event
        except ValueError as e:
            error_message = str(e)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        except Exception as e:
            logger.exception("Streaming error")
            error_message = str(e)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            latency_ms = int((time.perf_counter() - start) * 1000)
            await _log_stream_result(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                status="error" if error_message else "success",
                error_message=error_message,
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
