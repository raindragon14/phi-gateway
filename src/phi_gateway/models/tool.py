"""MCP-compatible tool definitions for external tool registry."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from phi_gateway.models.base import Base


class ToolDefinition(Base):
    """Registered external tool available for LLM function calling.

    Each tool has a unique name, a JSON Schema describing its
    parameters, and an HTTP endpoint to invoke it. Tools are
    owned by an API key and can be globally active or disabled.

    Attributes:
        id: UUID primary key.
        name: Unique tool name used as the function name in LLM calls.
        description: Human-readable description sent to the LLM.
        json_schema: JSON Schema dict defining the tool's parameters.
        endpoint: HTTP(S) URL invoked when the tool is called.
        auth_type: Authentication method : ``"none"``, ``"bearer"``,
            or ``"api_key"``.
        is_active: Whether the tool can be used in requests.
        owner_api_key_id: Optional foreign key to the owning API key.
        created_at: Timestamp of tool registration (server default).
    """

    __tablename__ = "tool_definitions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    json_schema: Mapped[dict] = mapped_column(JSON, nullable=False)
    endpoint: Mapped[str] = mapped_column(String(500), nullable=False)
    auth_type: Mapped[str] = mapped_column(String(20), nullable=False, default="none")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    owner_api_key_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("api_keys.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
