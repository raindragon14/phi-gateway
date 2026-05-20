"""Database engine, session factory, and connection pool.

Provides the async SQLAlchemy engine and a FastAPI-compatible
dependency generator for per-request database sessions.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from phi_gateway.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)
"""Async SQLAlchemy engine, configured from ``settings.DATABASE_URL``."""

async_session = async_sessionmaker(engine, expire_on_commit=False)
"""Session factory bound to the engine. Sessions do not expire on commit."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a per-request async database session.

    Intended for use as a FastAPI dependency. The session is
    automatically closed when the request finishes, even on errors.

    Yields:
        AsyncSession: A new SQLAlchemy async session.

    Example:
        >>> @app.get("/data")
        ... async def endpoint(db: AsyncSession = Depends(get_db)):
        ...     ...
    """
    session = async_session()
    try:
        yield session
    finally:
        await session.close()
