"""Domain exceptions for the service layer.

Services raise these exceptions instead of ``HTTPException`` to
decouple business logic from the web framework. The API layer
catches them and maps to appropriate HTTP status codes.
"""


class GatewayError(Exception):
    """Base exception for all domain errors."""


class NotFoundError(GatewayError):
    """Requested resource does not exist or is not owned by the caller.

    Attributes:
        resource: Human-readable resource type (e.g. ``"Knowledge base"``).
        identifier: Optional resource identifier string.
    """

    def __init__(self, resource: str, identifier: str | None = None) -> None:
        """Initialize with resource type and optional identifier."""
        self.resource = resource
        self.identifier = identifier
        msg = f"{resource} not found"
        if identifier:
            msg = f"{resource} '{identifier}' not found"
        super().__init__(msg)


class ConflictError(GatewayError):
    """Resource already exists (name/identifier collision).

    Attributes:
        resource: Human-readable resource type.
        identifier: The conflicting identifier.
    """

    def __init__(self, resource: str, identifier: str) -> None:
        """Initialize with resource type and conflicting identifier."""
        self.resource = resource
        self.identifier = identifier
        super().__init__(f"{resource} '{identifier}' already exists")


class ValidationError(GatewayError):
    """Input validation failed.

    Attributes:
        detail: Human-readable error description.
    """

    def __init__(self, detail: str) -> None:
        """Initialize with validation error detail."""
        self.detail = detail
        super().__init__(detail)


class ExternalToolError(GatewayError):
    """Tool endpoint failed during proxy invocation.

    Attributes:
        tool_name: Name of the tool that failed.
        status_code: HTTP status code returned by the tool, if any.
        message: Human-readable error description.
    """

    def __init__(self, tool_name: str, status_code: int | None, message: str) -> None:
        """Initialize with tool name, optional status code, and message."""
        self.tool_name = tool_name
        self.status_code = status_code
        self.message = message
        super().__init__(f"Tool '{tool_name}' error: {message}")


class ExternalToolTimeoutError(ExternalToolError):
    """Tool endpoint timed out."""

    def __init__(self, tool_name: str) -> None:
        """Initialize with tool name (status=504, 30s timeout)."""
        super().__init__(tool_name, 504, "timed out after 30s")


class RateLimitExceededError(GatewayError):
    """Rate limit was exceeded.

    Attributes:
        limit: The rate limit that was hit.
        window: The time window string (``"minute"`` or ``"day"``).
        retry_after: Seconds until the limit resets.
    """

    def __init__(self, limit: int, window: str, retry_after: int) -> None:
        """Initialize with limit, time window, and retry-after seconds."""
        self.limit = limit
        self.window = window
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded: {limit} req/{window}")
