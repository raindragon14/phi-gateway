import logging

logger = logging.getLogger(__name__)

# Cost per 1M tokens: (input_price_usd, output_price_usd)
COST_PER_1M_TOKENS: dict[str, tuple[float, float]] = {
    # OpenAI
    "gpt-5-nano": (0.05, 0.40),
    "gpt-5-mini": (0.25, 2.00),
    "gpt-5.2": (1.75, 14.00),
    "gpt-4.1": (2.00, 8.00),
    "gpt-4.1-nano": (0.10, 0.40),
    # Anthropic
    "claude-haiku-4.5": (1.00, 5.00),
    "claude-sonnet-4.6": (3.00, 15.00),
    "claude-opus-4.6": (5.00, 25.00),
    # Groq (free tier has zero cost, but include estimates for paid)
    "llama-3.3-70b": (0.59, 0.79),
    "llama-4-scout": (0.10, 0.20),
    "deepseek-r1-distill-llama-70b": (0.75, 0.99),
    # OpenRouter — key models (prices are OpenRouter pass-through rates)
    "mistral-medium-3-5": (2.00, 6.00),
    "mistral-large-3": (2.00, 6.00),
    "gpt-5-mini": (0.25, 2.00),
    "claude-sonnet-4.6": (3.00, 15.00),
    "gemini-2.5-flash": (0.15, 0.60),
    "deepseek-r1": (0.55, 2.19),
}


def _lookup_model(model: str) -> tuple[float, float] | None:
    """Look up pricing for a model, trying exact match then suffix match."""
    prices = COST_PER_1M_TOKENS.get(model)
    if prices:
        return prices

    # Try matching the last segment after "/" (e.g. "groq/llama-3.3-70b" → "llama-3.3-70b")
    if "/" in model:
        short = model.rsplit("/", 1)[-1]
        prices = COST_PER_1M_TOKENS.get(short)
        if prices:
            return prices

    return None


def calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> int:
    """Calculate the cost of an LLM request in micro-dollars.

    Returns cost as ``int`` in micro-dollars (1 micro-dollar = 0.000001 USD).
    Returns 0 if the model is unknown (logs a warning).
    """
    prices = _lookup_model(model)

    if prices is None:
        logger.warning("Unknown model '%s' for cost calculation — returning 0", model)
        return 0

    input_price, output_price = prices

    cost = (input_tokens * input_price + output_tokens * output_price) / 1_000_000
    # Convert to micro-dollars (1 USD = 1,000,000 micro-dollars)
    return int(cost * 1_000_000)
