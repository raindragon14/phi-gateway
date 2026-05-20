# Contributing to PhiGateway

## Development Setup

```bash
git clone https://github.com/raindragon14/phi-gateway
cd phi-gateway
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
pytest -v
```

Tests use in-memory SQLite. No external services required.

## Code Style

**Ruff** for linting and formatting. Config in `pyproject.toml`:

```bash
ruff format --check src/ tests/   # formatting
ruff check src/ tests/            # linting
```

Rules: `E`, `F`, `I`, `N`, `W`, `D100`, `D103`, `D107`
Line length: 120. No unused imports. snake_case functions, PascalCase classes.

**Docstrings:** Google style (mandatory for all public functions, classes, modules).

```python
def create_kb(name: str, db: AsyncSession) -> KnowledgeBaseResponse:
    """Create a new knowledge base.

    Args:
        name: Display name for the knowledge base.
        db: Async database session.

    Returns:
        The newly created ``KnowledgeBaseResponse``.

    Raises:
        ValueError: If the name is empty.
    """
```

Enforced by `scripts/check_docstrings.py` in CI. One-liner docstrings OK for
framework patterns and zero-arg functions.

## CI Pipeline

GitHub Actions runs on every push to `main`/`staging` and on PRs:

| Job | What it checks |
|-----|----------------|
| **lint** | `ruff format --check`, `ruff check`, Google-style docstring script, em dash grep, mypy (info only) |
| **tests** | `pytest tests/ -n auto` with coverage (Python 3.12 + 3.13 matrix) |
| **smoke-test** | Wheel build, `phi-gateway --help`, import check, production tests |
| **packaging** | sdist + wheel build, `twine check` |
| **build** | Docker image build (push to main/staging only) |

## Tests

```bash
pytest -v                                    # full suite
pytest tests/unit/ -v                        # unit only (fast, no DB)
pytest tests/integration/ -v                 # integration (in-memory DB)
pytest tests/production/ -v                  # smoke (wheel, CLI)
pytest --cov=phi_gateway --cov-report=term-missing  # with coverage
```

```
tests/
├── conftest.py               # Shared fixtures (test_db, test_api_key, admin_api_key, async_client)
├── unit/
│   ├── test_config.py
│   ├── test_cost_tracker.py
│   ├── test_llm_proxy_fallback.py
│   ├── test_log_config.py
│   ├── test_models_catalog.py
│   ├── test_rate_limiter.py
│   └── test_security.py
├── integration/
│   ├── test_api_flow.py
│   ├── test_body_limit.py
│   ├── test_chat.py
│   ├── test_dashboard.py
│   ├── test_embeddings.py
│   ├── test_error_handling.py
│   ├── test_health.py
│   ├── test_kb.py
│   ├── test_keys.py
│   ├── test_mcp.py
│   ├── test_memory.py
│   ├── test_request_id.py
│   ├── test_security_headers.py
│   ├── test_tools.py
│   └── test_usage.py
└── production/
    └── test_smoke.py
```

## Branch Workflow

1. Create feature branch from `main`
2. Commit with conventional commit message
3. Open PR against `main`
4. CI must pass
5. Maintainer merges via staging (staging -> CI green -> fast-forward to main)

## Commit Convention

[Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add webhook callback support for tool execution
fix: handle empty document ingest in knowledge base
refactor: consolidate pricing data into cost_tracker.py
chore: bump fastapi to 0.115.0
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `chore`, `style`.
Breaking changes: append `!` after type (`feat!: change /v1/tools response schema`).

## Project Structure

```
phi-gateway/
├── src/phi_gateway/
│   ├── api/                    # FastAPI route handlers
│   │   ├── chat.py             # POST /v1/chat/completions
│   │   ├── embeddings.py       # POST /v1/embeddings
│   │   ├── keys.py             # CRUD /v1/keys
│   │   ├── knowledge.py        # CRUD /v1/kb + search
│   │   ├── mcp.py              # POST /mcp (JSON-RPC 2.0)
│   │   ├── memory.py           # CRUD /v1/memory
│   │   ├── models.py           # GET /v1/models
│   │   ├── tools.py            # CRUD /v1/tools
│   │   ├── usage.py            # GET /v1/usage
│   │   ├── dashboard.py        # HTMX admin UI routes
│   │   └── router.py           # Router aggregation
│   ├── core/                   # Business logic (no DB)
│   │   ├── llm_proxy.py        # Multi-provider routing + fallback
│   │   ├── cost_tracker.py     # Cost calculation
│   │   ├── embedding.py        # Embedding generation
│   │   ├── rate_limiter.py     # Sliding window rate limiting
│   │   ├── security.py         # API key generation + bcrypt
│   │   ├── url_safety.py       # SSRF protection
│   │   └── exceptions.py       # Domain exception hierarchy
│   ├── models/                 # SQLAlchemy ORM models
│   ├── schemas/                # Pydantic request/response schemas
│   │   └── errors.py           # ErrorResponse model
│   ├── services/               # Service layer (DB + business logic)
│   ├── dashboard/
│   │   ├── static_pages.py     # Landing page + Scalar API docs (inline HTML)
│   │   └── templates/          # Jinja2 HTML templates
│   ├── config.py               # pydantic-settings
│   ├── database.py             # Async SQLAlchemy engine + session
│   ├── dependencies.py         # FastAPI deps (auth, rate limiting)
│   ├── log_config.py           # Structured JSON logging
│   ├── main.py                 # App factory, middleware, lifespan
│   └── models_catalog.py       # Model + pricing catalog
├── tests/
├── alembic/                    # Database migrations
├── scripts/                    # CI helpers (docstring check)
├── Dockerfile                  # Production container
├── docker-compose.yml          # Local development
├── entrypoint.sh               # Docker entrypoint (runs migrations + uvicorn)
├── Caddyfile                   # Dev reverse proxy config
└── pyproject.toml              # Package config, deps, tool settings
```

## Questions?

Open a [GitHub Discussion](https://github.com/raindragon14/phi-gateway/discussions) or file an [Issue](https://github.com/raindragon14/phi-gateway/issues).
