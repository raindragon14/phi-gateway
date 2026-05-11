import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_chat_unauthorized(async_client: AsyncClient):
    """POST /v1/chat/completions without auth returns 401."""
    response = await async_client.post(
        "/v1/chat/completions",
        json={"model": "gpt-5-nano", "messages": [{"role": "user", "content": "hi"}]},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_chat_invalid_model(async_client: AsyncClient):
    """POST /v1/chat/completions with unknown model returns 400."""
    created = await async_client.post("/v1/keys", json={"name": "test", "tier": "free"})
    full_key = created.json()["key"]

    response = await async_client.post(
        "/v1/chat/completions",
        json={
            "model": "unknown/model",
            "messages": [{"role": "user", "content": "hi"}],
        },
        headers={"Authorization": f"Bearer {full_key}"},
    )
    assert response.status_code == 400
    assert "unknown" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_models_endpoint(async_client: AsyncClient):
    """GET /v1/models returns list of available models."""
    response = await async_client.get("/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "id" in data[0]
    assert "provider" in data[0]
