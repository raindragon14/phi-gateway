"""Pydantic schemas for external tool management and invocation."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CreateToolRequest(BaseModel):
    """Request body to register a new external tool.

    Attributes:
        name: Unique tool name used as the function name in LLM calls.
        description: Human-readable description sent to the LLM.
        json_schema: JSON Schema dict defining the tool's parameters.
        endpoint: HTTP(S) URL to invoke when the tool is called.
        auth_type: Authentication method — ``"none"`` (default),
            ``"bearer"``, or ``"api_key"``.
    """

    name: str
    description: str
    json_schema: dict
    endpoint: str
    auth_type: str = "none"


class ToolResponse(BaseModel):
    """Public representation of a registered tool.

    Attributes:
        id: UUID of the tool.
        name: Unique tool name.
        description: Human-readable description.
        json_schema: JSON Schema dict.
        endpoint: HTTP(S) invocation URL.
        auth_type: Authentication method.
        is_active: Whether the tool is available for use.
        owner_api_key_id: Optional UUID of the owning API key.
        created_at: Timestamp of registration.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    json_schema: dict
    endpoint: str
    auth_type: str
    is_active: bool
    owner_api_key_id: Optional[UUID] = None
    created_at: datetime


class ToolCallRequest(BaseModel):
    """Request body to invoke a registered tool.

    Attributes:
        method: RPC method name to call.
        params: Method parameters dictionary.
    """

    method: str
    params: dict[str, Any] = {}


class ToolCallResponse(BaseModel):
    """Response from a tool invocation.

    Attributes:
        result: The result returned by the tool (any type).
        error: Optional error message if the call failed.
    """

    result: Any = None
    error: Optional[str] = None
