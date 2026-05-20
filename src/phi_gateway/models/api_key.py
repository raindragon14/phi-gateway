"""API key model : authentication, rate limits, and tier management."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from phi_gateway.models.base import Base


class ApiKey(Base):
    """Database model for API keys used to authenticate gateway requests.

    Each key has a tier (free, pro, team, admin) that controls rate
    limits, and can optionally expire. Keys are stored as bcrypt
    hashes : the raw value is never persisted beyond creation.

    Attributes:
        id: UUID primary key.
        key_hash: bcrypt hash of the full API key string.
        prefix: First 12 characters of the key (for lookup/display).
        name: Human-readable label for the key.
        user_id: Arbitrary user identifier (defaults to ``"default"``).
        tier: Rate-limiting tier : ``"free"``, ``"pro"``, ``"team"``,
            or ``"admin"``.
        rate_limit_per_min: Maximum requests allowed per minute.
        rate_limit_per_day: Maximum requests allowed per day.
        is_active: Whether the key is currently usable.
        created_at: Timestamp of key creation (server default).
        last_used_at: Optional timestamp of last authenticated request.
        expires_at: Optional expiration timestamp.
    """

    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    key_hash: Mapped[str] = mapped_column(String(60), nullable=False)
    prefix: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, default="default")
    tier: Mapped[str] = mapped_column(String(10), nullable=False, default="free")
    rate_limit_per_min: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    rate_limit_per_day: Mapped[int] = mapped_column(Integer, nullable=False, default=10000)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
