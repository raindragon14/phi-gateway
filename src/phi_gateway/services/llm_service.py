"""Chat completion orchestration : request logging, cost tracking, provider routing."""

import logging
import time
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from phi_gateway.core.cost_tracker import calculate_cost
from phi_gateway.core.llm_proxy import route_chat
from phi_gateway.models.api_key import ApiKey
from phi_gateway.models.llm_request import LLMRequest
from phi_gateway.schemas.chat import (
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    UsageInfo,
)

logger = logging.getLogger(__name__)


async def _log_request(
    db: AsyncSession,
    api_key: ApiKey,
    model: str,
    provider: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: int,
    status: str,
    error_message: str | None = None,
) -> None:
    """Write an LLMRequest log entry to the database.

    Args:
        db: Async database session.
        api_key: The authenticated API key making the request.
        model: Full model identifier string.
        provider: Provider slug (``"openai"``, ``"anthropic"``, etc.).
        input_tokens: Number of prompt tokens consumed.
        output_tokens: Number of completion tokens generated.
        latency_ms: Round-trip latency in milliseconds.
        status: ``"success"`` or ``"error"``.
        error_message: Optional error detail for failed requests.
    """
    cost_micro = calculate_cost(model, input_tokens, output_tokens)
    log_entry = LLMRequest(
        id=uuid.uuid4(),
        api_key_id=api_key.id,
        provider=provider,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd_micro=cost_micro,
        latency_ms=latency_ms,
        status=status,
        error_message=error_message,
    )
    db.add(log_entry)
    await db.commit()


async def chat_completion(
    request: ChatCompletionRequest,
    api_key: ApiKey,
    db: AsyncSession,
) -> ChatCompletionResponse:
    """Execute a chat completion (non-streaming) and log the request.

    Routes the request to the appropriate LLM provider, extracts
    token usage, calculates cost, and persists the audit log entry.

    Args:
        request: Validated chat completion request body.
        api_key: The authenticated API key making the request.
        db: Async database session for logging.

    Returns:
        A ``ChatCompletionResponse`` with choices, usage, provider,
        and cost metadata.

    Raises:
        HTTPException: 400 if the model/provider is invalid.
        HTTPException: 502 if the provider returns an error or is unreachable.
    """
    start = time.perf_counter()

    def _elapsed_ms() -> int:
        """Return elapsed milliseconds since the request started."""
        return int((time.perf_counter() - start) * 1000)

    async def _log_error(provider: str, error_message: str) -> None:
        """Log a failed request to the database.

        Args:
            provider: Provider slug (usually ``"unknown"`` on error).
            error_message: Description of the failure.
        """
        await _log_request(
            db=db, api_key=api_key, model=request.model,
            provider=provider, input_tokens=0, output_tokens=0,
            latency_ms=_elapsed_ms(), status="error", error_message=error_message,
        )

    try:
        raw_response = await route_chat(
            model=request.model,
            messages=[m.model_dump() for m in request.messages],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=False,
            tools=request.tools,
        )
    except ValueError as e:
        await _log_error("unknown", str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        await _log_error("unknown", str(e))
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error in chat completion")
        await _log_error("unknown", str(e))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM provider error: {str(e)}",
        )

    latency = _elapsed_ms()

    # Extract token counts
    usage = raw_response.get("usage", {})
    input_tokens = usage.get("prompt_tokens", 0)
    output_tokens = usage.get("completion_tokens", 0)
    provider_name = raw_response.get("provider", "unknown")

    # Log success
    await _log_request(
        db=db,
        api_key=api_key,
        model=request.model,
        provider=provider_name,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency,
        status="success",
    )

    # Build response
    choices = raw_response.get("choices", [])
    cost_micro = calculate_cost(request.model, input_tokens, output_tokens)

    return ChatCompletionResponse(
        id=raw_response.get("id", ""),
        created=raw_response.get("created", 0),
        model=request.model,
        choices=[
            ChatCompletionChoice(
                index=c.get("index", 0),
                message=ChatMessage(
                    role=c.get("message", {}).get("role", "assistant"),
                    content=c.get("message", {}).get("content", ""),
                ),
                finish_reason=c.get("finish_reason", "stop"),
            )
            for c in choices
        ],
        usage=UsageInfo(
            prompt_tokens=input_tokens,
            completion_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        ),
        provider=provider_name,
        cost_usd=cost_micro / 1_000_000,
    )
