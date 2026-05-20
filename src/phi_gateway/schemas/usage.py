"""Pydantic schemas for usage analytics and cost reporting."""

from pydantic import BaseModel


class ProviderBreakdown(BaseModel):
    """Usage metrics for a single provider.

    Attributes:
        provider: Provider slug (``"openai"``, ``"anthropic"``, etc.).
        requests: Total number of requests to this provider.
        cost_usd: Total cost in USD.
    """

    provider: str
    requests: int
    cost_usd: float


class ModelBreakdown(BaseModel):
    """Usage metrics for a single model.

    Attributes:
        model: Full model identifier string.
        requests: Total number of requests to this model.
        cost_usd: Total cost in USD.
    """

    model: str
    requests: int
    cost_usd: float


class UsageResponse(BaseModel):
    """Aggregated usage report across all providers and models.

    Attributes:
        total_requests: Total number of requests in the period.
        total_input_tokens: Total prompt tokens consumed.
        total_output_tokens: Total completion tokens generated.
        total_cost_usd: Total cost in USD.
        by_provider: Breakdown by provider.
        by_model: Breakdown by model.
    """

    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float
    by_provider: list[ProviderBreakdown]
    by_model: list[ModelBreakdown]
