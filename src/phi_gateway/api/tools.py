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
    """Register a new tool."""
    return await create_tool(body, api_key, db)


@router.get("", response_model=list[ToolResponse])
async def list_tools_endpoint(
    db: AsyncSession = Depends(get_db),
):
    """List all available tools (agent-discoverable)."""
    return await list_tools(db)


@router.get("/{tool_id}/schema")
async def get_tool_schema_endpoint(
    tool_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get JSON Schema for a specific tool."""
    return await get_tool_schema(tool_id, db)


@router.post("/{tool_id}/call", response_model=ToolCallResponse)
async def call_tool_endpoint(
    tool_id: UUID,
    body: ToolCallRequest,
    api_key: ApiKey = Depends(get_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Execute a tool by proxying to its endpoint."""
    response = await call_tool(tool_id, body, api_key, db)
    return ToolCallResponse(result=response)
