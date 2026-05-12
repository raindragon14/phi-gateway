import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from phi_gateway import __version__
from phi_gateway.api.router import api_router
from phi_gateway.database import engine
from phi_gateway.models import Base

logger = logging.getLogger(__name__)

LANDING_TITLE = "Phi AI Gateway - Agent-First API Platform"
LANDING_DESC = "LLM Proxy + Tool Registry + Knowledge Base + Agent Memory. One API, one docker compose up."
LONG_DESC = "LLM Proxy (OpenAI, Anthropic, Groq, OpenRouter) + Tool Registry (MCP-native) + Knowledge Base (RAG with embeddings) + Agent Memory (conversation management). All in one lightweight API."


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: create tables on startup, dispose engine on shutdown."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified/created")
    yield
    await engine.dispose()
    logger.info("Engine disposed")


def _get_landing_html() -> str:
    app_root = Path(os.environ.get("APP_ROOT", Path(__file__).resolve().parent.parent.parent))
    landing_path = app_root / "srv" / "landing" / "index.html"
    return landing_path.read_text(encoding="utf-8")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Phi AI Gateway",
        description=LONG_DESC,
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    @app.get("/favicon.ico")
    async def favicon():
        """Serve SVG favicon inline."""
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
            '<rect width="32" height="32" rx="6" fill="#6366f1"/>'
            '<text x="16" y="23" text-anchor="middle" font-size="22" '
            'font-family="system-ui" font-weight="700" fill="#fff">'
            '&phi;</text></svg>'
        )
        from fastapi.responses import Response
        return Response(content=svg, media_type="image/svg+xml")

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "version": __version__}

    @app.get("/", response_class=HTMLResponse)
    async def root(request: Request):
        """Landing page on main domain, API info on api subdomain."""
        host = request.headers.get("host", "")
        if host.startswith("api."):
            return _api_root_response()
        return HTMLResponse(content=_get_landing_html())

    return app


def _api_root_response() -> JSONResponse:
    return JSONResponse(content={
        "name": "Phi AI Gateway",
        "version": __version__,
        "description": LANDING_DESC,
        "docs": "https://phiconsulting.biz.id/docs",
        "redoc": "https://phiconsulting.biz.id/redoc",
        "health": "/health",
        "endpoints": {
            "chat": "/v1/chat/completions",
            "models": "/v1/models",
            "embeddings": "/v1/embeddings",
            "tools": "/v1/tools",
            "knowledge_base": "/v1/kb",
            "memory": "/v1/memory",
            "keys": "/v1/keys",
            "usage": "/v1/usage",
            "mcp": "/mcp",
        },
    })


app = create_app()
