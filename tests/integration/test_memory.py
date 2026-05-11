import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_conversation(async_client: AsyncClient):
    """POST /v1/memory/conversations creates a conversation."""
    key_resp = await async_client.post("/v1/keys", json={"name": "test", "tier": "free"})
    key = key_resp.json()["key"]

    resp = await async_client.post(
        "/v1/memory/conversations",
        json={"session_id": "sess-001", "title": "Test Conversation"},
        headers={"Authorization": f"Bearer {key}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["session_id"] == "sess-001"
    assert data["title"] == "Test Conversation"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_list_conversations(async_client: AsyncClient):
    """GET /v1/memory/conversations returns list of conversations."""
    key_resp = await async_client.post("/v1/keys", json={"name": "test", "tier": "free"})
    key = key_resp.json()["key"]

    # Create two conversations
    await async_client.post(
        "/v1/memory/conversations",
        json={"session_id": "sess-a", "title": "First"},
        headers={"Authorization": f"Bearer {key}"},
    )
    await async_client.post(
        "/v1/memory/conversations",
        json={"session_id": "sess-b", "title": "Second"},
        headers={"Authorization": f"Bearer {key}"},
    )

    resp = await async_client.get(
        "/v1/memory/conversations",
        headers={"Authorization": f"Bearer {key}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 2
    titles = [c["title"] for c in data]
    assert "First" in titles
    assert "Second" in titles


@pytest.mark.asyncio
async def test_add_and_get_messages(async_client: AsyncClient):
    """POST + GET messages in a conversation."""
    key_resp = await async_client.post("/v1/keys", json={"name": "test", "tier": "free"})
    key = key_resp.json()["key"]

    # Create conversation
    conv_resp = await async_client.post(
        "/v1/memory/conversations",
        json={"session_id": "sess-msg", "title": "Message Test"},
        headers={"Authorization": f"Bearer {key}"},
    )
    conv_id = conv_resp.json()["id"]

    # Add a message
    msg_resp = await async_client.post(
        f"/v1/memory/conversations/{conv_id}/messages",
        json={"role": "user", "content": "Hello, world!", "token_count": 5},
        headers={"Authorization": f"Bearer {key}"},
    )
    assert msg_resp.status_code == 201
    msg_data = msg_resp.json()
    assert msg_data["role"] == "user"
    assert msg_data["content"] == "Hello, world!"
    assert msg_data["token_count"] == 5
    assert msg_data["conversation_id"] == conv_id

    # Add another message
    await async_client.post(
        f"/v1/memory/conversations/{conv_id}/messages",
        json={"role": "assistant", "content": "Hi there!", "token_count": 3},
        headers={"Authorization": f"Bearer {key}"},
    )

    # Get messages
    get_resp = await async_client.get(
        f"/v1/memory/conversations/{conv_id}/messages",
        headers={"Authorization": f"Bearer {key}"},
    )
    assert get_resp.status_code == 200
    messages = get_resp.json()
    assert len(messages) == 2
    roles = {m["role"] for m in messages}
    assert roles == {"user", "assistant"}


@pytest.mark.asyncio
async def test_delete_conversation(async_client: AsyncClient):
    """DELETE /v1/memory/conversations/{id} deletes and returns 404 after."""
    key_resp = await async_client.post("/v1/keys", json={"name": "test", "tier": "free"})
    key = key_resp.json()["key"]

    # Create conversation
    conv_resp = await async_client.post(
        "/v1/memory/conversations",
        json={"session_id": "sess-del", "title": "To Delete"},
        headers={"Authorization": f"Bearer {key}"},
    )
    conv_id = conv_resp.json()["id"]

    # Delete
    del_resp = await async_client.delete(
        f"/v1/memory/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {key}"},
    )
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "deleted"

    # Verify gone (get messages returns 404)
    get_resp = await async_client.get(
        f"/v1/memory/conversations/{conv_id}/messages",
        headers={"Authorization": f"Bearer {key}"},
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_memory_unauthorized(async_client: AsyncClient):
    """Memory endpoints without auth return 401."""
    resp = await async_client.post(
        "/v1/memory/conversations",
        json={"session_id": "s1", "title": "Unauth"},
    )
    assert resp.status_code == 401

    resp = await async_client.get("/v1/memory/conversations")
    assert resp.status_code == 401
