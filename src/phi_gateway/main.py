import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response

from phi_gateway import __version__
from phi_gateway.api.router import api_router
from phi_gateway.database import engine
from phi_gateway.models import Base

logger = logging.getLogger(__name__)

LANDING_DESC = (
    "LLM Proxy + Tool Registry + Knowledge Base + Agent Memory. "
    "One API, one docker compose up."
)
LONG_DESC = (
    "LLM Proxy (OpenAI, Anthropic, Groq, OpenRouter) + "
    "Tool Registry (MCP-native, JSON-RPC 2.0) + "
    "Knowledge Base (RAG with embeddings, cosine similarity) + "
    "Agent Memory (conversation storage, context window management). "
    "All in one lightweight API."
)

SCALAR_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Phi AI Gateway - API Reference</title>
    <style>body{margin:0;padding:0;background:#0a0a0f}</style>
</head>
<body>
    <script id="api-reference" data-url="/openapi.json"
        data-configuration='{"spec":{"content":""},"darkMode":true,"hideClientButton":false,"defaultHttpClient":{"targetKey":"shell","clientKey":"curl"}}'></script>
    <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference@1"></script>
</body>
</html>"""

FAVICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
    '<rect width="32" height="32" rx="4" fill="#0a0a0a" stroke="#222" stroke-width="1"/>'
    '<text x="16" y="22" text-anchor="middle" font-size="19" '
    'font-family="Georgia,serif" font-weight="700" fill="#ededed" font-style="italic">&phi;</text>'
    '</svg>'
)


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
        docs_url=None,
        redoc_url=None,
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

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        return Response(content=FAVICON_SVG, media_type="image/svg+xml")

    @app.get("/health", include_in_schema=False)
    async def health_check():
        return {"status": "ok", "version": __version__}

    @app.get("/", include_in_schema=False)
    async def root(request: Request):
        host = request.headers.get("host", "")
        if host.startswith("api."):
            return _api_root_response()
        return HTMLResponse(content=_get_landing_html())

    @app.get("/docs", include_in_schema=False)
    async def api_docs():
        return HTMLResponse(content=SCALAR_HTML)

    return app


def _api_root_response() -> JSONResponse:
    return JSONResponse(content={
        "name": "Phi AI Gateway",
        "version": __version__,
        "description": LANDING_DESC,
        "docs": "https://phiconsulting.biz.id/docs",
        "openapi": "https://phiconsulting.biz.id/openapi.json",
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
