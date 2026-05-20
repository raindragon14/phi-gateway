"""Unit tests for phi_gateway.core.rate_limiter — in-memory sliding window."""

import time
import uuid

import pytest

from phi_gateway.core import rate_limiter
from phi_gateway.core.exceptions import RateLimitExceeded
from phi_gateway.core.rate_limiter import enforce_rate_limit, get_rate_limit_headers


def _make_api_key(rate_per_min: int = 5, rate_per_day: int = 1000):
    """Create a lightweight mock ApiKey with the fields rate_limiter needs."""
    return type(
        "MockApiKey",
        (),
        {
            "id": uuid.uuid4(),
            "rate_limit_per_min": rate_per_min,
            "rate_limit_per_day": rate_per_day,
        },
    )()


@pytest.fixture(autouse=True)
def _clear_buckets():
    """Reset in-memory rate limiter buckets before each test."""
    rate_limiter._minute_buckets.clear()
    rate_limiter._day_buckets.clear()
    yield
    rate_limiter._minute_buckets.clear()
    rate_limiter._day_buckets.clear()


class TestEnforceRateLimit:
    def test_under_limit_does_not_raise(self):
        """Requests below the per-minute limit should pass without error."""
        api_key = _make_api_key(rate_per_min=5)
        for _ in range(4):
            enforce_rate_limit(api_key)  # should not raise

    def test_at_limit_raises_rate_limit_exceeded(self):
        """Requests at or above the per-minute limit should raise RateLimitExceeded."""
        api_key = _make_api_key(rate_per_min=3)
        for _ in range(3):
            enforce_rate_limit(api_key)

        with pytest.raises(RateLimitExceeded) as exc_info:
            enforce_rate_limit(api_key)

        assert exc_info.value.limit == 3
        assert exc_info.value.window == "minute"

    def test_sliding_window_prunes_old_requests(self):
        """Old timestamps outside the window should be pruned, allowing new requests."""
        api_key = _make_api_key(rate_per_min=2)

        # Fill the bucket with old timestamps (> 60s ago)
        key_id = str(api_key.id)
        old_time = time.time() - 120  # 2 minutes ago
        rate_limiter._minute_buckets[key_id] = [old_time, old_time]

        # Should NOT raise because old entries are pruned
        enforce_rate_limit(api_key)  # should pass

    def test_daily_limit_raises_rate_limit_exceeded(self):
        """Exceeding the daily limit should raise RateLimitExceeded with window='day'."""
        api_key = _make_api_key(rate_per_min=9999, rate_per_day=2)

        enforce_rate_limit(api_key)
        enforce_rate_limit(api_key)

        with pytest.raises(RateLimitExceeded) as exc_info:
            enforce_rate_limit(api_key)

        assert exc_info.value.limit == 2
        assert exc_info.value.window == "day"


class TestGetRateLimitHeaders:
    def test_returns_correct_headers(self):
        """Headers should include limit and remaining for both minute and day."""
        api_key = _make_api_key(rate_per_min=10, rate_per_day=5000)

        headers = get_rate_limit_headers(api_key)

        assert headers["X-RateLimit-Limit-Min"] == "10"
        assert headers["X-RateLimit-Remaining-Min"] == "10"
        assert headers["X-RateLimit-Limit-Day"] == "5000"
        assert headers["X-RateLimit-Remaining-Day"] == "5000"

    def test_remaining_decreases_after_requests(self):
        """Remaining count should decrease as requests are made."""
        api_key = _make_api_key(rate_per_min=5, rate_per_day=1000)

        # Make 3 requests
        for _ in range(3):
            enforce_rate_limit(api_key)

        headers = get_rate_limit_headers(api_key)
        assert headers["X-RateLimit-Remaining-Min"] == "2"

    def test_remaining_never_negative(self):
        """Remaining should never go below 0."""
        api_key = _make_api_key(rate_per_min=2, rate_per_day=1000)

        # Make 5 requests (over limit, but we check headers)
        key_id = str(api_key.id)
        now = time.time()
        rate_limiter._minute_buckets[key_id] = [now] * 10

        headers = get_rate_limit_headers(api_key)
        assert int(headers["X-RateLimit-Remaining-Min"]) == 0
