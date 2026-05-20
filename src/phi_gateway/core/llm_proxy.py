"""Multi-provider LLM routing with fallback chains."""

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

# ── Client cache (reuse connection pools across requests) ──────────

_client_cache: dict[str, AsyncOpenAI | AsyncAnthropic | AsyncGroq] = {}

# ── Fallback chain ─────────────────────────────────────────────────

FALLBACK_CHAIN: dict[str, list[str]] = {
    "anthropic/": ["openai/gpt-5.2", "groq/llama-3.3-70b"],
    "openai/": ["groq/llama-3.3-70b", "openrouter/mistral-medium-3-5"],
    "groq/": ["openai/gpt-5-mini", "openrouter/gemini-2.5-flash"],
    "openrouter/": ["openai/gpt-5.2", "anthropic/claude-sonnet-4.6"],
}

ModelInfo = dict  # {"id": str, "provider": str, ...}


# ── Client management ──────────────────────────────────────────────


def _get_client(provider: str) -> AsyncOpenAI | AsyncAnthropic | AsyncGroq:
    """Return (or create and cache) the async SDK client for a provider.

    Args:
        provider: Provider slug (``"openai"``, ``"anthropic"``,
            ``"groq"``, or ``"openrouter"``).

    Returns:
        An async client instance.

    Raises:
        ValueError: If the provider is not recognized.
        RuntimeError: If the provider's API key is not configured.
    """
    if provider in _client_cache:
        return _client_cache[provider]

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
        logger.error("Provider '%s' not configured: missing %s", provider, env_key)
        raise RuntimeError(f"Provider '{provider}' is not available")

    if base_url:
        client = client_cls(api_key=api_key, base_url=base_url)
    else:
        client = client_cls(api_key=api_key)

    _client_cache[provider] = client
    return client


# ── Request translation helpers ─────────────────────────────────────


def _parse_model(model_str: str) -> tuple[str, str]:
    """Parse a model string into (provider, model_name).

    Accepts formats:
        - ``groq/llama-3.3-70b`` -> ``("groq", "llama-3.3-70b")``
        - ``gpt-5-mini`` -> ``("openai", "gpt-5-mini")`` (lookup)

    Args:
        model_str: Model identifier in ``provider/name`` or bare name
            format.

    Returns:
        Tuple of ``(provider, model_name)``.

    Raises:
        ValueError: If the provider or model is not recognized.
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

    known_providers = {"openai", "anthropic", "groq", "openrouter"}
    if provider not in known_providers:
        raise ValueError(f"Unknown provider '{provider}'. Valid providers: {', '.join(sorted(known_providers))}")

    return provider, model_name


def _split_system_message(messages: list[dict]) -> tuple[str | None, list[dict]]:
    """Extract the last system message from the message list.

    Anthropic uses a separate ``system`` parameter instead of a
    system-role message.

    Args:
        messages: List of message dicts in OpenAI format.

    Returns:
        Tuple of ``(system_content, non_system_messages)``. The first
        element is ``None`` if no system message is present.
    """
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

    Handles providers that return content as a list of blocks
    (e.g. Anthropic).

    Args:
        msg: A message dict with ``role`` and ``content`` keys.

    Returns:
        A new message dict with ``content`` guaranteed to be a string.
    """
    content = msg.get("content", "")
    if isinstance(content, list):
        texts = [b.get("text", "") for b in content if b.get("type") == "text"]
        msg = {**msg, "content": "\n".join(texts)}
    return msg


# ── Request building ────────────────────────────────────────────────


def _get_fallbacks(model: str) -> list[str]:
    """Get fallback models for a given primary model.

    Args:
        model: The primary model identifier.

    Returns:
        List of fallback model identifiers (empty if none configured).
    """
    for prefix, alt_models in FALLBACK_CHAIN.items():
        if model.startswith(prefix):
            return alt_models
    return []


def _build_request_kwargs(
    provider: str,
    messages: list[dict],
    temperature: float,
    max_tokens: int | None,
    tools: list[dict] | None,
) -> dict:
    """Build provider-specific kwargs for chat.completions.create().

    Args:
        provider: Provider slug.
        messages: Message list in OpenAI format.
        temperature: Sampling temperature.
        max_tokens: Optional token cap.
        tools: Optional tool definitions.

    Returns:
        Dict ready to unpack into ``client.chat.completions.create()``.
    """
    kwargs: dict = {"temperature": temperature}

    if max_tokens:
        kwargs["max_tokens"] = max_tokens

    # Message format
    if provider == "anthropic":
        kwargs.update(_anthropic_messages(messages))
    else:
        kwargs.update(_openai_messages(messages))

    # Tool format
    if tools:
        if provider == "anthropic":
            kwargs["tools"] = [
                {
                    "name": t["function"]["name"],
                    "description": t["function"].get("description", ""),
                    "input_schema": t["function"]["parameters"],
                }
                for t in tools
            ]
        else:
            kwargs["tools"] = tools

    return kwargs


def _openai_messages(messages: list[dict]) -> dict:
    """Prepare messages for OpenAI-compatible providers.

    Args:
        messages: List of message dicts.

    Returns:
        Dict with a single ``"messages"`` key suitable for
        ``client.chat.completions.create(**kwargs)``.
    """
    return {"messages": [_to_openai_message(m) for m in messages]}


def _anthropic_messages(messages: list[dict]) -> dict:
    """Prepare messages for Anthropic: separate system param, max_tokens required.

    Args:
        messages: List of message dicts in OpenAI format.

    Returns:
        Dict with ``"messages"``, ``"max_tokens"``, and optionally
        ``"system"`` keys for Anthropic's API.
    """
    system, non_system = _split_system_message(messages)
    result: dict = {
        "messages": non_system,
        "max_tokens": 4096,
    }
    if system:
        result["system"] = system
    return result


# ── Response translation ───────────────────────────────────────────


def _translate_response(response, model: str, provider: str) -> dict:
    """Translate any provider response to our standard OpenAI format.

    Args:
        response: Raw SDK response object.
        model: The model identifier string used for the request.
        provider: The provider slug.

    Returns:
        A dict matching the standard ``ChatCompletionResponse`` shape.
    """
    if provider == "anthropic":
        return _anthropic_to_openai(response, model, provider)
    return _openai_to_openai(response, model, provider)


def _openai_to_openai(response, model: str, provider: str) -> dict:
    """Normalize an OpenAI-compatible response to our standard format.

    Args:
        response: Raw SDK response object from ``AsyncOpenAI``.
        model: The model identifier string used for the request.
        provider: The provider slug.

    Returns:
        A dict matching the standard ``ChatCompletionResponse`` shape.
    """
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
    """Translate an Anthropic response to OpenAI format.

    Args:
        response: Raw SDK response object from ``AsyncAnthropic``.
        model: The model identifier string used for the request.
        provider: The provider slug (``"anthropic"``).

    Returns:
        A dict matching the standard ``ChatCompletionResponse`` shape.
    """
    content_text = ""
    for block in response.content:
        if block.type == "text":
            content_text += block.text

    input_tokens = response.usage.input_tokens if response.usage else 0
    output_tokens = response.usage.output_tokens if response.usage else 0

    return {
        "id": response.id,
        "object": "chat.completion",
        "created": 0,
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


# ── Chat completion ────────────────────────────────────────────────


async def route_chat(
    model: str,
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: int | None = None,
    tools: list[dict] | None = None,
) -> dict:
    """Route a chat completion request to the appropriate LLM provider.

    Returns a dict matching OpenAI's ``ChatCompletionResponse`` shape.
    On provider failure, automatically falls back to alternative
    models defined in ``FALLBACK_CHAIN``.

    Args:
        model: Full model identifier (e.g. ``"groq/llama-3.3-70b"``).
        messages: List of message dicts in OpenAI format.
        temperature: Sampling temperature (0-2, default 0.7).
        max_tokens: Optional cap on completion tokens.
        tools: Optional list of tool/function definitions in OpenAI
            format.

    Returns:
        A dict with keys ``id``, ``object``, ``created``, ``model``,
        ``choices``, ``usage``, and ``provider``.

    Raises:
        ValueError: If the model/provider is not recognized.
        RuntimeError: If the provider's API key is not configured.
        httpx.HTTPStatusError: If all fallback attempts fail.
    """
    models_to_try = [model] + _get_fallbacks(model)
    last_error: Exception | None = None

    for attempt_idx, candidate_model in enumerate(models_to_try):
        try:
            provider, model_name = _parse_model(candidate_model)
            client = _get_client(provider)
            kwargs = _build_request_kwargs(provider, messages, temperature, max_tokens, tools)
            kwargs["model"] = model_name

            response = await client.chat.completions.create(**kwargs)  # type: ignore[union-attr]
            return _translate_response(response, candidate_model, provider)

        except (
            httpx.HTTPStatusError,
            httpx.TimeoutException,
            httpx.ConnectError,
            OpenAIAPIError,
            AnthropicAPIError,
            ValueError,
        ) as exc:
            last_error = exc
            next_model = models_to_try[attempt_idx + 1] if attempt_idx + 1 < len(models_to_try) else None
            if next_model:
                logger.warning("Provider %s failed (%s), falling back to %s", candidate_model, exc, next_model)
            else:
                logger.warning("Provider %s failed (%s), no more fallbacks", candidate_model, exc)
            continue

    raise last_error  # type: ignore[misc]


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

    Args:
        model: Full model identifier (e.g. ``"groq/llama-3.3-70b"``).
        messages: List of message dicts in OpenAI format.
        temperature: Sampling temperature (0-2, default 0.7).
        max_tokens: Optional cap on completion tokens.
        tools: Optional list of tool/function definitions.

    Yields:
        SSE-formatted strings. The final yield is always
        ``data: [DONE]\n\n``.
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

    yield "data: [DONE]\n\n"


def _openai_stream_chunk(chunk, model: str, provider: str) -> str:
    """Format an OpenAI streaming chunk as SSE.

    When ``stream_options={"include_usage": True}`` is set, the
    final chunk carries usage data with empty choices.

    Args:
        chunk: A single streaming chunk from the SDK.
        model: The model identifier string.
        provider: The provider slug.

    Returns:
        An SSE-formatted string, or an empty string if the chunk
        has no content.
    """
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
    """Format an Anthropic streaming event as OpenAI-compatible SSE.

    Args:
        event: A single streaming event from the Anthropic SDK.

    Returns:
        An SSE-formatted string, or an empty string for events
        that don't map to content (e.g. ``message_stop``).
    """
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
    """Return all known models regardless of whether providers are configured.

    Returns:
        List of model info dicts with keys ``id``, ``provider``,
        ``pricing``, and ``context_window``.
    """
    return KNOWN_MODELS
