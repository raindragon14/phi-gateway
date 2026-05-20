"""Model Context Protocol (JSON-RPC 2.0) endpoint for agent tool discovery.

Supports ``tools/list``, ``tools/call``, ``resources/list``,
and ``resources/read`` methods per the MCP specification.
"""

import logging
import uuid

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from phi_gateway.core.url_safety import validate_endpoint_url
from phi_gateway.database import get_db
from phi_gateway.dependencies import get_api_key
from phi_gateway.models.api_key import ApiKey
from phi_gateway.models.document import Document, KnowledgeBase
from phi_gateway.schemas.mcp import JsonRpcRequest
from phi_gateway.services.tool_service import list_tools

logger = logging.getLogger(__name__)

router = APIRouter(tags=["MCP"])


@router.post("/mcp")
async def mcp_endpoint(
    body: JsonRpcRequest,
    api_key: ApiKey = Depends(get_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Model Context Protocol endpoint (JSON-RPC 2.0).

    Supports:
      - ``tools/list`` — list available tools
      - ``tools/call`` — execute a tool (requires auth)
      - ``resources/list`` — list available KBs
      - ``resources/read`` — search a KB

    Args:
        body: JSON-RPC 2.0 request with method and params.
        api_key: Authenticated API key.
        db: Async database session.

    Returns:
        JSON-RPC 2.0 response dict with ``"result"`` on success
        or ``"error"`` on failure.
    """
    try:
        if body.method == "tools/list":
            tools = await list_tools(db)
            result = [
                {
                    "name": t.name,
                    "description": t.description,
                    "inputSchema": t.json_schema,
                }
                for t in tools
            ]
            return {"jsonrpc": "2.0", "result": result, "id": body.id}

        elif body.method == "tools/call":
            # Requires auth — pass through to /v1/tools/{name}/call logic
            tool_name = body.params.get("name", "")
            arguments = body.params.get("arguments", {})

            # Look up tool by name
            all_tools = await list_tools(db)
            tool = next((t for t in all_tools if t.name == tool_name), None)
            if not tool:
                return {
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Tool '{tool_name}' not found"},
                    "id": body.id,
                }

            # For now, execute via the registry's stored endpoint
            # (full auth handling is in the REST endpoint)
            try:
                validate_endpoint_url(tool.endpoint)
            except ValueError:
                return {
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": f"Tool '{tool_name}' endpoint is in a blocked network"},
                    "id": body.id,
                }

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    tool.endpoint,
                    json={"method": tool_name, "params": arguments},
                    headers={"Content-Type": "application/json"},
                )
                resp.raise_for_status()
                data = resp.json()

            return {
                "jsonrpc": "2.0",
                "result": {"content": [{"type": "text", "text": str(data)}]},
                "id": body.id,
            }

        elif body.method == "resources/list":
            # Query all knowledge bases as MCP resources
            result = await db.execute(
                select(KnowledgeBase).order_by(KnowledgeBase.created_at)
            )
            kbs = result.scalars().all()
            resources = [
                {
                    "uri": f"phi-kb://{kb.id}",
                    "name": kb.name,
                    "description": kb.description or "",
                    "mimeType": "application/json",
                }
                for kb in kbs
            ]
            return {
                "jsonrpc": "2.0",
                "result": {"resources": resources},
                "id": body.id,
            }

        elif body.method == "resources/read":
            uri = body.params.get("uri", "")
            kb_id_str = uri.replace("phi-kb://", "").split("/")[0]

            if not kb_id_str:
                return {
                    "jsonrpc": "2.0",
                    "error": {"code": -32602, "message": "Missing or invalid URI"},
                    "id": body.id,
                }

            # Query documents for this knowledge base
            try:
                kb_uuid = uuid.UUID(kb_id_str)
            except ValueError:
                return {
                    "jsonrpc": "2.0",
                    "error": {"code": -32602, "message": f"Invalid KB ID in URI: {kb_id_str}"},
                    "id": body.id,
                }

            result = await db.execute(
                select(Document).where(
                    Document.kb_id == kb_uuid
                ).limit(20)
            )
            docs = result.scalars().all()
            contents = [
                {
                    "uri": f"phi-kb://{kb_id_str}/doc/{doc.id}",
                    "text": doc.content,
                    "mimeType": "text/plain",
                }
                for doc in docs
            ]
            return {
                "jsonrpc": "2.0",
                "result": {"contents": contents},
                "id": body.id,
            }

        else:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": f"Method '{body.method}' not supported"},
                "id": body.id,
            }

    except Exception as e:
        logger.exception("MCP error")
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": str(e)},
            "id": body.id,
        }
