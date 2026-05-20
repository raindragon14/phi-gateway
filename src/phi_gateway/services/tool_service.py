"""External tool registration, discovery, validation, and HTTP proxying."""

import logging
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from phi_gateway.core.exceptions import (
    ConflictError,
    ExternalToolError,
    ExternalToolTimeoutError,
    NotFoundError,
    ValidationError,
)
from phi_gateway.core.url_safety import validate_endpoint_url
from phi_gateway.models.api_key import ApiKey
from phi_gateway.models.tool import ToolDefinition
from phi_gateway.schemas.tools import CreateToolRequest, ToolCallRequest, ToolResponse

logger = logging.getLogger(__name__)


async def create_tool(
    body: CreateToolRequest,
    api_key: ApiKey,
    db: AsyncSession,
) -> ToolResponse:
    """Register a new tool definition.

    Args:
        body: Request body with name, description, schema, endpoint,
            and auth type.
        api_key: The authenticated API key owning the tool.
        db: Async database session.

    Returns:
        The newly created ``ToolResponse``.

    Raises:
        ConflictError: If a tool with the same name already exists.
        ValidationError: If the endpoint URL is invalid or resolved
            to a private network.
    """
    # Validate endpoint URL (SSRF prevention)
    try:
        validate_endpoint_url(body.endpoint)
    except ValueError as e:
        raise ValidationError(f"Invalid endpoint URL: {e}")

    # Check name uniqueness
    existing = await db.execute(
        select(ToolDefinition).where(ToolDefinition.name == body.name)
    )
    if existing.scalar_one_or_none():
        raise ConflictError("Tool", body.name)

    tool = ToolDefinition(
        name=body.name,
        description=body.description,
        json_schema=body.json_schema,
        endpoint=body.endpoint,
        auth_type=body.auth_type,
        owner_api_key_id=api_key.id,
    )
    db.add(tool)
    await db.commit()
    await db.refresh(tool)
    return ToolResponse.model_validate(tool)


async def list_tools(db: AsyncSession) -> list[ToolResponse]:
    """List all active tools.

    Args:
        db: Async database session.

    Returns:
        List of ``ToolResponse`` ordered by name.
    """
    result = await db.execute(
        select(ToolDefinition).where(ToolDefinition.is_active.is_(True)).order_by(ToolDefinition.name)
    )
    tools = result.scalars().all()
    return [ToolResponse.model_validate(t) for t in tools]


async def get_tool_schema(tool_id: UUID, db: AsyncSession) -> dict:
    """Get the JSON Schema for a specific tool.

    Args:
        tool_id: UUID of the tool.
        db: Async database session.

    Returns:
        The tool's JSON Schema dictionary.

    Raises:
        NotFoundError: If the tool is not found or is inactive.
    """
    tool = await _get_active_tool(tool_id, db)
    return tool.json_schema


async def call_tool(
    tool_id: UUID,
    body: ToolCallRequest,
    api_key: ApiKey,
    db: AsyncSession,
) -> dict:
    """Execute a tool by proxying the call to its registered endpoint.

    Validates required parameters against the tool's JSON Schema
    before forwarding the request.

    Args:
        tool_id: UUID of the tool to invoke.
        body: Request body with method and params.
        api_key: The authenticated API key.
        db: Async database session.

    Returns:
        The JSON response from the tool's endpoint.

    Raises:
        NotFoundError: If the tool is not found or is inactive.
        ValidationError: If required parameters are missing or the
            endpoint URL is invalid.
        ExternalToolError: If the tool endpoint returns an error or
            is unreachable.
        ExternalToolTimeoutError: If the tool endpoint times out (30s).
    """
    tool = await _get_active_tool(tool_id, db)

    # Validate endpoint URL (SSRF prevention — also checks tools
    # registered before this validation existed)
    try:
        validate_endpoint_url(tool.endpoint)
    except ValueError as e:
        raise ValidationError(f"Tool endpoint '{tool.name}' is invalid: {e}")

    # Validate params against schema (basic check)
    if tool.json_schema:
        _validate_params(body.params, tool.json_schema)

    # Proxy the call
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                tool.endpoint,
                json={"method": body.method, "params": body.params},
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        raise ExternalToolTimeoutError(tool.name)
    except httpx.HTTPStatusError as e:
        raise ExternalToolError(tool.name, e.response.status_code, str(e))
    except httpx.RequestError as e:
        raise ExternalToolError(tool.name, None, f"Could not reach endpoint: {e}")


async def _get_active_tool(tool_id: UUID, db: AsyncSession) -> ToolDefinition:
    """Fetch an active tool by ID or raise 404.

    Args:
        tool_id: UUID of the tool.
        db: Async database session.

    Returns:
        The ``ToolDefinition`` instance.

    Raises:
        NotFoundError: If the tool is not found or is inactive.
    """
    result = await db.execute(
        select(ToolDefinition).where(
            ToolDefinition.id == tool_id,
            ToolDefinition.is_active.is_(True),
        )
    )
    tool = result.scalar_one_or_none()
    if tool is None:
        raise NotFoundError("Tool", str(tool_id))
    return tool


def _validate_params(params: dict, schema: dict) -> None:
    """Validate params against JSON Schema (basic — checks required fields only).

    Args:
        params: Parameters provided by the caller.
        schema: JSON Schema dict with a ``"required"`` key.

    Raises:
        ValidationError: If a required field is missing.

    Note:
        Phase 2 improvement: use ``jsonschema`` library for full
        validation.
    """
    required = schema.get("required", [])
    for field in required:
        if field not in params:
            raise ValidationError(f"Missing required parameter: '{field}'")
