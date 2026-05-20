# Contributing to PhiGateway

Thank you for considering a contribution to PhiGateway. This guide covers everything you need to set up your development environment, run tests, and submit changes.

## Development Setup

### Prerequisites

- Python 3.12+ (3.13 recommended)
- Git
- Docker & Docker Compose (optional, for integration testing)

### Quick Start

```bash
# 1. Fork and clone
git clone https://github.com/raindragon14/phi-gateway
cd phi-gateway

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install with dev dependencies
pip install -e ".[dev]"

# 4. Copy environment config
cp .env.example .env
# Edit .env with your API keys (optional — most tests work without them)

# 5. Run the test suite to verify setup
pytest -v
```

Tests use an in-memory SQLite database — no external services required.

### Running the Server Locally

```bash
uvicorn phi_gateway.main:app --reload --port 8000
# Open http://localhost:8000/docs for interactive API docs
```

## Running Tests

```bash
# Full suite (unit + integration + production smoke)
pytest -v

# Unit tests only (fast, no DB)
pytest tests/unit/ -v

# Integration tests (use in-memory SQLite)
pytest tests/integration/ -v

# Production smoke tests (wheel build, CLI, imports)
pytest tests/production/ -v

# With coverage report
pytest --cov=phi_gateway --cov-report=term-missing

# Single test file
pytest tests/unit/test_cost_tracker.py -v

# Single test function
pytest tests/unit/test_cost_tracker.py::test_pricing_calculation -v
```

### Test Structure

```
tests/
├── conftest.py          # Shared fixtures (test DB, async client, test key)
├── unit/                # Fast, isolated tests (no DB, no network)
│   ├── test_cost_tracker.py
│   ├── test_llm_proxy_fallback.py
│   ├── test_log_config.py
│   ├── test_rate_limiter.py
│   ├── test_config.py
│   └── test_security.py
├── integration/         # Tests that use the full app (in-memory DB)
│   ├── test_chat.py
│   ├── test_keys.py
│   ├── test_kb.py
│   ├── test_memory.py
│   ├── test_tools.py
│   ├── test_mcp.py
│   ├── test_usage.py
│   ├── test_health.py
│   ├── test_security_headers.py
│   ├── test_body_limit.py
│   ├── test_request_id.py
│   ├── test_embeddings.py
│   └── test_dashboard.py
└── production/          # Smoke tests (wheel, CLI, imports)
    └── test_smoke.py
```

## Code Style

We use [Ruff](https://github.com/astral-sh/ruff) for linting. Configuration is in `pyproject.toml`:

```toml
[tool.ruff]
target-version = "py312"
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]  # Errors, pyflakes, isort, naming, warnings
```

Run before committing:

```bash
# Check for lint errors
ruff check src/ tests/

# Auto-fix formatting issues
ruff check --fix src/ tests/

# Format code
ruff format src/ tests/
```

**Rules:**
- Line length: **120 characters**
- Import sorting: automatic via Ruff (isort-compatible)
- No unused imports (`F` rule)
- Naming conventions (`N` rule): `snake_case` for functions/variables, `PascalCase` for classes

## CI Pipeline

GitHub Actions runs on every push and PR:

| Job | Tool | Requirement |
|-----|------|-------------|
| **Lint** | `ruff check` | Zero warnings |
| **Unit tests** | `pytest tests/unit/` | All pass (Python 3.12 + 3.13) |
| **Integration tests** | `pytest tests/integration/` | All pass (Python 3.12 + 3.13) |
| **Smoke tests** | `pytest tests/production/` | All pass |
| **Build** | `python -m build` | Wheel builds successfully |
| **Docker** | `docker build` | Image builds on linux/amd64 |

## Adding a New LLM Provider

PhiGateway's LLM proxy routes requests to providers based on the model string prefix. To add a new provider:

### 1. Add the provider client

Create a new file in `src/phi_gateway/core/` following the existing pattern:

```python
# src/phi_gateway/core/new_provider.py

import httpx

class NewProviderClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.newprovider.com/v1"

    async def chat_completion(self, model: str, messages: list, **kwargs) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": model, "messages": messages, **kwargs},
            )
            response.raise_for_status()
            return response.json()
```

### 2. Register the provider

In `src/phi_gateway/core/llm_proxy.py`, add the provider to the routing map. The model string prefix (e.g., `newprovider/model-name`) determines which client handles the request.

### 3. Add configuration

Add the API key to `src/phi_gateway/config.py`:

```python
NEWPROVIDER_API_KEY: str = ""
```

And to `.env.example`:

```env
NEWPROVIDER_API_KEY=your-key-here
```

### 4. Add tests

Write tests in `tests/unit/test_llm_proxy_fallback.py` or create a new test file. Mock the HTTP client — don't call the real API.

### 5. Update documentation

- Add the provider to the model table in `README.md`
- Document any provider-specific quirks

## Adding a New API Endpoint

### 1. Create the route module

Add a new file in `src/phi_gateway/api/`:

```python
# src/phi_gateway/api/my_feature.py

from fastapi import APIRouter, Depends
from phi_gateway.dependencies import get_current_key

router = APIRouter(prefix="/v1/my-feature", tags=["My Feature"])

@router.get("/")
async def list_items(api_key=Depends(get_current_key)):
    return {"items": []}
```

### 2. Register the router

In `src/phi_gateway/api/router.py`, include your new router:

```python
from phi_gateway.api.my_feature import router as my_feature_router

app.include_router(my_feature_router)
```

### 3. Add schemas (if needed)

Define request/response models in `src/phi_gateway/schemas/`.

### 4. Add database models (if needed)

Define SQLAlchemy models in `src/phi_gateway/models/` and create an Alembic migration:

```bash
alembic revision --autogenerate -m "add my_feature table"
alembic upgrade head
```

### 5. Write tests

Add integration tests in `tests/integration/test_my_feature.py`. Use the existing `conftest.py` fixtures for the test database and authenticated client.

## Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: <short description>

<optional body>

<optional footer>
```

**Types:**

| Type | When to use |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `test` | Adding or updating tests |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `perf` | Performance improvement |
| `chore` | Build process, CI, tooling, dependencies |
| `style` | Formatting, whitespace (no logic change) |

**Examples:**

```
feat: add webhook callback support for tool execution
fix: handle empty document ingest in knowledge base
docs: update quick-start guide for Docker Compose v2
test: add integration tests for MCP tool discovery
refactor: consolidate pricing data into cost_tracker.py
chore: bump fastapi to 0.115.0
```

**Breaking changes:** Append `!` after the type:

```
feat!: change /v1/tools response schema
```

## Pull Request Process

1. **Fork** the repository and create a feature branch:
   ```bash
   git checkout -b feat/my-feature
   ```

2. **Write code** following the style guide above.

3. **Write tests** for your changes. Aim for the same test categories:
   - Unit tests for isolated logic
   - Integration tests for API behavior

4. **Run the full test suite:**
   ```bash
   ruff check src/ tests/
   pytest -v
   ```

5. **Commit** with a conventional commit message.

6. **Push** and open a PR against `main` with:
   - A clear title matching the commit convention
   - A description explaining *what* and *why*
   - Reference any related issues (`Closes #42`)

7. **CI must pass** before merging. The maintainer will review and may request changes.

## Project Structure

```
phi-gateway/
├── src/phi_gateway/
│   ├── api/                  # FastAPI route handlers (12 modules)
│   │   ├── chat.py           # /v1/chat/completions — LLM proxy
│   │   ├── keys.py           # /v1/keys — API key CRUD
│   │   ├── knowledge.py      # /v1/kb — knowledge base + search
│   │   ├── memory.py         # /v1/memory — agent memory
│   │   ├── tools.py          # /v1/tools — tool registry
│   │   ├── mcp.py            # /mcp — JSON-RPC 2.0 (MCP)
│   │   ├── usage.py          # /v1/usage — cost analytics
│   │   ├── embeddings.py     # /v1/embeddings — embedding API
│   │   ├── models.py         # /v1/models — model listing
│   │   ├── dashboard.py      # /dashboard — HTMX admin UI
│   │   └── router.py         # Router registry
│   ├── core/                 # Business logic
│   │   ├── llm_proxy.py      # Multi-provider LLM routing
│   │   ├── cost_tracker.py   # Pricing data + cost calculation
│   │   ├── rate_limiter.py   # In-memory rate limiting
│   │   ├── embedding.py      # Embedding generation + search
│   │   └── security.py       # Password hashing, key generation
│   ├── dashboard/templates/  # HTMX admin UI templates
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas/              # Pydantic request/response schemas
│   ├── services/             # Business logic orchestration
│   ├── config.py             # pydantic-settings configuration
│   ├── database.py           # Async SQLAlchemy engine + session
│   ├── dependencies.py       # FastAPI dependencies (auth, rate limiting)
│   ├── log_config.py         # Structured JSON logging
│   └── main.py               # App factory + lifespan
├── tests/                    # pytest suite
├── alembic/                  # Database migrations
├── scripts/                  # CI helpers (docstring check)
├── CHANGELOG.md              # Release history
├── CONTRIBUTING.md           # This file
├── Dockerfile                # Production container build
├── docker-compose.yml        # Local development setup
└── pyproject.toml            # Package metadata + tool config
```

## Questions?

Open a [GitHub Discussion](https://github.com/raindragon14/phi-gateway/discussions) or file an [Issue](https://github.com/raindragon14/phi-gateway/issues).
