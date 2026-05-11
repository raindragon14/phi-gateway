import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_overview(async_client: AsyncClient):
    """GET /dashboard returns 200 with HTML content."""
    resp = await async_client.get("/dashboard")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Overview" in resp.text


@pytest.mark.asyncio
async def test_dashboard_keys(async_client: AsyncClient):
    """GET /dashboard/keys returns 200 with HTML content."""
    resp = await async_client.get("/dashboard/keys")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "API Keys" in resp.text


@pytest.mark.asyncio
async def test_dashboard_keys_table(async_client: AsyncClient):
    """GET /dashboard/keys/table returns 200 with HTML content."""
    resp = await async_client.get("/dashboard/keys/table")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


@pytest.mark.asyncio
async def test_dashboard_usage(async_client: AsyncClient):
    """GET /dashboard/usage returns 200 with HTML content."""
    resp = await async_client.get("/dashboard/usage")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Usage" in resp.text


@pytest.mark.asyncio
async def test_dashboard_docs(async_client: AsyncClient):
    """GET /dashboard/docs returns 200 with HTML content."""
    resp = await async_client.get("/dashboard/docs")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


@pytest.mark.asyncio
async def test_dashboard_memory(async_client: AsyncClient):
    """GET /dashboard/memory returns 200 with HTML content."""
    resp = await async_client.get("/dashboard/memory")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Conversations" in resp.text
