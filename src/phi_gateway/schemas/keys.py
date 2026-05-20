"""Pydantic schemas for API key management : creation, listing, and responses."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator


class CreateApiKeyRequest(BaseModel):
    """Request body to create a new API key.

    Attributes:
        name: Human-readable label for the key.
        tier: Rate-limiting tier : ``"free"``, ``"pro"``, ``"team"``,
            or ``"admin"``. Defaults to ``"free"``.
    """

    name: str
    tier: str = "free"

    @model_validator(mode="after")
    def validate_tier(self) -> "CreateApiKeyRequest":
        """Ensure the tier is one of the accepted values."""
        valid_tiers = {"free", "pro", "team", "admin"}
        if self.tier not in valid_tiers:
            raise ValueError(f"tier must be one of {valid_tiers}, got '{self.tier}'")
        return self


class ApiKeyResponse(BaseModel):
    """Public representation of an API key (no raw key value exposed).

    Attributes:
        id: UUID of the key.
        prefix: First 12 characters for identification.
        name: Human-readable label.
        tier: Rate-limiting tier.
        is_active: Whether the key is currently usable.
        created_at: Timestamp of creation.
        last_used_at: Optional timestamp of last authenticated request.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    prefix: str
    name: str
    tier: str
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None


class ApiKeyCreatedResponse(BaseModel):
    """Response when a new key is created : includes the raw key shown once.

    Attributes:
        id: UUID of the new key.
        key: The full raw API key string (shown only in this response).
        prefix: First 12 characters for identification.
        name: Human-readable label.
        tier: Rate-limiting tier.
        is_active: Always ``True`` for new keys.
        created_at: Timestamp of creation.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    key: str  # The raw key (shown only once)
    prefix: str
    name: str
    tier: str
    is_active: bool
    created_at: datetime
