"""LLM request log model for usage tracking, cost monitoring, and audit.

Every chat completion is logged here with token counts, cost
(in micro-USD), latency, and provider/model identifiers.
"""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from phi_gateway.models.base import Base


class LLMRequest(Base):
    """Audit log entry for a single LLM request.

    Records the provider, model, token usage, cost (in micro-USD
    for precision without floats), latency, and success/error
    status. Linked to the API key that made the request.

    Attributes:
        id: UUID primary key.
        api_key_id: Foreign key to the API key that made the request.
        provider: Provider slug (``"openai"``, ``"anthropic"``,
            ``"groq"``, ``"openrouter"``).
        model: Full model identifier string.
        input_tokens: Number of prompt tokens consumed.
        output_tokens: Number of completion tokens generated.
        cost_usd_micro: Total cost in micro-USD (cents × 10).
        latency_ms: Round-trip latency in milliseconds.
        status: ``"success"`` or ``"error"``.
        error_message: Optional error detail for failed requests.
        created_at: Timestamp of the request (server default).
    """

    __tablename__ = "llm_requests"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    api_key_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("api_keys.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_usd_micro: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="success")
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
