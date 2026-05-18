"""Main application factory for PhiGateway.

The gateway is self-hosted and fully open source (MIT).
"""

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from sqlalchemy import text

from phi_gateway import __version__
from phi_gateway.api.router import api_router
from phi_gateway.config import settings
from phi_gateway.database import async_session, engine
from phi_gateway.log_config import setup_logging
from phi_gateway.models import Base

logger = logging.getLogger(__name__)

START_TIME = time.time()

SCALAR_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PhiGateway — API Reference</title>
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


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    # Apply structured JSON logging config before any loggers are used
    setup_logging()

    app = FastAPI(
        title="PhiGateway",
        description="LLM proxy + MCP tool registry + RAG knowledge base + agent memory. One API, zero lock-in.",
        version=__version__,
        docs_url=None,
        redoc_url=None,
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Inject unique request_id into each request for log correlation
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # Parse allowed origins from config
    allowed_origins = (
        ["*"]
        if settings.ALLOWED_ORIGINS == "*"
        else [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()]
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Security headers middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    # Request body size limit middleware
    @app.middleware("http")
    async def limit_request_body_size(request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > settings.MAX_REQUEST_BODY_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Request body too large. Max size: {settings.MAX_REQUEST_BODY_SIZE} bytes",
                    )
            except ValueError:
                pass
        response = await call_next(request)
        return response

    app.include_router(api_router)

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        return Response(content=FAVICON_SVG, media_type="image/svg+xml")

    @app.get("/health", include_in_schema=False)
    async def health_check():
        """Health check endpoint with database connectivity probe."""
        uptime_seconds = time.time() - START_TIME
        db_status = "ok"
        try:
            async with async_session() as session:
                await session.execute(text("SELECT 1"))
        except Exception:
            db_status = "degraded"

        status_code = 200 if db_status == "ok" else 503
        return JSONResponse(
            status_code=status_code,
            content={
                "status": "ok" if db_status == "ok" else "degraded",
                "version": __version__,
                "db_status": db_status,
                "uptime": round(uptime_seconds, 2),
            },
        )

    @app.get("/", include_in_schema=False)
    async def root():
        return JSONResponse({
            "service": "PhiGateway",
            "version": __version__,
            "description": "Self-hosted AI gateway — LLM proxy, MCP tool registry, RAG knowledge base, agent memory.",
            "docs": "/docs",
            "openapi": "/openapi.json",
            "health": "/health",
        })

    @app.get("/docs", include_in_schema=False)
    async def api_docs():
        return HTMLResponse(content=SCALAR_HTML)

    return app


app = create_app()
