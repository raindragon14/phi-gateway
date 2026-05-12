from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from phi_gateway.core.security import generate_api_key
from phi_gateway.database import get_db
from phi_gateway.dependencies import get_api_key
from phi_gateway.models.api_key import ApiKey
from phi_gateway.schemas.keys import ApiKeyCreatedResponse, ApiKeyResponse, CreateApiKeyRequest

router = APIRouter(prefix="/v1/keys", tags=["API Keys"])


@router.post("", response_model=ApiKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    body: CreateApiKeyRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new API key. Returns the full key only once."""
    full_key, prefix, hashed = generate_api_key()

    # Map tier to rate limits
    rate_limits = {"free": (10, 10000), "pro": (60, 100000), "team": (300, 500000)}
    rpm, rpd = rate_limits.get(body.tier, (10, 10000))

    api_key = ApiKey(
        key_hash=hashed,
        prefix=prefix,
        name=body.name,
        tier=body.tier,
        rate_limit_per_min=rpm,
        rate_limit_per_day=rpd,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return ApiKeyCreatedResponse(
        id=api_key.id,
        key=full_key,
        prefix=prefix,
        name=api_key.name,
        tier=api_key.tier,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
    )


@router.get("", response_model=list[ApiKeyResponse])
async def list_api_keys(
    api_key: ApiKey = Depends(get_api_key),
    db: AsyncSession = Depends(get_db),
):
    """List all API keys for the current user."""
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.user_id == api_key.user_id,
            ApiKey.is_active.is_(True),
        )
    )
    keys = result.scalars().all()

    return [
        ApiKeyResponse(
            id=k.id,
            prefix=k.prefix,
            name=k.name,
            tier=k.tier,
            is_active=k.is_active,
            created_at=k.created_at,
            last_used_at=k.last_used_at,
        )
        for k in keys
    ]


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: UUID,
    api_key: ApiKey = Depends(get_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Revoke an API key by setting it to inactive."""
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.id == key_id,
            ApiKey.user_id == api_key.user_id,
            ApiKey.is_active.is_(True),
        )
    )
    target = result.scalar_one_or_none()

    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found or already revoked",
        )

    target.is_active = False
    await db.commit()

    return {"status": "revoked", "id": str(target.id)}
