import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_api_key(async_client: AsyncClient):
    """POST /v1/keys returns a valid API key."""
    response = await async_client.post(
        "/v1/keys",
        json={"name": "test", "tier": "free"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["key"].startswith("phi-sk-")
    assert len(data["key"]) == 55  # phi-sk- (7) + 48 hex
    assert data["prefix"] == data["key"][:12]
    assert data["name"] == "test"
    assert data["tier"] == "free"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_api_keys(async_client: AsyncClient):
    """GET /v1/keys returns list with the created key."""
    created = await async_client.post("/v1/keys", json={"name": "test", "tier": "free"})
    full_key = created.json()["key"]

    response = await async_client.get(
        "/v1/keys",
        headers={"Authorization": f"Bearer {full_key}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "test"


@pytest.mark.asyncio
async def test_revoke_api_key(async_client: AsyncClient):
    """DELETE /v1/keys/{id} revokes key, then it fails auth."""
    created = await async_client.post("/v1/keys", json={"name": "test", "tier": "free"})
    data = created.json()
    full_key = data["key"]
    key_id = data["id"]

    revoke = await async_client.delete(
        f"/v1/keys/{key_id}",
        headers={"Authorization": f"Bearer {full_key}"},
    )
    assert revoke.status_code == 200
    assert revoke.json()["status"] == "revoked"

    # Using the revoked key should now fail
    retry = await async_client.get(
        "/v1/keys",
        headers={"Authorization": f"Bearer {full_key}"},
    )
    assert retry.status_code == 401


@pytest.mark.asyncio
async def test_unauthorized_access(async_client: AsyncClient):
    """GET /v1/keys without auth returns 401."""
    response = await async_client.get("/v1/keys")
    assert response.status_code == 401
    assert "Missing" in response.json()["detail"]
