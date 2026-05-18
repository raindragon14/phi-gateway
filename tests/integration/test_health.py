"""Integration tests for the /health endpoint."""

import pytest
from httpx import AsyncClient

from phi_gateway import __version__


@pytest.mark.asyncio
async def test_health_returns_200(async_client: AsyncClient):
    """GET /health returns 200."""
    response = await async_client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_has_required_fields(async_client: AsyncClient):
    """Response contains status, version, db_status, uptime."""
    response = await async_client.get("/health")
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "db_status" in data
    assert "uptime" in data


@pytest.mark.asyncio
async def test_health_status_ok(async_client: AsyncClient):
    """Status field is 'ok' when DB is reachable."""
    response = await async_client.get("/health")
    data = response.json()
    assert data["status"] == "ok"
    assert data["db_status"] == "ok"


@pytest.mark.asyncio
async def test_health_version_matches(async_client: AsyncClient):
    """Version matches __version__."""
    response = await async_client.get("/health")
    data = response.json()
    assert data["version"] == __version__


@pytest.mark.asyncio
async def test_health_uptime_is_numeric(async_client: AsyncClient):
    """Uptime is a number >= 0."""
    response = await async_client.get("/health")
    data = response.json()
    assert isinstance(data["uptime"], (int, float))
    assert data["uptime"] >= 0
