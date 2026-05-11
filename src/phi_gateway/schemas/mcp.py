from typing import Any, Optional

from pydantic import BaseModel


class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: dict[str, Any] = {}
    id: str | int = "1"


class JsonRpcResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: Any = None
    error: Optional[dict] = None
    id: str | int | None = None
