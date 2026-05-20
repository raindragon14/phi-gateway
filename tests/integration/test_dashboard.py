"""Integration tests for the HTMX dashboard UI routes."""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_overview(
    async_client: AsyncClient,
    admin_api_key: tuple[uuid.UUID, str, str],
):
    """GET /dashboard returns 200 with HTML content."""
    _, full_key, _ = admin_api_key
    resp = await async_client.get(
        "/dashboard",
        headers={"Authorization": f"Bearer {full_key}"},
    )
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


@pytest.mark.asyncio
async def test_dashboard_keys(
    async_client: AsyncClient,
    admin_api_key: tuple[uuid.UUID, str, str],
):
    """GET /dashboard/keys returns 200 with HTML content."""
    _, full_key, _ = admin_api_key
    resp = await async_client.get(
        "/dashboard/keys",
        headers={"Authorization": f"Bearer {full_key}"},
    )
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


@pytest.mark.asyncio
async def test_dashboard_keys_table(
    async_client: AsyncClient,
    admin_api_key: tuple[uuid.UUID, str, str],
):
    """GET /dashboard/keys/table returns 200 with HTML content."""
    _, full_key, _ = admin_api_key
    resp = await async_client.get(
        "/dashboard/keys/table",
        headers={"Authorization": f"Bearer {full_key}"},
    )
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


@pytest.mark.asyncio
async def test_dashboard_usage(
    async_client: AsyncClient,
    admin_api_key: tuple[uuid.UUID, str, str],
):
    """GET /dashboard/usage returns 200 with HTML content."""
    _, full_key, _ = admin_api_key
    resp = await async_client.get(
        "/dashboard/usage",
        headers={"Authorization": f"Bearer {full_key}"},
    )
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


@pytest.mark.asyncio
async def test_dashboard_docs(
    async_client: AsyncClient,
    admin_api_key: tuple[uuid.UUID, str, str],
):
    """GET /dashboard/docs returns 200 with HTML content."""
    _, full_key, _ = admin_api_key
    resp = await async_client.get(
        "/dashboard/docs",
        headers={"Authorization": f"Bearer {full_key}"},
    )
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


@pytest.mark.asyncio
async def test_dashboard_memory(
    async_client: AsyncClient,
    admin_api_key: tuple[uuid.UUID, str, str],
):
    """GET /dashboard/memory returns 200 with HTML content."""
    _, full_key, _ = admin_api_key
    resp = await async_client.get(
        "/dashboard/memory",
        headers={"Authorization": f"Bearer {full_key}"},
    )
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
