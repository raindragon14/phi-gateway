from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator


class CreateApiKeyRequest(BaseModel):
    name: str
    tier: str = "free"

    @model_validator(mode="after")
    def validate_tier(self) -> "CreateApiKeyRequest":
        valid_tiers = {"free", "pro", "team"}
        if self.tier not in valid_tiers:
            raise ValueError(f"tier must be one of {valid_tiers}, got '{self.tier}'")
        return self


class ApiKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    prefix: str
    name: str
    tier: str
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None


class ApiKeyCreatedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    key: str  # The raw key (shown only once)
    prefix: str
    name: str
    tier: str
    is_active: bool
    created_at: datetime
