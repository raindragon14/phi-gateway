"""Unified model and pricing catalog — single source of truth.

Both ``cost_tracker`` and ``llm_proxy`` import from here so model
names and pricing never drift apart.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelSpec:
    """Immutable specification for a single LLM model.

    Attributes:
        id: Full identifier (e.g. ``"groq/llama-3.3-70b"`` or
            ``"gpt-5-nano"``).
        provider: Provider slug (``"openai"``, ``"anthropic"``,
            ``"groq"``, ``"openrouter"``).
        context_window: Maximum context length in tokens.
        input_price_per_1m: USD cost per 1M input tokens (0 = free).
        output_price_per_1m: USD cost per 1M output tokens (0 = free).
        pricing_display: Human-readable price string, e.g.
            ``"$0.05/$0.40"`` or ``"free"``.
    """

    id: str  # full id (e.g. "groq/llama-3.3-70b" or "gpt-5-nano")
    provider: str  # "openai", "anthropic", "groq", "openrouter"
    context_window: int
    input_price_per_1m: float  # USD per 1M input tokens (0 = free)
    output_price_per_1m: float  # USD per 1M output tokens (0 = free)
    pricing_display: str  # human-readable, e.g. "$0.05/$0.40" or "free"


MODELS: list[ModelSpec] = [
    # ── OpenAI ──────────────────────────────────────────────────────
    ModelSpec("gpt-5-nano", "openai", 400_000, 0.05, 0.40, "$0.05/$0.40"),
    ModelSpec("gpt-5-mini", "openai", 400_000, 0.25, 2.00, "$0.25/$2.00"),
    ModelSpec("gpt-5.2", "openai", 400_000, 1.75, 14.00, "$1.75/$14.00"),
    ModelSpec("gpt-4.1", "openai", 1_000_000, 2.00, 8.00, "$2.00/$8.00"),
    ModelSpec("gpt-4.1-nano", "openai", 1_000_000, 0.10, 0.40, "$0.10/$0.40"),
    # ── Anthropic ───────────────────────────────────────────────────
    ModelSpec("claude-haiku-4.5", "anthropic", 200_000, 1.00, 5.00, "$1.00/$5.00"),
    ModelSpec("claude-sonnet-4.6", "anthropic", 200_000, 3.00, 15.00, "$3.00/$15.00"),
    ModelSpec("claude-opus-4.6", "anthropic", 200_000, 5.00, 25.00, "$5.00/$25.00"),
    # ── Groq ────────────────────────────────────────────────────────
    ModelSpec("groq/llama-3.3-70b", "groq", 128_000, 0.59, 0.79, "free"),
    ModelSpec("groq/llama-4-scout", "groq", 128_000, 0.10, 0.20, "free"),
    ModelSpec("groq/deepseek-r1-distill-llama-70b", "groq", 128_000, 0.75, 0.99, "free"),
    # ── OpenRouter ──────────────────────────────────────────────────
    ModelSpec("openrouter/mistralai/mistral-medium-3-5", "openrouter", 256_000, 2.00, 6.00, "$2.00/$6.00"),
    ModelSpec("openrouter/mistralai/mistral-large-3", "openrouter", 256_000, 2.00, 6.00, "$2.00/$6.00"),
    ModelSpec("openrouter/anthropic/claude-sonnet-4.6", "openrouter", 200_000, 3.00, 15.00, "$3.00/$15.00"),
    ModelSpec("openrouter/openai/gpt-5-mini", "openrouter", 400_000, 0.25, 2.00, "$0.25/$2.00"),
    ModelSpec("openrouter/google/gemini-2.5-flash", "openrouter", 1_000_000, 0.15, 0.60, "$0.15/$0.60"),
    ModelSpec("openrouter/deepseek/deepseek-r1", "openrouter", 128_000, 0.55, 2.19, "$0.55/$2.19"),
    ModelSpec("openrouter/poolside/laguna-m.1:free", "openrouter", 128_000, 0.0, 0.0, "free"),
]
"""Canonical list of all known LLM models with pricing metadata."""


# ── Lookup structures used by cost_tracker, llm_proxy, /v1/models ──

COST_PER_1M_TOKENS: dict[str, tuple[float, float]] = {
    m.id: (m.input_price_per_1m, m.output_price_per_1m) for m in MODELS
}
"""Mapping of model ID to ``(input_price, output_price)`` per 1M tokens in USD."""

KNOWN_MODELS: list[dict] = [
    {
        "id": m.id,
        "provider": m.provider,
        "pricing": m.pricing_display,
        "context_window": m.context_window,
    }
    for m in MODELS
]
"""List of model info dicts for the ``/v1/models`` endpoint."""

_MODEL_TO_PROVIDER: dict[str, str] = {m.id: m.provider for m in MODELS}
"""Mapping of model ID to provider slug (for name-only lookups)."""
