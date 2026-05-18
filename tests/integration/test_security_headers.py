"""Integration tests for security headers middleware."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_security_headers_present(async_client: AsyncClient):
    """All responses have X-Content-Type-Options, X-Frame-Options, Referrer-Policy."""
    response = await async_client.get("/")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "Referrer-Policy" in response.headers


@pytest.mark.asyncio
async def test_security_headers_on_health(async_client: AsyncClient):
    """/health has security headers."""
    response = await async_client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


@pytest.mark.asyncio
async def test_security_headers_on_root(async_client: AsyncClient):
    """/ has security headers."""
    response = await async_client.get("/")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
