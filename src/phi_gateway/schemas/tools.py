from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CreateToolRequest(BaseModel):
    name: str
    description: str
    json_schema: dict
    endpoint: str
    auth_type: str = "none"


class ToolResponse(BaseModel):
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
    method: str
    params: dict[str, Any] = {}


class ToolCallResponse(BaseModel):
    result: Any = None
    error: Optional[str] = None
