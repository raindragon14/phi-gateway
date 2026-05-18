"""Main application factory for PhiGateway.

The gateway is self-hosted and fully open source (MIT).
"""

import logging
import time
import uuid
from contextlib import asynccontextmanager

import bcrypt
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from phi_gateway import __version__
from phi_gateway.api.router import api_router
from phi_gateway.config import settings
from phi_gateway.database import async_session, engine, get_db
from phi_gateway.log_config import setup_logging
from phi_gateway.models import Base
from phi_gateway.models.api_key import ApiKey

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

LANDING_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PhiGateway — Self-hosted AI Gateway</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Geist', 'Helvetica Neue', -apple-system, sans-serif;
            background: #000000;
            color: #ededed;
            line-height: 1.6;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            -webkit-font-smoothing: antialiased;
        }
        .page {
            max-width: 960px;
            margin: 0 auto;
            padding: 60px 40px 40px;
            width: 100%;
            flex: 1;
        }
        .hero { margin-bottom: 48px; }
        .hero-brand {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 16px;
        }
        .hero-brand svg { width: 32px; height: 32px; }
        .hero-brand h1 {
            font-size: 22px;
            font-weight: 500;
            letter-spacing: -0.02em;
            color: #ffffff;
        }
        .hero p {
            font-size: 13px;
            color: #a1a1aa;
            max-width: 600px;
        }
        .hero-links {
            display: flex;
            gap: 12px;
            margin-top: 20px;
        }
        .hero-links a {
            font-size: 12px;
            color: #71717a;
            text-decoration: none;
            padding: 6px 14px;
            border: 1px solid #222;
            border-radius: 2px;
            transition: all 120ms cubic-bezier(0.2,0,0,1);
        }
        .hero-links a:hover { color: #fff; border-color: #444; }
        .hero-links a.primary {
            background: #ededed;
            color: #000;
            border-color: #ededed;
        }
        .hero-links a.primary:hover { background: #fff; border-color: #fff; }
        .section-title {
            font-size: 14px;
            font-weight: 600;
            color: #ffffff;
            margin-bottom: 16px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1px;
            background: #222;
            border: 1px solid #222;
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 40px;
        }
        .card {
            background: #0a0a0a;
            padding: 24px;
        }
        .card:hover { background: #0e0e0e; }
        .card h3 {
            font-size: 13px;
            font-weight: 500;
            color: #ffffff;
            margin-bottom: 6px;
        }
        .card p {
            font-size: 12px;
            color: #71717a;
            line-height: 1.5;
        }
        .card .tag {
            display: inline-block;
            font-size: 10px;
            color: #52525b;
            font-family: 'Geist Mono', 'SF Mono', monospace;
            margin-top: 8px;
        }
        .terminal {
            background: #050505;
            border: 1px solid #1f1f1f;
            border-radius: 4px;
            margin-bottom: 40px;
            overflow: hidden;
        }
        .terminal-bar {
            background: #1a1a1a;
            padding: 8px 14px;
            display: flex;
            align-items: center;
            gap: 8px;
            border-bottom: 1px solid #1f1f1f;
        }
        .terminal-dot { width: 8px; height: 8px; border-radius: 50%; }
        .terminal-dot.r { background: #3b3b3b; }
        .terminal-dot.y { background: #3b3b3b; }
        .terminal-dot.g { background: #3b3b3b; }
        .terminal-title {
            font-size: 10px;
            color: #52525b;
            font-family: 'Geist Mono', 'SF Mono', monospace;
            margin-left: auto;
        }
        .terminal-body {
            padding: 16px 20px;
            font-family: 'Geist Mono', 'SF Mono', monospace;
            font-size: 12px;
            line-height: 1.55;
            color: #a1a1aa;
            overflow-x: auto;
        }
        .terminal-body .ps1 { color: #52525b; user-select: none; }
        .terminal-body .ps1::before { content: "$ "; color: #52525b; }
        .terminal-body .cmd { color: #e4e4e7; }
        .terminal-body .comment { color: #3f3f46; }
        .terminal-body .out { color: #a1a1aa; }
        .footer {
            border-top: 1px solid #222;
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 10px;
            color: #3f3f46;
        }
        .footer a { color: #52525b; text-decoration: none; }
        .footer a:hover { color: #71717a; }
        @media (max-width: 720px) {
            .page { padding: 32px 20px; }
            .grid { grid-template-columns: 1fr; }
            .hero-links { flex-direction: column; }
            .footer { flex-direction: column; gap: 8px; }
        }
    </style>
</head>
<body>
    <div class="page">
        <div class="hero">
            <div class="hero-brand">
                <svg viewBox="0 0 32 32"><rect width="32" height="32" rx="4" fill="#0a0a0a" stroke="#222" stroke-width="1"/><text x="16" y="22" text-anchor="middle" font-size="19" font-family="Georgia,serif" font-weight="700" fill="#ededed" font-style="italic">&phi;</text></svg>
                <h1>PhiGateway</h1>
            </div>
            <p>Self-hosted AI gateway &mdash; LLM proxy, tool registry, RAG knowledge base, and agent memory behind one OpenAI-compatible endpoint.</p>
            <div class="hero-links">
                <a href="/docs" class="primary">API Docs</a>
                <a href="/login">Dashboard</a>
                <a href="https://github.com/raindragon14/phi-gateway">GitHub</a>
            </div>
        </div>
        <div class="section-title">Capabilities</div>
        <div class="grid">
            <div class="card">
                <h3>LLM Proxy</h3>
                <p>Route to OpenAI, Anthropic, Groq, or OpenRouter. Switch providers &mdash; or use fallback chains &mdash; without changing agent code.</p>
                <span class="tag">POST /v1/chat/completions</span>
            </div>
            <div class="card">
                <h3>Tool Registry</h3>
                <p>Register tools via JSON schema. Agents discover and call them through REST or MCP (JSON-RPC 2.0). MCP-native.</p>
                <span class="tag">GET /v1/tools</span>
            </div>
            <div class="card">
                <h3>Knowledge Base</h3>
                <p>Chunk, embed, and search documents. Cosine similarity + keyword fallback. No external vector database needed.</p>
                <span class="tag">POST /v1/kb/search</span>
            </div>
            <div class="card">
                <h3>Agent Memory</h3>
                <p>Store conversations, paginate history, auto-trim context. Includes X-Context-Truncated header for token control.</p>
                <span class="tag">GET /v1/memory</span>
            </div>
        </div>
        <div class="section-title">Quick Start</div>
        <div class="terminal">
            <div class="terminal-bar">
                <div class="terminal-dot r"></div>
                <div class="terminal-dot y"></div>
                <div class="terminal-dot g"></div>
                <span class="terminal-title">terminal &mdash; bash</span>
            </div>
            <div class="terminal-body">
                <span class="comment"># Install &amp; start</span><br>
                <span class="ps1"></span><span class="cmd">pip install phi-gateway</span><br>
                <span class="ps1"></span><span class="cmd">uvicorn phi_gateway.main:app</span><br>
                <br>
                <span class="comment"># Create an API key</span><br>
                <span class="ps1"></span><span class="cmd">curl -sX POST</span> <span class="cmd">http://localhost:8000/v1/keys</span> \<br>
                &nbsp;&nbsp;<span class="cmd">-H</span> <span class="comment">"Content-Type: application/json"</span> \<br>
                &nbsp;&nbsp;<span class="cmd">-d</span> <span class="comment">'{"name":"my-agent","tier":"free"}'</span><br>
                <br>
                <span class="comment"># Chat through the gateway</span><br>
                <span class="ps1"></span><span class="cmd">curl -s http://localhost:8000/v1/chat/completions</span> \<br>
                &nbsp;&nbsp;<span class="cmd">-H</span> <span class="comment">"Authorization: Bearer &lt;your-key&gt;"</span> \<br>
                &nbsp;&nbsp;<span class="cmd">-d</span> <span class="comment">'{"model":"groq/llama-3.3-70b","messages":[{"role":"user","content":"Hello"}]}'</span><br>
                <span class="out">{ "choices": [...], "usage": {...} }</span>
            </div>
        </div>
        <div class="section-title">Status</div>
        <div class="terminal">
            <div class="terminal-bar">
                <div class="terminal-dot r"></div>
                <div class="terminal-dot y"></div>
                <div class="terminal-dot g"></div>
                <span class="terminal-title">health &mdash; json</span>
            </div>
            <div class="terminal-body">
                <span class="ps1"></span><span class="cmd">curl -s https://phiconsulting.biz.id/health</span><br>
                <span class="out">{ "status": "ok", "version": "VERSION_PLACEHOLDER", "db_status": "ok" }</span>
            </div>
        </div>
    </div>
    <div class="footer">
        <span>&copy; 2026 PhiGateway &mdash; MIT License</span>
        <a href="https://github.com/raindragon14/phi-gateway">raindragon14/phi-gateway</a>
    </div>
</body>
</html>"""


# ── Lifecycle ──────────────────────────────────────────────────────


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
            result = await session.execute(
                select(ApiKey).where(ApiKey.prefix == settings.INITIAL_ADMIN_KEY[:12])
            )
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

    logger.info("Database tables verified/created")
    yield
    await engine.dispose()
    logger.info("Engine disposed")


# ── App factory ────────────────────────────────────────────────────


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
        # Attach rate-limit headers if set by dependencies.get_api_key()
        rate_headers = getattr(request.state, "rate_limit_headers", None)
        if rate_headers:
            for k, v in rate_headers.items():
                response.headers[k] = v
        return response

    # Request body size limit middleware
    @app.middleware("http")
    async def limit_request_body_size(request: Request, call_next):
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
        return HTMLResponse(content=LANDING_HTML.replace("VERSION_PLACEHOLDER", __version__))

    @app.get("/docs", include_in_schema=False)
    async def api_docs():
        return HTMLResponse(content=SCALAR_HTML)

    return app


app = create_app()
