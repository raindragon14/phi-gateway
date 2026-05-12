# Phi AI Gateway

**Agent-First API Platform**

LLM Proxy + Tool Registry (MCP) + Knowledge Base (RAG) + Agent Memory in a single lightweight API. Runs on a 4GB VPS.

<p>
  <a href="#quick-start">Quick Start</a> &middot;
  <a href="#features">Features</a> &middot;
  <a href="https://phiconsulting.biz.id/docs">Documentation</a> &middot;
  <a href="https://phiconsulting.biz.id">Website</a>
</p>

---

## What is Phi AI Gateway?

Phi AI Gateway provides all the primitives AI agents need behind a single API. Instead of stitching together six services, you run one Docker container.

| Primitive | Description |
|---|---|
| **LLM Proxy** | OpenAI-compatible chat completions across 10+ models (OpenAI, Anthropic, Groq, OpenRouter). Streaming, cost tracking, request logging. |
| **Tool Registry** | Register, discover, and execute tools via REST or MCP (JSON-RPC 2.0). JSON Schema contracts for agent-discoverable tools. |
| **Knowledge Base** | Document ingestion with chunking and embedding. Semantic search via cosine similarity with keyword fallback. |
| **Agent Memory** | Persistent conversation storage with session management, pagination, and automatic context window trimming. |

## Hosted or Self-Hosted

Phi AI Gateway is open source (MIT). Run it on your own server for free, or use the hosted version at **[phiconsulting.biz.id](https://phiconsulting.biz.id)** with managed infrastructure, SSL, and support included.

| | Self-Hosted | Cloud |
|---|---|---|
| **License** | MIT, free forever | Managed service |
| **Setup** | `docker compose up` | Instant, no setup |
| **Pricing** | Free | Free tier available, paid plans for scale |
| **Maintenance** | You manage it | Fully managed |

The hosted API is available at `api.phiconsulting.biz.id`. Full documentation at [phiconsulting.biz.id/docs](https://phiconsulting.biz.id/docs).

## Quick Start

```bash
# Clone
git clone https://github.com/raindragon14/phi-gateway
cd phi-gateway

# Install
pip install -e ".[dev]"
cp .env.example .env  # Add your LLM API keys

# Run
uvicorn phi_gateway.main:app --reload
```

Create an API key and start using it:

```bash
# Create a key
curl -X POST http://localhost:8000/v1/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "dev", "tier": "free"}'

# Chat with Groq (free tier)
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer <your-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "groq/llama-3.3-70b",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

Or deploy with Docker:

```bash
docker compose up -d
```

## Features

### LLM Proxy
OpenAI-compatible endpoint with multi-provider routing, SSE streaming, and transparent per-request cost tracking.

### Tool Registry (MCP-Native)
Register tools with JSON Schema contracts. Execute via proxied HTTP calls or the MCP endpoint (`POST /mcp`) with `tools/list` and `tools/call`.

### Knowledge Base
Create knowledge bases, ingest documents with paragraph-aware chunking, generate embeddings via OpenAI, and search with cosine similarity. Falls back to keyword search when embeddings are unavailable.

### Agent Memory
Conversation CRUD with session IDs, paginated message history, and context window management. Returns `X-Context-Truncated` header when old messages are trimmed.

### Dashboard
HTMX + Tailwind CSS admin UI for managing API keys, viewing usage breakdowns by provider and model, and browsing documentation.

## Architecture

```
Caddy (reverse proxy, auto SSL)
  └── FastAPI (2 uvicorn workers, ~300MB RAM)
        ├── /v1/chat         → LLM proxy → OpenAI/Anthropic/Groq/OpenRouter
        ├── /v1/tools        → Tool registry (MCP-native)
        ├── /v1/kb           → RAG (SQLite + cosine similarity)
        ├── /v1/memory       → Agent memory
        ├── /v1/keys         → API key management
        ├── /v1/usage        → Usage analytics
        ├── /mcp             → JSON-RPC 2.0 MCP endpoint
        ├── /dashboard       → HTMX admin UI
        └── /docs            → Swagger UI
              └── SQLite (single file, ~20MB)
```

Idle RAM footprint is approximately 800 MB on a 4GB VPS, leaving roughly 3.2GB of headroom.

## Key Decisions

| Decision | Rationale |
|---|---|
| Python + FastAPI | AI ecosystem, async-native, auto OpenAPI 3.1 |
| SQLite + pure Python vectors | Zero ops, single file, 200MB saved vs external vector DB |
| Caddy reverse proxy | Auto SSL via Let's Encrypt, single binary, ~50MB RAM |
| Proxy-first architecture | 4GB VPS cannot run local LLMs alongside the app; Groq free tier fills the gap |
| MCP protocol from day one | JSON-RPC 2.0, de facto standard for agent-tool communication |
| API-key-only auth | Simple to implement and use, familiar to developers |



## Project Structure

```
phi-gateway/
├── src/phi_gateway/          # Application code
│   ├── api/                  # FastAPI route handlers (10 modules)
│   ├── core/                 # Business logic (LLM proxy, auth, cost, embeddings)
│   ├── dashboard/            # HTMX admin UI templates
│   ├── models/               # SQLAlchemy ORM models (6 tables)
│   ├── schemas/              # Pydantic request/response schemas
│   ├── services/             # Service layer orchestration
│   ├── config.py             # pydantic-settings
│   ├── database.py           # Async SQLAlchemy engine + session
│   ├── dependencies.py       # FastAPI dependency injection
│   └── main.py               # App factory + lifespan
├── srv/landing/              # Landing page
├── tests/                    # pytest suite (unit + integration)
├── alembic/                  # Database migrations (3 revisions)
├── .github/workflows/        # CI/CD (pytest + ruff + Docker build)
├── docker-compose.yml        # Local dev (Caddy + API)
├── docker-compose.vps.yml    # VPS deploy (API only)
├── Dockerfile                # Production build
├── Caddyfile                 # Reverse proxy config
└── pyproject.toml            # Project metadata + tool config
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest -v

# Lint
ruff check src/ tests/

# Run server with auto-reload
uvicorn phi_gateway.main:app --reload
```

## License

MIT. See [LICENSE](LICENSE).

Self-hosting is free forever. [phiconsulting.biz.id](https://phiconsulting.biz.id) provides a managed hosted option if you prefer not to operate your own infrastructure.
