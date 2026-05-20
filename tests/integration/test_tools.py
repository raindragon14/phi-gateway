"""Integration tests for the /v1/tools registry and invocation endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_tool(async_client: AsyncClient):
    """POST /v1/tools creates a new tool definition."""
    key_resp = await async_client.post("/v1/keys", json={"name": "test", "tier": "free"})
    key = key_resp.json()["key"]

    resp = await async_client.post(
        "/v1/tools",
        json={
            "name": "test-tool",
            "description": "A test tool",
            "json_schema": {"type": "object", "properties": {"x": {"type": "string"}}},
            "endpoint": "https://httpbin.org/post",
        },
        headers={"Authorization": f"Bearer {key}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "test-tool"
    assert data["is_active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_create_duplicate_tool(async_client: AsyncClient):
    """POST /v1/tools with duplicate name returns 409."""
    key_resp = await async_client.post("/v1/keys", json={"name": "test", "tier": "free"})
    key = key_resp.json()["key"]
    payload = {
        "name": "dup-tool",
        "description": "dup",
        "json_schema": {"type": "object"},
        "endpoint": "https://httpbin.org/post",
    }

    resp1 = await async_client.post("/v1/tools", json=payload, headers={"Authorization": f"Bearer {key}"})
    assert resp1.status_code == 201

    resp2 = await async_client.post("/v1/tools", json=payload, headers={"Authorization": f"Bearer {key}"})
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_list_tools(async_client: AsyncClient):
    """GET /v1/tools returns list of available tools."""
    key_resp = await async_client.post("/v1/keys", json={"name": "test", "tier": "free"})
    key = key_resp.json()["key"]

    # Create a tool
    await async_client.post(
        "/v1/tools",
        json={"name": "listable", "description": "x", "json_schema": {"type": "object"}, "endpoint": "https://x.com"},
        headers={"Authorization": f"Bearer {key}"},
    )

    resp = await async_client.get("/v1/tools")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    names = [t["name"] for t in data]
    assert "listable" in names


@pytest.mark.asyncio
async def test_tool_schema(async_client: AsyncClient):
    """GET /v1/tools/{id}/schema returns the JSON schema."""
    key_resp = await async_client.post("/v1/keys", json={"name": "test", "tier": "free"})
    key = key_resp.json()["key"]

    schema = {"type": "object", "properties": {"q": {"type": "string"}}, "required": ["q"]}
    created = await async_client.post(
        "/v1/tools",
        json={"name": "schema-test", "description": "x", "json_schema": schema, "endpoint": "https://x.com"},
        headers={"Authorization": f"Bearer {key}"},
    )
    tool_id = created.json()["id"]

    resp = await async_client.get(f"/v1/tools/{tool_id}/schema")
    assert resp.status_code == 200
    assert resp.json() == schema
