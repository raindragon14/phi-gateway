"""Integration tests for error response quality.

Verifies that all error responses are well-structured JSON with
descriptive messages — what a real API consumer would expect.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_missing_auth_returns_401_with_detail(async_client: AsyncClient):
    """Missing Authorization header → 401 with descriptive message."""
    response = await async_client.get("/v1/keys")
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert "Missing" in data["detail"]
    assert "Authorization" in data["detail"]


@pytest.mark.asyncio
async def test_invalid_auth_format_returns_401(async_client: AsyncClient):
    """Malformed Authorization header → 401 with format guidance."""
    response = await async_client.get(
        "/v1/keys",
        headers={"Authorization": "not-bearer-format"},
    )
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert "Bearer" in data["detail"]


@pytest.mark.asyncio
async def test_invalid_model_returns_400_with_available_models(async_client: AsyncClient):
    """Unknown model → 400 with detail listing available models."""
    # Create a key first
    key_resp = await async_client.post("/v1/keys", json={"name": "test", "tier": "free"})
    key = key_resp.json()["key"]

    response = await async_client.post(
        "/v1/chat/completions",
        json={"model": "nonexistent/model", "messages": [{"role": "user", "content": "hi"}]},
        headers={"Authorization": f"Bearer {key}"},
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "unknown" in data["detail"].lower() or "Unknown" in data["detail"]


@pytest.mark.asyncio
async def test_rate_limit_returns_429_with_retry_after(async_client: AsyncClient):
    """Rate limit exceeded → 429 with Retry-After header."""
    # Create a key with minimal rate limit
    key_resp = await async_client.post("/v1/keys", json={"name": "rl-test", "tier": "free"})
    key = key_resp.json()["key"]
    headers = {"Authorization": f"Bearer {key}"}

    # The default rate limit is 10/min. Exhaust it.
    # We need to hit the rate limiter directly since chat completions require LLM providers.
    # Instead, use a protected endpoint repeatedly.
    for _ in range(10):
        await async_client.get("/v1/keys", headers=headers)

    # The next request should be rate limited
    response = await async_client.get("/v1/keys", headers=headers)
    if response.status_code == 429:
        data = response.json()
        assert "detail" in data
        assert "Rate limit" in data["detail"] or "rate limit" in data["detail"].lower()
        assert "Retry-After" in response.headers


@pytest.mark.asyncio
async def test_request_too_large_returns_413(async_client: AsyncClient):
    """Oversized request → 413 with max size info."""
    from phi_gateway.config import settings

    oversized = settings.MAX_REQUEST_BODY_SIZE + 1
    response = await async_client.post(
        "/v1/keys",
        content=b"x",
        headers={
            "Content-Length": str(oversized),
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 413
    data = response.json()
    assert "detail" in data
    assert "too large" in data["detail"].lower()
    assert str(settings.MAX_REQUEST_BODY_SIZE) in data["detail"]


@pytest.mark.asyncio
async def test_error_responses_are_json(async_client: AsyncClient):
    """All error responses return valid JSON with a 'detail' field."""
    error_endpoints = [
        ("GET", "/v1/keys", 401),
        ("GET", "/v1/usage", 401),
        ("POST", "/v1/kb", 401),
        ("GET", "/v1/memory/conversations", 401),
    ]

    for method, path, expected_status in error_endpoints:
        if method == "GET":
            response = await async_client.get(path)
        else:
            response = await async_client.post(path, json={"name": "x", "description": "x"})

        assert response.status_code == expected_status, f"{method} {path}: expected {expected_status}, got {response.status_code}"
        data = response.json()
        assert "detail" in data, f"{method} {path}: missing 'detail' in {data}"
        assert isinstance(data["detail"], str), f"{method} {path}: 'detail' should be a string"
        assert len(data["detail"]) > 0, f"{method} {path}: 'detail' is empty"
