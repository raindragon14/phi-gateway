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


@pytest.mark.asyncio
async def test_mcp_tools_list(async_client: AsyncClient):
    """POST /mcp with tools/list returns JSON-RPC 2.0 response."""
    resp = await async_client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": "1"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["jsonrpc"] == "2.0"
    assert "result" in data
    assert data["id"] == "1"


@pytest.mark.asyncio
async def test_mcp_unknown_method(async_client: AsyncClient):
    """POST /mcp with unknown method returns error code -32601."""
    resp = await async_client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "method": "bogus", "params": {}, "id": "1"},
    )
    assert resp.status_code == 200  # JSON-RPC uses 200 even for errors
    data = resp.json()
    assert data["error"]["code"] == -32601


@pytest.mark.asyncio
async def test_kb_crud(async_client: AsyncClient):
    """POST/GET/DELETE /v1/kb CRUD flow."""
    key_resp = await async_client.post("/v1/keys", json={"name": "test", "tier": "free"})
    key = key_resp.json()["key"]

    # Create
    created = await async_client.post(
        "/v1/kb",
        json={"name": "my-kb", "description": "test KB"},
        headers={"Authorization": f"Bearer {key}"},
    )
    assert created.status_code == 201
    kb_id = created.json()["id"]
    assert created.json()["name"] == "my-kb"

    # Delete
    deleted = await async_client.delete(
        f"/v1/kb/{kb_id}",
        headers={"Authorization": f"Bearer {key}"},
    )
    assert deleted.status_code == 200
    assert deleted.json()["status"] == "deleted"


@pytest.mark.asyncio
async def test_kb_ingest_and_search(async_client: AsyncClient):
    """POST /v1/kb/{id}/documents with ingest + POST /v1/kb/{id}/search."""
    key_resp = await async_client.post("/v1/keys", json={"name": "test", "tier": "free"})
    key = key_resp.json()["key"]

    # Create KB
    kb_resp = await async_client.post(
        "/v1/kb",
        json={"name": "search-kb", "description": "for testing search"},
        headers={"Authorization": f"Bearer {key}"},
    )
    kb_id = kb_resp.json()["id"]

    # Ingest documents
    ingest_resp = await async_client.post(
        f"/v1/kb/{kb_id}/documents",
        json={
            "documents": [
                {"title": "D1", "content": "The quick brown fox jumps over the lazy dog.", "metadata": {"tag": "animal"}},
                {"title": "D2", "content": "Python is a high-level programming language.", "metadata": {"tag": "tech"}},
            ]
        },
        headers={"Authorization": f"Bearer {key}"},
    )
    assert ingest_resp.status_code == 201
    assert ingest_resp.json()["total_chunks"] == 2

    # Search (keyword fallback since no OpenAI key)
    search_resp = await async_client.post(
        f"/v1/kb/{kb_id}/search",
        json={"query": "fox", "top_k": 3},
        headers={"Authorization": f"Bearer {key}"},
    )
    assert search_resp.status_code == 200
    results = search_resp.json()["results"]
    assert len(results) >= 1
    assert "fox" in results[0]["content"].lower()


@pytest.mark.asyncio
async def test_kb_unauthorized(async_client: AsyncClient):
    """KB operations without auth return 401."""
    resp = await async_client.post("/v1/kb", json={"name": "x", "description": "x"})
    assert resp.status_code == 401

    resp = await async_client.post("/v1/kb/00000000-0000-0000-0000-000000000000/documents", json={"documents": []})
    assert resp.status_code == 401
