import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from phi_gateway.core.security import verify_api_key
from phi_gateway.database import get_db
from phi_gateway.models.api_key import ApiKey


async def get_api_key(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiKey:
    """Extract and verify the API key from the Authorization header.

    Expected format: ``Authorization: Bearer <api_key>``

    Returns the ApiKey model instance on success.
    Raises HTTPException(401) on missing/invalid/expired key.
    """
    auth = request.headers.get("Authorization")
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header. Use: Bearer <api_key>",
        )

    parts = auth.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Use: Bearer <api_key>",
        )

    api_key_str = parts[1]
    prefix = api_key_str[:12]

    # Look up by prefix (constant-time prefix comparison doesn't matter here;
    # the bcrypt check below provides the actual verification)
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.prefix == prefix,
            ApiKey.is_active == True,
        )
    )
    api_key = result.scalar_one_or_none()

    if api_key is None:
        # Always run bcrypt check to prevent timing oracle
        verify_api_key(api_key_str, "$2b$12$" + "0" * 53)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    if not verify_api_key(api_key_str, api_key.key_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    utc_now = datetime.now(timezone.utc)
    if api_key.expires_at and api_key.expires_at < utc_now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired",
        )

    # Update last_used_at in background (don't fail the request on write error)
    api_key.last_used_at = utc_now
    await db.flush()

    return api_key


def require_tier(min_tier: str) -> Callable:
    """Dependency factory: require API key tier to be at least ``min_tier``.

    Tier ordering: free < pro < team

    Usage::

        @router.get("/admin")
        async def admin_endpoint(key: ApiKey = Depends(require_tier("team"))):
            ...
    """

    async def _require_tier(
        api_key: Annotated[ApiKey, Depends(get_api_key)],
    ) -> ApiKey:
        tier_order = {"free": 0, "pro": 1, "team": 2}
        if tier_order.get(api_key.tier, 0) < tier_order.get(min_tier, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires tier '{min_tier}' or higher. Current tier: '{api_key.tier}'",
            )
        return api_key

    return _require_tier
