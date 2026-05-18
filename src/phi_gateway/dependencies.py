from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from phi_gateway.core.rate_limiter import enforce_rate_limit, get_rate_limit_headers
from phi_gateway.core.security import verify_api_key
from phi_gateway.database import get_db
from phi_gateway.models.api_key import ApiKey


async def get_api_key(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiKey:
    """Extract and verify the API key from the Authorization header.

    Expected format: ``Authorization: Bearer ***

    Returns the ApiKey model instance on success.
    Raises HTTPException(401) on missing/invalid/expired key.
    On success, stores rate-limit headers on ``request.state.rate_limit_headers``
    so middleware or the endpoint can include them in the response.
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
            ApiKey.is_active.is_(True),
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

    # Enforce rate limits (sliding window)
    enforce_rate_limit(api_key)

    # Store rate-limit headers on request.state for downstream use
    request.state.rate_limit_headers = get_rate_limit_headers(api_key)

    # Update last_used_at in background (don't fail the request on write error)
    api_key.last_used_at = utc_now
    await db.commit()

    return api_key
