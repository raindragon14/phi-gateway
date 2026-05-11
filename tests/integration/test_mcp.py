import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_mcp_resources_list_empty(async_client: AsyncClient):
    """POST /mcp with resources/list returns empty list when no KBs exist."""
    resp = await async_client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "method": "resources/list", "params": {}, "id": "1"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["jsonrpc"] == "2.0"
    assert "result" in data
    assert data["result"]["resources"] == []


@pytest.mark.asyncio
async def test_mcp_resources_list_with_kb(async_client: AsyncClient):
    """POST /mcp with resources/list returns created KBs."""
    key_resp = await async_client.post("/v1/keys", json={"name": "test", "tier": "free"})
    key = key_resp.json()["key"]

    # Create a KB
    create_resp = await async_client.post(
        "/v1/kb",
        json={"name": "mcp-kb", "description": "For MCP testing"},
        headers={"Authorization": f"Bearer {key}"},
    )
    assert create_resp.status_code == 201
    kb_id = create_resp.json()["id"]

    # Query resources
    resp = await async_client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "method": "resources/list", "params": {}, "id": "1"},
    )
    assert resp.status_code == 200
    data = resp.json()
    resources = data["result"]["resources"]
    assert len(resources) >= 1

    # Find our KB
    kb_resource = next((r for r in resources if r["name"] == "mcp-kb"), None)
    assert kb_resource is not None
    assert kb_resource["uri"] == f"phi-kb://{kb_id}"
    assert kb_resource["mimeType"] == "application/json"


@pytest.mark.asyncio
async def test_mcp_resources_read(async_client: AsyncClient):
    """POST /mcp with resources/read returns document contents."""
    key_resp = await async_client.post("/v1/keys", json={"name": "test", "tier": "free"})
    key = key_resp.json()["key"]

    # Create KB
    kb_resp = await async_client.post(
        "/v1/kb",
        json={"name": "readable-kb", "description": "For MCP read testing"},
        headers={"Authorization": f"Bearer {key}"},
    )
    kb_id = kb_resp.json()["id"]

    # Ingest a document
    await async_client.post(
        f"/v1/kb/{kb_id}/documents",
        json={
            "documents": [
                {"title": "Readme", "content": "This is a test document.", "metadata": {}}
            ]
        },
        headers={"Authorization": f"Bearer {key}"},
    )

    # Read via MCP
    resp = await async_client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "method": "resources/read",
            "params": {"uri": f"phi-kb://{kb_id}"},
            "id": "2",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["jsonrpc"] == "2.0"
    assert "result" in data

    contents = data["result"]["contents"]
    assert len(contents) >= 1
    assert contents[0]["text"] == "This is a test document."
    assert contents[0]["mimeType"] == "text/plain"
    assert contents[0]["uri"].startswith(f"phi-kb://{kb_id}/doc/")
