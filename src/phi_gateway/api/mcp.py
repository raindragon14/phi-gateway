"""Model Context Protocol (JSON-RPC 2.0) endpoint for agent tool discovery.

Supports ``tools/list``, ``tools/call``, ``resources/list``,
and ``resources/read`` methods per the MCP specification.
"""

import logging
import uuid
from collections.abc import Callable
from typing import Any

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from phi_gateway.core.url_safety import validate_endpoint_url
from phi_gateway.database import get_db
from phi_gateway.dependencies import get_api_key
from phi_gateway.models.api_key import ApiKey
from phi_gateway.models.document import Document, KnowledgeBase
from phi_gateway.models.tool import ToolDefinition
from phi_gateway.schemas.mcp import JsonRpcRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["MCP"])


# ── Helpers ─────────────────────────────────────────────────────────


def _jsonrpc_result(request_id: str | int, result: Any) -> dict:
    """Build a JSON-RPC 2.0 success response.

    Args:
        request_id: The request ID from the original request.
        result: The result payload.

    Returns:
        A JSON-RPC 2.0 response dict.
    """
    return {"jsonrpc": "2.0", "result": result, "id": request_id}


def _jsonrpc_error(request_id: str | int, code: int, message: str) -> dict:
    """Build a JSON-RPC 2.0 error response.

    Args:
        request_id: The request ID from the original request.
        code: JSON-RPC error code.
        message: Human-readable error message.

    Returns:
        A JSON-RPC 2.0 error response dict.
    """
    return {"jsonrpc": "2.0", "error": {"code": code, "message": message}, "id": request_id}


# ── Method handlers ─────────────────────────────────────────────────


async def _handle_tools_list(body: JsonRpcRequest, db: AsyncSession) -> dict:
    """List all registered tools.

    Args:
        body: The JSON-RPC request.
        db: Async database session.

    Returns:
        JSON-RPC response with tool list.
    """
    result = await db.execute(select(ToolDefinition).order_by(ToolDefinition.name))
    tools = result.scalars().all()
    return _jsonrpc_result(
        body.id,
        [
            {
                "name": t.name,
                "description": t.description,
                "inputSchema": t.json_schema,
            }
            for t in tools
        ],
    )


async def _handle_tools_call(body: JsonRpcRequest, db: AsyncSession) -> dict:
    """Execute a registered tool by name.

    Args:
        body: The JSON-RPC request with ``params.name`` and ``params.arguments``.
        db: Async database session.

    Returns:
        JSON-RPC response with tool output or error.
    """
    tool_name = body.params.get("name", "")
    arguments = body.params.get("arguments", {})

    result = await db.execute(select(ToolDefinition).where(ToolDefinition.name == tool_name))
    tool = result.scalar_one_or_none()
    if not tool:
        return _jsonrpc_error(body.id, -32601, f"Tool '{tool_name}' not found")

    try:
        validate_endpoint_url(tool.endpoint)
    except ValueError:
        return _jsonrpc_error(body.id, -32603, f"Tool '{tool_name}' endpoint is in a blocked network")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            tool.endpoint,
            json={"method": tool_name, "params": arguments},
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()

    return _jsonrpc_result(body.id, {"content": [{"type": "text", "text": str(data)}]})


async def _handle_resources_list(body: JsonRpcRequest, db: AsyncSession) -> dict:
    """List all knowledge bases as MCP resources.

    Args:
        body: The JSON-RPC request.
        db: Async database session.

    Returns:
        JSON-RPC response with resource list.
    """
    result = await db.execute(select(KnowledgeBase).order_by(KnowledgeBase.created_at))
    kbs = result.scalars().all()
    return _jsonrpc_result(
        body.id,
        {
            "resources": [
                {
                    "uri": f"phi-kb://{kb.id}",
                    "name": kb.name,
                    "description": kb.description or "",
                    "mimeType": "application/json",
                }
                for kb in kbs
            ]
        },
    )


async def _handle_resources_read(body: JsonRpcRequest, db: AsyncSession) -> dict:
    """Read documents from a knowledge base.

    Args:
        body: The JSON-RPC request with ``params.uri`` (e.g. ``phi-kb://<uuid>``).
        db: Async database session.

    Returns:
        JSON-RPC response with document contents or error.
    """
    uri = body.params.get("uri", "")
    kb_id_str = uri.replace("phi-kb://", "").split("/")[0]

    if not kb_id_str:
        return _jsonrpc_error(body.id, -32602, "Missing or invalid URI")

    try:
        kb_uuid = uuid.UUID(kb_id_str)
    except ValueError:
        return _jsonrpc_error(body.id, -32602, f"Invalid KB ID in URI: {kb_id_str}")

    result = await db.execute(select(Document).where(Document.kb_id == kb_uuid).limit(20))
    docs = result.scalars().all()
    return _jsonrpc_result(
        body.id,
        {
            "contents": [
                {
                    "uri": f"phi-kb://{kb_id_str}/doc/{doc.id}",
                    "text": doc.content,
                    "mimeType": "text/plain",
                }
                for doc in docs
            ]
        },
    )


# ── Dispatch ────────────────────────────────────────────────────────

_METHOD_HANDLERS: dict[str, Callable] = {
    "tools/list": _handle_tools_list,
    "tools/call": _handle_tools_call,
    "resources/list": _handle_resources_list,
    "resources/read": _handle_resources_read,
}


@router.post("/mcp")
async def mcp_endpoint(
    body: JsonRpcRequest,
    api_key: ApiKey = Depends(get_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Model Context Protocol endpoint (JSON-RPC 2.0).

    Dispatches to method-specific handlers based on ``body.method``.

    Args:
        body: JSON-RPC 2.0 request with method and params.
        api_key: Authenticated API key.
        db: Async database session.

    Returns:
        JSON-RPC 2.0 response dict with ``"result"`` on success
        or ``"error"`` on failure.
    """
    handler = _METHOD_HANDLERS.get(body.method)
    if handler is None:
        return _jsonrpc_error(body.id, -32601, f"Method '{body.method}' not supported")

    try:
        return await handler(body, db)
    except Exception as e:
        logger.exception("MCP error")
        return _jsonrpc_error(body.id, -32603, str(e))
