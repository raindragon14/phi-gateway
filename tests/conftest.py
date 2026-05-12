import uuid
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from phi_gateway.core.security import generate_api_key
from phi_gateway.database import get_db
from phi_gateway.main import app
from phi_gateway.models import Base
from phi_gateway.models.api_key import ApiKey

TEST_DB_URL = "sqlite+aiosqlite://"


@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh in-memory SQLite database for each test."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    session = session_factory()
    try:
        yield session
    finally:
        await session.close()
        await engine.dispose()


@pytest_asyncio.fixture
async def test_api_key(test_db: AsyncSession) -> tuple[uuid.UUID, str, str]:
    """Create a test API key and return (key_id, full_key, prefix)."""
    full_key, prefix, hashed = generate_api_key()
    api_key = ApiKey(
        key_hash=hashed,
        prefix=prefix,
        name="test-key",
        tier="free",
    )
    test_db.add(api_key)
    await test_db.commit()
    await test_db.refresh(api_key)
    return api_key.id, full_key, prefix


@pytest_asyncio.fixture
async def async_client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client with overridden DB dependency."""
    app.dependency_overrides.clear()

    async def _override_db():
        yield test_db

    app.dependency_overrides[get_db] = _override_db  # type: ignore[assignment]

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
