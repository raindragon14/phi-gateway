"""Integration tests for the /health endpoint."""

import pytest
from httpx import AsyncClient

from phi_gateway import __version__


@pytest.mark.asyncio
async def test_health_status_ok(async_client: AsyncClient):
    """GET /health returns 200 with all required fields and status 'ok'."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["db_status"] == "ok"
    assert "version" in data
    assert data["version"] == __version__
    assert "uptime" in data
    assert isinstance(data["uptime"], (int, float))
    assert data["uptime"] >= 0
