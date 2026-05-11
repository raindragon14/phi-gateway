# Contributing to Phi AI Gateway

We welcome contributions! Here's how.

## Development Setup

```bash
git clone https://github.com/phiconsulting/phi-gateway
cd phi-gateway
pip install -e ".[dev]"
cp .env.example .env
# Edit .env with API keys (optional — most tests work without them)
```

## Running Tests

```bash
pytest -v
```

## Code Style

```bash
ruff check .
ruff format . --check
```

## Pull Request Process

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Write tests for your changes
4. Ensure all tests pass
5. Run `ruff check .` — zero warnings
6. Open a PR with a clear description

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
├── dashboard/    # HTMX + Tailwind CSS UI templates
├── models/       # SQLAlchemy ORM models
├── schemas/      # Pydantic request/response schemas
├── services/     # Service layer orchestration
├── config.py     # pydantic-settings configuration
├── database.py   # SQLAlchemy async engine + session
├── dependencies.py  # FastAPI dependencies (auth, DB)
└── main.py       # App factory
```

## Architecture Decisions

See `docs/03-decisions.md` for Architecture Decision Records (ADRs).
