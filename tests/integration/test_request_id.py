"""Integration tests for the X-Request-ID middleware."""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_request_id_generated(async_client: AsyncClient):
    """X-Request-ID header is present in response."""
    response = await async_client.get("/")
    assert "X-Request-ID" in response.headers


@pytest.mark.asyncio
async def test_request_id_echoed_back(async_client: AsyncClient):
    """If client sends X-Request-ID, it's echoed back."""
    custom_id = "my-custom-request-id-12345"
    response = await async_client.get("/", headers={"X-Request-ID": custom_id})
    assert response.headers["X-Request-ID"] == custom_id


@pytest.mark.asyncio
async def test_request_id_is_uuid(async_client: AsyncClient):
    """Generated request ID is a valid UUID."""
    response = await async_client.get("/")
    request_id = response.headers["X-Request-ID"]
    # Should parse as a valid UUID
    parsed = uuid.UUID(request_id)
    assert str(parsed) == request_id
