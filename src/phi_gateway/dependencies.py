"""Shared FastAPI dependencies for request authentication and rate limiting.

Provides ``RequireApiKey`` which extracts, verifies, and optionally
tier-gates API keys from the Authorization header or session cookie.

Usage::

    # Any authenticated tier:
    api_key: ApiKey = Depends(RequireApiKey())

    # Admin or pro tier only:
    api_key: ApiKey = Depends(RequireApiKey(required_tiers=("admin", "pro")))
"""

from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from phi_gateway.core.rate_limiter import enforce_rate_limit, get_rate_limit_headers
from phi_gateway.core.security import verify_api_key
from phi_gateway.database import get_db
from phi_gateway.models.api_key import ApiKey


class RequireApiKey:
    """Dependency class for API key authentication with optional tier gating.

    Instantiated once at import time and passed to ``Depends()``.
    ``__init__`` params control tier policy; ``__call__`` params are
    injected by FastAPI on each request.

    Args:
        required_tiers: Tuple of allowed tier names, or ``None`` to
            accept any authenticated key.

    Example::

        # Any tier:
        api_key: ApiKey = Depends(RequireApiKey())

        # Dashboard (admin/pro only):
        api_key: ApiKey = Depends(RequireApiKey(required_tiers=("admin", "pro")))
    """

    def __init__(self, required_tiers: tuple[str, ...] | None = None) -> None:
        """Initialize with optional tier constraint.

        Args:
            required_tiers: Allowed tier names. ``None`` accepts all tiers.
        """
        self.required_tiers = required_tiers

    async def __call__(
        self,
        request: Request,
        db: AsyncSession = Depends(get_db),
    ) -> ApiKey:
        """Authenticate the request and return the API key.

        Reads the key from ``Authorization: Bearer <key>`` header or
        ``phi_api_key`` cookie. Enforces rate limits and updates
        ``last_used_at`` on success.

        Args:
            request: The incoming HTTP request.
            db: Async database session (injected by FastAPI).

        Returns:
            The verified ``ApiKey`` instance.

        Raises:
            HTTPException: 401 if missing/invalid/expired. 403 if tier
                is not in ``required_tiers``.

        Note:
            Stores rate-limit headers on ``request.state.rate_limit_headers``
            so the security-headers middleware can attach them.
        """
        api_key_str: str | None = None

        auth = request.headers.get("Authorization")
        if auth:
            parts = auth.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                api_key_str = parts[1]
        else:
            # Fallback to cookie (browser users after login)
            cookie_key = request.cookies.get("phi_api_key")
            if cookie_key:
                api_key_str = cookie_key

        if not api_key_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Authorization header. Use: Bearer <api_key>",
            )

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

        # Tier gate : reject if the key's tier is not in the allowed set
        if self.required_tiers is not None and api_key.tier not in self.required_tiers:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of tiers: {', '.join(self.required_tiers)}",
            )

        return api_key


# Default instance : any tier, no gating. Used by most endpoints.
get_api_key = RequireApiKey()
