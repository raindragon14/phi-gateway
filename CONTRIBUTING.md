# Contributing to Phi AI Gateway

We welcome contributions! Here's how to get started.

## Development Setup

```bash
git clone https://github.com/raindragon14/phi-gateway
cd phi-gateway
pip install -e ".[dev]"
cp .env.example .env
# Edit .env with API keys (optional — most tests work without them)
```

## Running Tests

```bash
pytest -v
```

Tests use an in-memory SQLite database — no setup required.

## Code Quality

We use ruff for linting. Run before committing:

```bash
ruff check src/ tests/
```

CI (GitHub Actions) runs on every push and PR:
- **Lint**: `ruff check` — must pass with zero warnings
- **Type check**: `mypy` — informational (warnings allowed for now)
- **Tests**: `pytest` — all tests must pass
- **Build**: Docker image build verification (on main/staging push)

## Pull Request Process

1. Fork the repo and create a feature branch:
   ```bash
   git checkout -b feature/my-feature
   ```
2. Write tests for your changes
3. Run `ruff check .` — zero warnings
4. Run `pytest -v` — all tests must pass
5. Open a PR with a clear description of what and why

## Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add vector search endpoint
fix: handle empty document ingest
docs: update quick-start guide
chore: bump dependencies
```

## Project Structure

```
src/phi_gateway/
├── api/          # FastAPI route handlers
├── core/         # Business logic (auth, LLM proxy, cost tracking)
├── dashboard/    # HTMX admin UI templates
├── models/       # SQLAlchemy ORM models
├── schemas/      # Pydantic request/response schemas
├── services/     # Service layer orchestration
├── config.py     # pydantic-settings configuration
├── database.py   # SQLAlchemy async engine + session
├── dependencies.py  # FastAPI dependencies (auth, DB)
└── main.py       # App factory + lifespan
```

## Architecture Decisions

See `docs/03-decisions.md` for Architecture Decision Records (ADRs).
