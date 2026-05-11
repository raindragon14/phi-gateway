import json
import logging
import uuid
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from phi_gateway.models.api_key import ApiKey
from phi_gateway.models.tool import ToolDefinition
from phi_gateway.schemas.tools import CreateToolRequest, ToolCallRequest, ToolResponse

logger = logging.getLogger(__name__)


async def create_tool(
    body: CreateToolRequest,
    api_key: ApiKey,
    db: AsyncSession,
) -> ToolResponse:
    """Register a new tool definition."""
    # Check name uniqueness
    existing = await db.execute(
        select(ToolDefinition).where(ToolDefinition.name == body.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tool with name '{body.name}' already exists",
        )

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
    """List all active tools."""
    result = await db.execute(
        select(ToolDefinition).where(ToolDefinition.is_active == True).order_by(ToolDefinition.name)
    )
    tools = result.scalars().all()
    return [ToolResponse.model_validate(t) for t in tools]


async def get_tool_schema(tool_id: UUID, db: AsyncSession) -> dict:
    """Get the JSON Schema for a specific tool."""
    tool = await _get_active_tool(tool_id, db)
    return tool.json_schema


async def call_tool(
    tool_id: UUID,
    body: ToolCallRequest,
    api_key: ApiKey,
    db: AsyncSession,
) -> dict:
    """Execute a tool by proxying the call to its endpoint."""
    tool = await _get_active_tool(tool_id, db)

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
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Tool '{tool.name}' timed out after 30s",
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Tool '{tool.name}' returned error: {e.response.status_code}",
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not reach tool '{tool.name}': {e}",
        )


async def _get_active_tool(tool_id: UUID, db: AsyncSession) -> ToolDefinition:
    """Fetch an active tool by ID or raise 404."""
    result = await db.execute(
        select(ToolDefinition).where(
            ToolDefinition.id == tool_id,
            ToolDefinition.is_active == True,
        )
    )
    tool = result.scalar_one_or_none()
    if tool is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found",
        )
    return tool


def _validate_params(params: dict, schema: dict) -> None:
    """Validate params against JSON Schema (basic — just checks required fields).

    Phase 2 improvement: use `jsonschema` library for full validation.
    """
    required = schema.get("required", [])
    for field in required:
        if field not in params:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required parameter: '{field}'",
            )
