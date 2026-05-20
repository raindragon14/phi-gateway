"""Main application factory for PhiGateway.

The gateway is self-hosted and fully open source (MIT).
"""

import logging
import time
import uuid
from contextlib import asynccontextmanager

import bcrypt
from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from phi_gateway import __version__
from phi_gateway.api.router import api_router
from phi_gateway.config import settings
from phi_gateway.core.exceptions import (
    ConflictError,
    ExternalToolError,
    ExternalToolTimeoutError,
    NotFoundError,
    RateLimitExceededError,
    ValidationError,
)
from phi_gateway.dashboard.static_pages import FAVICON_SVG, LANDING_HTML, SCALAR_HTML
from phi_gateway.database import async_session, engine, get_db
from phi_gateway.log_config import setup_logging
from phi_gateway.models import Base
from phi_gateway.models.api_key import ApiKey
from phi_gateway.schemas.errors import ErrorDetail

logger = logging.getLogger(__name__)

START_TIME = time.time()  # App start timestamp : used by /health for uptime


# ── Lifecycle


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: create tables on startup, dispose engine on shutdown.

    If ``INITIAL_ADMIN_KEY`` is configured in the environment, seed an admin
    API key on first startup so ``/v1/keys`` can be protected from
    unauthenticated access.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Bootstrap initial admin key if configured
    if settings.INITIAL_ADMIN_KEY:
        async with async_session() as session:
            result = await session.execute(select(ApiKey).where(ApiKey.prefix == settings.INITIAL_ADMIN_KEY[:12]))
            existing = result.scalar_one_or_none()
            if not existing:
                full_key = settings.INITIAL_ADMIN_KEY
                hashed = bcrypt.hashpw(full_key.encode(), bcrypt.gensalt()).decode()
                admin_key = ApiKey(
                    key_hash=hashed,
                    prefix=full_key[:12],
                    name="initial-admin",
                    tier="admin",
                    rate_limit_per_min=1000,
                    rate_limit_per_day=500000,
                )
                session.add(admin_key)
                await session.commit()
                logger.info("Seeded initial admin API key from INITIAL_ADMIN_KEY")
            else:
                logger.debug("Initial admin API key already exists, skipping seed")

    # ── Config validation warnings ──
    if not settings.ALLOWED_ORIGINS:
        logger.warning(
            "ALLOWED_ORIGINS is empty : CORS is disabled. Set ALLOWED_ORIGINS in .env to enable cross-origin requests."
        )
    if settings.SESSION_SECRET in ("", "change-me-in-production"):
        logger.warning("SESSION_SECRET is set to a default value. Set a strong random value in .env for production.")

    logger.info("Database tables verified/created")
    yield
    await engine.dispose()
    logger.info("Engine disposed")


# ── App factory ────────────────────────────────────────────────────


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Sets up middleware stack (request ID, CORS, security headers,
    body size limits), mounts API routes, and registers landing
    page, health check, favicon, and API docs endpoints.

    Returns:
        FastAPI: Fully configured application instance.
    """
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
        """Middleware: attach a unique ``X-Request-ID`` to every request/response.

        Reads from ``X-Request-ID`` request header if present,
        otherwise generates a UUID. Echoes the ID back in the response
        for client-side correlation.
        """
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

    # CORS : only register if origins are explicitly configured
    if allowed_origins:
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
        """Middleware: inject OWASP-recommended security headers.

        Adds ``X-Content-Type-Options``, ``X-Frame-Options``, and
        ``Referrer-Policy``. Also attaches rate-limit headers if
        set by ``get_api_key`` on ``request.state``.
        """
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Attach rate-limit headers if set by dependencies.get_api_key()
        rate_headers = getattr(request.state, "rate_limit_headers", None)
        if rate_headers:
            for k, v in rate_headers.items():
                response.headers[k] = v
        return response

    # Request body size limit middleware
    @app.middleware("http")
    async def limit_request_body_size(request: Request, call_next):
        """Middleware: reject requests exceeding ``MAX_REQUEST_BODY_SIZE``.

        Checks the ``Content-Length`` header and returns HTTP 413
        before the body is read, saving server resources.
        """
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > settings.MAX_REQUEST_BODY_SIZE:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": f"Request body too large. Max size: {settings.MAX_REQUEST_BODY_SIZE} bytes",
                        },
                    )
            except ValueError:
                pass
        response = await call_next(request)
        return response

    app.include_router(api_router)

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        """Serve the PhiGateway favicon as inline SVG."""
        return Response(content=FAVICON_SVG, media_type="image/svg+xml")

    @app.get("/health", include_in_schema=False)
    async def health_check(db: AsyncSession = Depends(get_db)):
        """Health check endpoint with database connectivity probe."""
        uptime_seconds = time.time() - START_TIME
        db_status = "ok"
        try:
            await db.execute(text("SELECT 1"))
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
        """Serve the landing page with version-substituted HTML."""
        return HTMLResponse(content=LANDING_HTML.replace("VERSION_PLACEHOLDER", __version__))

    @app.get("/docs", include_in_schema=False)
    async def api_docs():
        """Serve the Scalar API documentation UI."""
        return HTMLResponse(content=SCALAR_HTML)

    # ── Global exception handlers ─────────────────────────────────
    @app.exception_handler(FastAPIHTTPException)
    async def http_exception_handler(request: Request, exc: FastAPIHTTPException):
        """Return all HTTP errors in the standard ``ErrorDetail`` envelope."""
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorDetail(
                detail=exc.detail,
                id=request_id,
            ).model_dump(exclude_none=True),
            headers=exc.headers or None,
        )

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError):
        """Map ``NotFoundError`` to HTTP 404."""
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=404,
            content=ErrorDetail(detail=str(exc), id=request_id).model_dump(exclude_none=True),
        )

    @app.exception_handler(ConflictError)
    async def conflict_handler(request: Request, exc: ConflictError):
        """Map ``ConflictError`` to HTTP 409."""
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=409,
            content=ErrorDetail(detail=str(exc), id=request_id).model_dump(exclude_none=True),
        )

    @app.exception_handler(ValidationError)
    async def validation_handler(request: Request, exc: ValidationError):
        """Map ``ValidationError`` to HTTP 400."""
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=400,
            content=ErrorDetail(detail=str(exc), id=request_id).model_dump(exclude_none=True),
        )

    @app.exception_handler(ExternalToolTimeoutError)
    async def tool_timeout_handler(request: Request, exc: ExternalToolTimeoutError):
        """Map ``ExternalToolTimeoutError`` to HTTP 504."""
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=504,
            content=ErrorDetail(detail=str(exc), id=request_id).model_dump(exclude_none=True),
        )

    @app.exception_handler(ExternalToolError)
    async def tool_error_handler(request: Request, exc: ExternalToolError):
        """Map ``ExternalToolError`` to HTTP 502."""
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=502,
            content=ErrorDetail(detail=str(exc), id=request_id).model_dump(exclude_none=True),
        )

    @app.exception_handler(RateLimitExceededError)
    async def rate_limit_handler(request: Request, exc: RateLimitExceededError):
        """Map ``RateLimitExceededError`` to HTTP 429 with Retry-After header."""
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=429,
            content=ErrorDetail(detail=str(exc), id=request_id).model_dump(exclude_none=True),
            headers={"Retry-After": str(exc.retry_after)},
        )

    return app


app = create_app()  # Module-level FastAPI instance imported by uvicorn and tests
