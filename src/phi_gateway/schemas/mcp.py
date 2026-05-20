"""Pydantic schemas for the MCP (Model Context Protocol) gateway endpoint."""

from typing import Any

from pydantic import BaseModel


class JsonRpcRequest(BaseModel):
    """A JSON-RPC 2.0 request body.

    Used by MCP clients to interact with the gateway's
    tool registry and execute registered tools.

    Attributes:
        jsonrpc: Protocol version, always ``"2.0"``.
        method: RPC method name.
        params: Method parameters dictionary.
        id: Request identifier (string or integer).
    """

    jsonrpc: str = "2.0"
    method: str
    params: dict[str, Any] = {}
    id: str | int = "1"
