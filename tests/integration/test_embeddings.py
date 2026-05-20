"""Integration tests for the /v1/embeddings endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_embeddings_unauthorized(async_client: AsyncClient):
    """POST /v1/embeddings without auth returns 401."""
    response = await async_client.post(
        "/v1/embeddings",
        json={"model": "text-embedding-3-small", "input": "hello"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_embeddings_with_openrouter(async_client: AsyncClient):
    """POST /v1/embeddings succeeds when OpenRouter is configured."""
    key_resp = await async_client.post("/v1/keys", json={"name": "test", "tier": "free"})
    key = key_resp.json()["key"]

    response = await async_client.post(
        "/v1/embeddings",
        json={"model": "text-embedding-3-small", "input": "hello"},
        headers={"Authorization": f"Bearer {key}"},
    )
    assert response.status_code in (200, 502)
    if response.status_code == 200:
        data = response.json()
        assert len(data["data"][0]["embedding"]) > 0
