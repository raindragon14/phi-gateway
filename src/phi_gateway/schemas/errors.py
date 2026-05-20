"""Standard error response schema for all API endpoints.

Provides a consistent machine-readable error envelope across the
entire API surface, replacing ad-hoc ``{"detail": "..."}`` responses
from HTTPException.
"""

from typing import Any

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Standard error response body.

    Every API error returns this shape, making it predictable for
    API clients and agent consumers to parse.

    Attributes:
        detail: Human-readable error description.
        code: Machine-readable error code (e.g. ``"NOT_FOUND"``,
            ``"RATE_LIMIT_EXCEEDED"``). Optional.
        id: Optional request ID for log correlation.
        context: Optional dict with additional error-specific fields
            (e.g. which resource was missing, which tier was required).
    """

    detail: str
    code: str | None = None
    id: str | None = None
    context: dict[str, Any] | None = None


# ── Standard error codes ──────────────────────────────────────────

NOT_FOUND = "NOT_FOUND"
CONFLICT = "CONFLICT"
VALIDATION_ERROR = "VALIDATION_ERROR"
RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
UNAUTHORIZED = "UNAUTHORIZED"
FORBIDDEN = "FORBIDDEN"
BAD_GATEWAY = "BAD_GATEWAY"
GATEWAY_TIMEOUT = "GATEWAY_TIMEOUT"
INTERNAL_ERROR = "INTERNAL_ERROR"
