# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.1] — 2026-05-20

### Fixed

- **`__version__` sync** — `__init__.py` version now matches `pyproject.toml` (was stale at 0.3.0)

## [0.4.0] — 2026-05-20

### Added

- **SSRF protection** (`core/url_safety.py`) — blocks private/metadata IP ranges on tool endpoints
- **Domain exception hierarchy** (`core/exceptions.py`) — `GatewayError` base with typed subclasses
- **Standardized error responses** (`schemas/errors.py`) — `{detail, id}` envelope across all endpoints
- **Global exception handler** — single handler replaces 7 duplicate handlers in `main.py`
- **MCP endpoint decomposition** — 1 god function split into 4 focused handlers with dispatch table
- **JSON Schema validation** for MCP tool arguments — validates against registered tool schemas
- **Unified auth** (`RequireApiKey` class) — replaces `_require_admin` wrapper, supports tier-based access
- **Google-style docstrings** — enforced across all 52 Python source files via CI
- **HTML docstrings** — all 8 dashboard templates documented with purpose, blocks, JS functions
- **CI enforcement** — docstring check script, em dash grep, ruff format check, parallel pytest
- **jsonschema dependency** — for MCP tool parameter validation

### Changed

- **Error messages sanitized** — LLM proxy errors no longer expose env key names to clients
- **LLM proxy refactored** — extracted `_build_openai_params`, `_build_anthropic_params`, `_route_single`
- **docker-compose.yml** — simplified for VPS (host networking, env_file, no embedded Caddy)
- **CONTRIBUTING.md** — rewritten to match current codebase (CI pipeline, project structure, test structure)
- **.env.example** — cleaned up, added PostgreSQL example, removed marketing copy

### Removed

- **7 duplicate exception handlers** in `main.py` (replaced by single `_gateway_error_handler`)
- **`Response=None` anti-pattern** in `api/memory.py`
- **Inline HTML** from `main.py` (extracted to `dashboard/static_pages.py`)
- **Unused `CONTEXT_WINDOW_BY_ID`** from `models_catalog.py`
- **Non-codebase files**: `docs/`, `assets/`, `DESIGN.md`, `PRODUCTION.md`, `docker-compose.vps.yml`, `scripts/backup-db.sh`
- **Stale `.gitignore` entries** — cleaned up

### Fixed

- **f-string SQL** in `usage_service.py` — replaced with parameterized queries
- **Embedding degradation warnings** — explicit warnings when embedding service unavailable
- **N818 naming** — `RateLimitExceeded` renamed to `RateLimitExceededError`
- **Unused imports** cleaned up (F401)

## [0.3.0] — 2026-05-18

### Added

- **Unified model catalog** (`models_catalog.py`) — single source of truth for model IDs, providers, pricing, and context windows
- **Provider filtering** on `/v1/models` — `?provider=groq` to filter by provider
- **Model search** on `/v1/models` — `?q=llama` to search model names
- **Rate limit headers** — `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` on all API responses
- **v0.3.0 roadmap** in README — Major Refactor milestone

### Changed

- README header: centered `<h1>` with "Phi Gateway" branding
- README model table: expanded to 15 models with pricing, covers OpenAI/Anthropic/Groq/OpenRouter
- README roadmap: v0.3.0 = Major Refactor (done), v0.4.0 = Scalability & Observability, v0.5.0 = Advanced Agent Features
- Rate limiter: `deque` for O(1) popleft (was list with O(n) pop(0))
- `COST_PER_1M_TOKENS` and `KNOWN_MODELS` now derived from `models_catalog.MODELS` — no more duplicate dicts

### Removed

- Dead `CONTEXT_LIMITS` entries from `memory_service.py` (redundant with `models_catalog`)
- Unused `JsonRpcResponse` from `schemas/mcp.py`
- Duplicate pricing dictionaries from `cost_tracker.py` (now imports from `models_catalog`)

### Fixed

- CI: separate coverage job — 70% gate runs on full suite, not per-test-subset
- `.coverage` file added to `.gitignore`

## [0.2.0] — 2026-05-18

### Added

- **PRODUCTION.md** — full production checklist (6 tiers, 30+ items)
- **CONTRIBUTING.md** — comprehensive contributor guide (dev setup, testing, code style, adding providers/endpoints, PR process)
- **Security hardening:** CORS config-driven via `ALLOWED_ORIGINS` env var, security headers middleware (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`), request body size limit (`MAX_REQUEST_BODY_SIZE`)
- **Health endpoint** with DB connectivity probe — returns version, uptime, db_status
- **Docker HEALTHCHECK** — curl to /health, interval 30s
- **Provider fallback chain** — auto-retry across model fallbacks (anthropic→openai→groq→openrouter) with logging at each step
- **Connection pooling** — SQLAlchemy engine tuned (pool_size=10, max_overflow=20, pool_pre_ping=True)
- **Structured JSON logging** via `log_config.py` — request ID middleware, JSON access logs
- **OPS.md** — operations runbook (restart, logs, backup, upgrade, troubleshooting)
- **Backup script** (`scripts/backup-db.sh`) — timestamped SQLite backup, 30-day retention
- **CHANGELOG.md** — this file
- **100-test suite:** 49 unit + 37 integration + 4 production smoke + 10 existing
  - Unit: log_config (5), fallback chain (16), rate limiter (7), config (6)
  - Integration: health (5), security headers (3), request ID (3), body limit (2)
  - Production: wheel build, CLI entry point, version consistency, import verification
- Cross-platform: 46 source files scanned — zero platform-specific code
- PyPI classifiers: Python 3.13, FastAPI, OS Independent

### Changed

- CI workflow: 6-job matrix (lint, unit-test 3.12/3.13, integration-test 3.12/3.13, smoke-test, packaging, build)
- Health endpoint uses `Depends(get_db)` instead of module-level `async_session` (works with test DB overrides)
- Body limit returns `JSONResponse(413)` directly (not `HTTPException` — leaked through Starlette middleware)
- README.md: improved header with badges, quick-start code example, and organized roadmap by version
- Pricing data consolidated into `cost_tracker.py` — single source of truth for all provider costs
- Test suite rewritten: 49 unit + 37 integration + 4 production smoke (up from 10 tests)

### Removed

- **OPS.md** — operations info merged into README.md's Self-Hosting section and PRODUCTION.md
- Dead code: removed unused provider stubs and duplicate pricing dictionaries

### Fixed

- `uvicorn[standard]` → `uvicorn` (uvloop & httptools Linux-only, broke Windows `pip install`)
- Health endpoint `data/` path dependency in CI (now uses injected DB session)

## [0.1.1] — 2026-05-18

### Fixed

- `uvicorn[standard]` → `uvicorn` (uvloop & httptools Linux-only, broke Windows pip install)

## [0.1.0] — 2026-05-18

### Added

- Initial PyPI release of `phi-gateway`
- FastAPI-based LLM proxy with OpenAI, Anthropic, Groq, and OpenRouter support
- MCP (Model Context Protocol) tool registry — register and invoke tools via API
- RAG knowledge base — upload documents, semantic search with embeddings
- Agent memory — persistent conversation memory per session
- API key authentication with tier-based rate limiting
- Usage tracking and cost management per API key
- Built-in SQLite database (single-node deployment)
- Docker Compose setup for easy self-hosting
- Scalar API documentation UI at `/docs`
- CI/CD pipeline via GitHub Actions (ruff, pytest, Docker build)
- PyPI publish workflow triggered on version tags
