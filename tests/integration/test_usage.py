import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from phi_gateway.models.llm_request import LLMRequest


@pytest.mark.asyncio
async def test_usage_unauthorized(async_client: AsyncClient):
    """GET /v1/usage without auth returns 401."""
    response = await async_client.get("/v1/usage")
    assert response.status_code == 401
    assert "Missing" in response.json()["detail"]


@pytest.mark.asyncio
async def test_usage_empty(async_client: AsyncClient):
    """GET /v1/usage with new key returns zero usage."""
    key_resp = await async_client.post("/v1/keys", json={"name": "test", "tier": "free"})
    key = key_resp.json()["key"]

    resp = await async_client.get(
        "/v1/usage",
        headers={"Authorization": f"Bearer {key}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_requests"] == 0
    assert data["total_input_tokens"] == 0
    assert data["total_output_tokens"] == 0
    assert data["total_cost_usd"] == 0.0
    assert data["by_provider"] == []
    assert data["by_model"] == []


@pytest.mark.asyncio
async def test_usage_with_data(async_client: AsyncClient, test_db: AsyncSession):
    """GET /v1/usage reflects inserted LLMRequest rows."""
    # Create a key
    key_resp = await async_client.post("/v1/keys", json={"name": "test", "tier": "free"})
    key_data = key_resp.json()
    key = key_data["key"]
    key_id = uuid.UUID(key_data["id"])

    # Insert LLM request rows directly into the test DB
    requests = [
        LLMRequest(
            id=uuid.uuid4(),
            api_key_id=key_id,
            provider="groq",
            model="llama-3.3-70b",
            input_tokens=1000,
            output_tokens=500,
            cost_usd_micro=1500,
            latency_ms=200,
            status="success",
        ),
        LLMRequest(
            id=uuid.uuid4(),
            api_key_id=key_id,
            provider="openai",
            model="gpt-5-nano",
            input_tokens=200,
            output_tokens=100,
            cost_usd_micro=50,
            latency_ms=150,
            status="success",
        ),
    ]
    for r in requests:
        test_db.add(r)
    await test_db.commit()

    # Query usage
    resp = await async_client.get(
        "/v1/usage",
        headers={"Authorization": f"Bearer {key}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_requests"] == 2
    assert data["total_input_tokens"] == 1200
    assert data["total_output_tokens"] == 600
    assert data["total_cost_usd"] == round(1550 / 1_000_000, 6)

    # Check provider breakdown
    providers = {p["provider"]: p for p in data["by_provider"]}
    assert "groq" in providers
    assert "openai" in providers
    assert providers["groq"]["requests"] == 1

    # Check model breakdown
    models = {m["model"]: m for m in data["by_model"]}
    assert "llama-3.3-70b" in models
    assert "gpt-5-nano" in models
