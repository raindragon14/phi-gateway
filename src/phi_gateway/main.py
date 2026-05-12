from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from phi_gateway import __version__
from phi_gateway.api.router import api_router
from phi_gateway.database import engine
from phi_gateway.models import Base

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: create tables on startup, dispose engine on shutdown."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified/created")
    yield
    await engine.dispose()
    logger.info("Engine disposed")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Phi AI Gateway",
        version=__version__,
        docs_url="/docs",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS — allow all origins for MVP
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routers
    app.include_router(api_router)

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "version": __version__}

    @app.get("/", response_class=HTMLResponse)
    async def landing_page():
        """Serve the landing page at the root."""
        # APP_ROOT is set in Docker to /app; fallback for local dev
        app_root = Path(os.environ.get("APP_ROOT", Path(__file__).resolve().parent.parent.parent))
        landing_path = app_root / "srv" / "landing" / "index.html"
        return HTMLResponse(content=landing_path.read_text(encoding="utf-8"))

    return app


app = create_app()
