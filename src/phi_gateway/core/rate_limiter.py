"""Rate limiting with sliding window — enforced per API key.

Uses an in-memory store (dict) for MVP. Replace with Redis for
multi-worker deployments.
"""

import time
from collections import defaultdict, deque

from fastapi import HTTPException, status

from phi_gateway.models.api_key import ApiKey

# ── In-memory stores (replace with Redis in production) ────────────

# minute_counts: {key_id: deque([timestamp, ...])}
_minute_buckets: dict[str, deque[float]] = defaultdict(deque)
_day_buckets: dict[str, deque[float]] = defaultdict(deque)


def _prune(bucket: deque[float] | list[float], cutoff: float) -> deque[float]:
    """Remove timestamps older than cutoff from a sliding window bucket.

    Args:
        bucket: Deque or list of unix timestamps.
        cutoff: Timestamps older than this are removed.

    Returns:
        The pruned deque.
    """
    if isinstance(bucket, list):
        bucket = deque(bucket)
    while bucket and bucket[0] < cutoff:
        bucket.popleft()
    return bucket


def enforce_rate_limit(api_key: ApiKey) -> None:
    """Check and enforce rate limits for the given API key.

    Uses a sliding window algorithm for both per-minute and per-day
    limits.

    Args:
        api_key: The authenticated API key to check.

    Raises:
        HTTPException: 429 if per-minute or per-day rate limits are
            exceeded. Includes a ``Retry-After`` header.
    """
    now = time.time()
    key_id = str(api_key.id)

    # ── Per-minute check ──
    minute_cutoff = now - 60
    _minute_buckets[key_id] = _prune(_minute_buckets[key_id], minute_cutoff)

    if len(_minute_buckets[key_id]) >= api_key.rate_limit_per_min:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {api_key.rate_limit_per_min} req/min. "
            f"Upgrade to pro or team tier.",
            headers={"Retry-After": "60"},
        )

    _minute_buckets[key_id].append(now)

    # ── Per-day check ──
    day_cutoff = now - 86400
    _day_buckets[key_id] = _prune(_day_buckets[key_id], day_cutoff)

    if len(_day_buckets[key_id]) >= api_key.rate_limit_per_day:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily rate limit exceeded: {api_key.rate_limit_per_day} req/day. "
            f"Upgrade to pro or team tier.",
            headers={"Retry-After": "86400"},
        )

    _day_buckets[key_id].append(now)


def get_rate_limit_headers(api_key: ApiKey) -> dict[str, str]:
    """Return rate limit headers for a response (informational).

    Args:
        api_key: The authenticated API key.

    Returns:
        Dict with ``X-RateLimit-Limit-Min``,
        ``X-RateLimit-Remaining-Min``, ``X-RateLimit-Limit-Day``,
        and ``X-RateLimit-Remaining-Day`` header values.
    """
    key_id = str(api_key.id)
    now = time.time()

    minute_count = len([t for t in _minute_buckets[key_id] if t > now - 60])
    day_count = len([t for t in _day_buckets[key_id] if t > now - 86400])

    return {
        "X-RateLimit-Limit-Min": str(api_key.rate_limit_per_min),
        "X-RateLimit-Remaining-Min": str(max(0, api_key.rate_limit_per_min - minute_count)),
        "X-RateLimit-Limit-Day": str(api_key.rate_limit_per_day),
        "X-RateLimit-Remaining-Day": str(max(0, api_key.rate_limit_per_day - day_count)),
    }
