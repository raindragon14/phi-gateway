"""API key management endpoints — create, list, and revoke gateway keys.

Protected against unauthorized creation after initial bootstrap.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from phi_gateway.core.security import generate_api_key
from phi_gateway.database import get_db
from phi_gateway.dependencies import get_api_key
from phi_gateway.models.api_key import ApiKey
from phi_gateway.schemas.keys import ApiKeyCreatedResponse, ApiKeyResponse, CreateApiKeyRequest

router = APIRouter(prefix="/v1/keys", tags=["API Keys"])


async def _require_auth_or_bootstrap(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiKey | None:
    """Require auth for key creation if any admin key already exists.

    On a fresh deploy with zero admin keys, this allows unauthenticated
    creation (bootstrapping). Once at least one admin key is present,
    valid admin/pro credentials are required.

    Args:
        request: The incoming HTTP request.
        db: Async database session.

    Returns:
        The authenticated ``ApiKey`` if auth is required, or ``None``
        during bootstrapping (no admin keys exist yet).
    """
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.tier == "admin",
            ApiKey.is_active.is_(True),
        )
    )
    admin_exists = result.first() is not None

    if not admin_exists:
        return None  # bootstrapping — no auth needed

    # Admin key exists — delegate to standard auth (raises 401 on failure)
    return await get_api_key(request, db)


@router.post("", response_model=ApiKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    body: CreateApiKeyRequest,
    db: AsyncSession = Depends(get_db),
    auth: ApiKey | None = Depends(_require_auth_or_bootstrap),
):
    """Create a new API key.

    **Bootstrapping:** When no admin keys exist yet, this endpoint can
    be called without authentication (first-deploy scenario). After at
    least one admin key has been created, an admin or pro API key is
    required to create new keys.

    Args:
        body: Request with key name and tier.
        db: Async database session.
        auth: Authenticated API key (``None`` during bootstrapping).

    Returns:
        ``ApiKeyCreatedResponse`` including the raw key (shown once).

    Raises:
        HTTPException: 403 if the caller is not admin or pro tier.
    """
    if auth and auth.tier not in ("admin", "pro"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or pro tier keys can create new API keys",
        )

    full_key, prefix, hashed = generate_api_key()

    # Map tier to rate limits
    rate_limits = {
        "free": (10, 10000),
        "pro": (60, 100000),
        "team": (300, 500000),
        "admin": (1000, 500000),
    }
    rpm, rpd = rate_limits.get(body.tier, (10, 10000))

    api_key_obj = ApiKey(
        key_hash=hashed,
        prefix=prefix,
        name=body.name,
        tier=body.tier,
        rate_limit_per_min=rpm,
        rate_limit_per_day=rpd,
    )
    db.add(api_key_obj)
    await db.commit()
    await db.refresh(api_key_obj)

    return ApiKeyCreatedResponse(
        id=api_key_obj.id,
        key=full_key,
        prefix=prefix,
        name=api_key_obj.name,
        tier=api_key_obj.tier,
        is_active=api_key_obj.is_active,
        created_at=api_key_obj.created_at,
    )


@router.get("", response_model=list[ApiKeyResponse])
async def list_api_keys(
    api_key: ApiKey = Depends(get_api_key),
    db: AsyncSession = Depends(get_db),
):
    """List all active API keys for the current user.

    Args:
        api_key: Authenticated API key (used to scope results).
        db: Async database session.

    Returns:
        List of ``ApiKeyResponse`` (no raw key values exposed).
    """
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
    """Revoke an API key by setting it to inactive.

    Args:
        key_id: UUID of the key to revoke.
        api_key: Authenticated API key (must own the target key).
        db: Async database session.

    Returns:
        Dict with ``"status"`` and ``"id"`` keys.

    Raises:
        HTTPException: 404 if the key does not exist, is not owned
            by the caller, or is already revoked.
    """
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
