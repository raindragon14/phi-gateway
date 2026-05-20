"""Per-request cost calculation using the unified model catalog."""

import logging

from phi_gateway.models_catalog import COST_PER_1M_TOKENS

logger = logging.getLogger(__name__)


def _lookup_model(model: str) -> tuple[float, float] | None:
    """Look up pricing for a model, trying exact match then suffix match.

    Args:
        model: Full model identifier (e.g. ``"groq/llama-3.3-70b"``).

    Returns:
        Tuple of ``(input_price_per_1m, output_price_per_1m)`` in USD,
        or ``None`` if the model is not in the catalog.
    """
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

    Args:
        model: Full model identifier string.
        input_tokens: Number of prompt tokens consumed.
        output_tokens: Number of completion tokens generated.

    Returns:
        Cost as an integer in micro-dollars (1 µ$ = 0.000001 USD).
        Returns 0 if the model is not in the catalog.
    """
    prices = _lookup_model(model)

    if prices is None:
        logger.warning("Unknown model '%s' for cost calculation : returning 0", model)
        return 0

    input_price, output_price = prices

    cost_usd = (input_tokens * input_price + output_tokens * output_price) / 1_000_000
    # Convert to micro-dollars (1 µ$ = 0.000001 USD), round to nearest integer
    return round(cost_usd * 1_000_000)
