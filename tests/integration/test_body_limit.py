"""Integration tests for the request body size limit middleware."""

import pytest
from httpx import AsyncClient

from phi_gateway.config import settings


@pytest.mark.asyncio
async def test_body_under_limit_accepted(async_client: AsyncClient):
    """Normal request goes through."""
    response = await async_client.post(
        "/v1/keys",
        json={"name": "test", "tier": "free"},
    )
    # Should succeed (not 413)
    assert response.status_code != 413


@pytest.mark.asyncio
async def test_body_over_limit_rejected(async_client: AsyncClient):
    """Request with Content-Length > MAX_REQUEST_BODY_SIZE returns 413."""
    # Send a request with a fake Content-Length exceeding the limit
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
    assert "too large" in data["detail"].lower()
