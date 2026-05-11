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
async def test_embeddings_no_openai_key(async_client: AsyncClient):
    """POST /v1/embeddings without configured OpenAI key returns 502."""
    key_resp = await async_client.post("/v1/keys", json={"name": "test", "tier": "free"})
    key = key_resp.json()["key"]

    response = await async_client.post(
        "/v1/embeddings",
        json={"model": "text-embedding-3-small", "input": "hello"},
        headers={"Authorization": f"Bearer {key}"},
    )
    assert response.status_code == 502
    assert "OPENAI_API_KEY" in response.json()["detail"]
