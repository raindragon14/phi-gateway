import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_kb_crud(async_client: AsyncClient):
    """POST + DELETE /v1/kb CRUD flow."""
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
