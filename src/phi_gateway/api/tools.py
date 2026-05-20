"""External tool registry API — register, discovery, schema, and invocation.

Tools are registered with JSON Schema definitions and invoked
via HTTP proxy to their configured endpoints.
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from phi_gateway.database import get_db
from phi_gateway.dependencies import get_api_key
from phi_gateway.models.api_key import ApiKey
from phi_gateway.schemas.tools import (
    CreateToolRequest,
    ToolCallRequest,
    ToolCallResponse,
    ToolResponse,
)
from phi_gateway.services.tool_service import call_tool, create_tool, get_tool_schema, list_tools

router = APIRouter(prefix="/v1/tools", tags=["Tools"])


@router.post("", response_model=ToolResponse, status_code=201)
async def create_tool_endpoint(
    body: CreateToolRequest,
    api_key: ApiKey = Depends(get_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Register a new tool.

    Args:
        body: Request with name, description, schema, endpoint,
            and auth type.
        api_key: Authenticated API key (becomes the tool owner).
        db: Async database session.

    Returns:
        The newly created ``ToolResponse``.

    Raises:
        HTTPException: 409 if a tool with the same name exists.
    """
    return await create_tool(body, api_key, db)


@router.get("", response_model=list[ToolResponse])
async def list_tools_endpoint(
    db: AsyncSession = Depends(get_db),
):
    """List all available tools (agent-discoverable).

    Args:
        db: Async database session.

    Returns:
        List of ``ToolResponse`` ordered by name.
    """
    return await list_tools(db)


@router.get("/{tool_id}/schema")
async def get_tool_schema_endpoint(
    tool_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get JSON Schema for a specific tool.

    Args:
        tool_id: UUID of the tool.
        db: Async database session.

    Returns:
        The tool's JSON Schema dictionary.

    Raises:
        HTTPException: 404 if the tool is not found or is inactive.
    """
    return await get_tool_schema(tool_id, db)


@router.post("/{tool_id}/call", response_model=ToolCallResponse)
async def call_tool_endpoint(
    tool_id: UUID,
    body: ToolCallRequest,
    api_key: ApiKey = Depends(get_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Execute a tool by proxying to its endpoint.

    Args:
        tool_id: UUID of the tool to invoke.
        body: Request with method and params.
        api_key: Authenticated API key.
        db: Async database session.

    Returns:
        ``ToolCallResponse`` with the tool's result.

    Raises:
        HTTPException: 400 if required parameters are missing.
        HTTPException: 404 if the tool is not found or is inactive.
        HTTPException: 502 if the tool endpoint returns an error.
        HTTPException: 504 if the tool endpoint times out.
    """
    response = await call_tool(tool_id, body, api_key, db)
    return ToolCallResponse(result=response)
