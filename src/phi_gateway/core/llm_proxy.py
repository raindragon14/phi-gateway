import json
import logging
from collections.abc import AsyncGenerator

import httpx
from anthropic import APIError as AnthropicAPIError
from anthropic import AsyncAnthropic
from groq import AsyncGroq
from openai import APIError as OpenAIAPIError
from openai import AsyncOpenAI

from phi_gateway.config import settings
from phi_gateway.models_catalog import _MODEL_TO_PROVIDER, KNOWN_MODELS

# ── Provider registry ──────────────────────────────────────────────

logger = logging.getLogger(__name__)

# ── Fallback chain ─────────────────────────────────────────────────

FALLBACK_CHAIN: dict[str, list[str]] = {
    "anthropic/": ["openai/gpt-5.2", "groq/llama-3.3-70b"],
    "openai/": ["groq/llama-3.3-70b", "openrouter/mistral-medium-3-5"],
    "groq/": ["openai/gpt-5-mini", "openrouter/gemini-2.5-flash"],
    "openrouter/": ["openai/gpt-5.2", "anthropic/claude-sonnet-4.6"],
}

ModelInfo = dict  # {"id": str, "provider": str, ...}


def _get_client(provider: str):
    """Return the async client for the given provider."""
    registry: dict[str, tuple[type, str, str | None]] = {
        "openai": (AsyncOpenAI, "OPENAI_API_KEY", "https://api.openai.com/v1"),
        "anthropic": (AsyncAnthropic, "ANTHROPIC_API_KEY", None),
        "groq": (AsyncGroq, "GROQ_API_KEY", None),
        "openrouter": (AsyncOpenAI, "OPENROUTER_API_KEY", "https://openrouter.ai/api/v1"),
    }
    entry = registry.get(provider)
    if entry is None:
        raise ValueError(f"Unknown provider: {provider}")

    client_cls, env_key, base_url = entry
    api_key = getattr(settings, env_key, None)
    if not api_key:
        raise RuntimeError(
            f"Provider '{provider}' is not configured. "
            f"Set {env_key} in your .env file."
        )

    if base_url:
        return client_cls(api_key=api_key, base_url=base_url)
    return client_cls(api_key=api_key)


# ── Request translation helpers ─────────────────────────────────────

def _parse_model(model_str: str) -> tuple[str, str]:
    """Parse model string into (provider, model_name).

    Accepts formats:
        - ``groq/llama-3.3-70b`` → (groq, llama-3.3-70b)
        - ``gpt-5-mini`` → (openai, gpt-5-mini)  [lookup by known model]

    Raises ValueError if the provider or model is not recognized.
    """
    if "/" in model_str:
        parts = model_str.split("/", 1)
        provider = parts[0]
        model_name = parts[1]
    else:
        provider = _MODEL_TO_PROVIDER.get(model_str)
        if not provider:
            raise ValueError(
                f"Unknown model '{model_str}'. Use format 'provider/model_name' "
                f"or choose from: {', '.join(sorted(_MODEL_TO_PROVIDER))}"
            )
        model_name = model_str

    # Validate provider is one we know about
    known_providers = {"openai", "anthropic", "groq", "openrouter"}
    if provider not in known_providers:
        raise ValueError(
            f"Unknown provider '{provider}'. Valid providers: {', '.join(sorted(known_providers))}"
        )

    return provider, model_name


def _split_system_message(messages: list[dict]) -> tuple[str | None, list[dict]]:
    """Extract the last system message (Anthropic uses a separate ``system`` param)."""
    system = None
    non_system = []
    for msg in messages:
        if msg.get("role") == "system":
            system = msg["content"]
        else:
            non_system.append(msg)
    return system, non_system


def _to_openai_message(msg: dict) -> dict:
    """Normalize a message dict to basic OpenAI format (string content).

    Handles providers that return content as a list of blocks (e.g. Anthropic).
    """
    content = msg.get("content", "")
    if isinstance(content, list):
        texts = [b.get("text", "") for b in content if b.get("type") == "text"]
        msg = {**msg, "content": "\n".join(texts)}
    return msg


# ── Chat completion ────────────────────────────────────────────────

async def route_chat(
    model: str,
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: int | None = None,
    stream: bool = False,
    tools: list[dict] | None = None,
) -> dict:
    """Route a chat completion request to the appropriate LLM provider.

    Returns a dict matching OpenAI's ``ChatCompletionResponse`` shape.
    Handles non-streaming only (streaming is handled by a separate generator).
    On provider failure, automatically falls back to alternative models
    defined in FALLBACK_CHAIN.
    """
    # Build ordered list of models to try (primary + fallbacks)
    fallbacks: list[str] = []
    for prefix, alt_models in FALLBACK_CHAIN.items():
        if model.startswith(prefix):
            fallbacks = alt_models
            break

    models_to_try = [model] + fallbacks
    last_error: Exception | None = None

    for attempt_idx, candidate_model in enumerate(models_to_try):
        try:
            provider, model_name = _parse_model(candidate_model)
            client = _get_client(provider)

            kwargs: dict = {
                "model": model_name,
                "temperature": temperature,
            }

            if stream:
                kwargs["stream"] = True

            if max_tokens:
                kwargs["max_tokens"] = max_tokens

            # Per-provider adaptations
            if provider == "anthropic":
                msg_kwargs = _anthropic_messages(messages)
                kwargs.update(msg_kwargs)
            elif provider == "openai":
                msg_kwargs = _openai_messages(messages)
                kwargs.update(msg_kwargs)
            else:
                # Groq uses OpenAI-compatible format
                msg_kwargs = _openai_messages(messages)
                kwargs.update(msg_kwargs)

            # Tools passthrough (all providers)
            if tools:
                if provider == "anthropic":
                    kwargs["tools"] = [
                        {"name": t["function"]["name"], "description": t["function"].get("description", ""),
                         "input_schema": t["function"]["parameters"]}
                        for t in tools
                    ]
                else:
                    kwargs["tools"] = tools

            response = await client.chat.completions.create(**kwargs)  # type: ignore[union-attr]

            if provider == "anthropic":
                return _anthropic_to_openai(response, candidate_model, provider)
            return _openai_to_openai(response, candidate_model, provider)

        except (
            httpx.HTTPStatusError,
            httpx.TimeoutException,
            httpx.ConnectError,
            OpenAIAPIError,
            AnthropicAPIError,
            ValueError,
        ) as exc:
            last_error = exc
            next_model = (
                models_to_try[attempt_idx + 1]
                if attempt_idx + 1 < len(models_to_try)
                else None
            )
            if next_model:
                logger.warning(
                    'Provider %s failed (%s), falling back to %s',
                    candidate_model,
                    exc,
                    next_model,
                )
            else:
                logger.warning(
                    'Provider %s failed (%s), no more fallbacks',
                    candidate_model,
                    exc,
                )
            continue

    # All attempts failed — raise the last error
    raise last_error  # type: ignore[misc]


def _openai_messages(messages: list[dict]) -> dict:
    """Prepare messages for OpenAI-compatible providers."""
    return {"messages": [_to_openai_message(m) for m in messages]}


def _anthropic_messages(messages: list[dict]) -> dict:
    """Prepare messages for Anthropic — separate system param, max_tokens required."""
    system, non_system = _split_system_message(messages)
    result: dict = {
        "messages": non_system,
        "max_tokens": 4096,  # required by Anthropic, will be overridden if caller provides
    }
    if system:
        result["system"] = system
    return result


# ── Response translation ───────────────────────────────────────────

def _openai_to_openai(response, model: str, provider: str) -> dict:
    """Normalize an OpenAI-compatible response to our format."""
    choice = response.choices[0]
    return {
        "id": response.id,
        "object": "chat.completion",
        "created": int(response.created) if hasattr(response, "created") else 0,
        "model": model,
        "choices": [
            {
                "index": choice.index,
                "message": {
                    "role": choice.message.role,
                    "content": choice.message.content or "",
                },
                "finish_reason": choice.finish_reason or "stop",
            }
        ],
        "usage": {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
            "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            "total_tokens": response.usage.total_tokens if response.usage else 0,
        },
        "provider": provider,
    }


def _anthropic_to_openai(response, model: str, provider: str) -> dict:
    """Translate an Anthropic response to OpenAI format."""
    content_text = ""
    for block in response.content:
        if block.type == "text":
            content_text += block.text

    input_tokens = response.usage.input_tokens if response.usage else 0
    output_tokens = response.usage.output_tokens if response.usage else 0

    return {
        "id": response.id,
        "object": "chat.completion",
        "created": 0,  # Anthropic doesn't return a Unix timestamp
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content_text,
                },
                "finish_reason": response.stop_reason or "stop",
            }
        ],
        "usage": {
            "prompt_tokens": input_tokens,
            "completion_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
        },
        "provider": provider,
    }


# ── Streaming ──────────────────────────────────────────────────────

async def route_chat_stream(
    model: str,
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: int | None = None,
    tools: list[dict] | None = None,
) -> AsyncGenerator[str, None]:
    """Stream a chat completion, yielding SSE-formatted strings.

    Each yield produces a string like ``data: {...}\n\n``, compatible
    with the OpenAI streaming format.
    """
    provider, model_name = _parse_model(model)
    client = _get_client(provider)

    kwargs: dict = {
        "model": model_name,
        "temperature": temperature,
        "stream": True,
    }

    if max_tokens:
        kwargs["max_tokens"] = max_tokens

    if provider == "anthropic":
        system, non_system = _split_system_message(messages)
        kwargs["messages"] = non_system
        kwargs["max_tokens"] = max_tokens or 4096
        if system:
            kwargs["system"] = system
    else:
        kwargs["messages"] = [_to_openai_message(m) for m in messages]
        if provider in ("openai", "openrouter"):
            kwargs["stream_options"] = {"include_usage": True}

    if tools:
        kwargs["tools"] = tools

    stream = await client.chat.completions.create(**kwargs)  # type: ignore[union-attr]

    if provider == "anthropic":
        async for event in stream:
            yield _anthropic_stream_event(event)
    else:
        async for chunk in stream:
            event = _openai_stream_chunk(chunk, model, provider)
            if event:
                yield event

    # Signal stream completion
    yield "data: [DONE]\n\n"


def _openai_stream_chunk(chunk, model: str, provider: str) -> str:
    """Format an OpenAI streaming chunk as SSE.

    When ``stream_options={"include_usage": True}`` is set, the
    final chunk carries usage data with empty choices.
    """
    # Usage-only chunk (final chunk with stream_options)
    if not chunk.choices and chunk.usage:
        data = {
            "object": "chat.completion.chunk",
            "model": model,
            "usage": {
                "prompt_tokens": chunk.usage.prompt_tokens,
                "completion_tokens": chunk.usage.completion_tokens,
                "total_tokens": chunk.usage.total_tokens,
            },
        }
        return f"data: {json.dumps(data)}\n\n"

    choice = chunk.choices[0] if chunk.choices else None
    if choice is None:
        return ""

    delta = choice.delta
    data = {
        "id": chunk.id,
        "object": "chat.completion.chunk",
        "created": int(chunk.created) if hasattr(chunk, "created") else 0,
        "model": model,
        "choices": [
            {
                "index": choice.index,
                "delta": {
                    "role": delta.role if delta.role else None,
                    "content": delta.content if delta.content else None,
                },
                "finish_reason": choice.finish_reason,
            }
        ],
    }
    return f"data: {json.dumps(data)}\n\n"


def _anthropic_stream_event(event) -> str:
    """Format an Anthropic streaming event as OpenAI-compatible SSE."""
    event_type = event.type
    if event_type == "message_start":
        data = {
            "id": event.message.id,
            "object": "chat.completion.chunk",
            "created": 0,
            "model": event.message.model,
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant", "content": None},
                    "finish_reason": None,
                }
            ],
        }
        return f"data: {json.dumps(data)}\n\n"
    elif event_type == "content_block_delta":
        if event.delta.type == "text_delta":
            data = {
                "id": "",
                "object": "chat.completion.chunk",
                "created": 0,
                "model": "",
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": event.delta.text},
                        "finish_reason": None,
                    }
                ],
            }
            return f"data: {json.dumps(data)}\n\n"
    elif event_type == "message_stop":
        return ""
    return ""


# ── Model listing ──────────────────────────────────────────────────

def list_models() -> list[ModelInfo]:
    """Return all known models regardless of whether providers are configured."""
    return KNOWN_MODELS
