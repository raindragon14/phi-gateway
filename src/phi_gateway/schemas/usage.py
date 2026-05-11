from pydantic import BaseModel


class ProviderBreakdown(BaseModel):
    provider: str
    requests: int
    cost_usd: float


class ModelBreakdown(BaseModel):
    model: str
    requests: int
    cost_usd: float


class UsageResponse(BaseModel):
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float
    by_provider: list[ProviderBreakdown]
    by_model: list[ModelBreakdown]
