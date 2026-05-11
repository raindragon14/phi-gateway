<div align="center">
  <h1>φ Phi AI Gateway</h1>
  <p><strong>Agent-First API Platform</strong></p>
  <p>LLM Proxy + Tool Registry (MCP) + Knowledge Base (RAG) + Agent Memory<br>
  — all in one lightweight API. Runs on a 4GB VPS.</p>
  <p>
    <a href="#quick-start">Quick Start</a> •
    <a href="#features">Features</a> •
    <a href="docs/03-decisions.md">Architecture</a> •
    <a href="srv/landing/deploy.md">Deploy</a>
  </p>
</div>

---

## What is Phi AI Gateway?

Phi AI Gateway provides all the primitives AI agents need in a single API:

| Primitive | What it does |
|-----------|-------------|
| **LLM Proxy** | OpenAI-compatible endpoint for 10+ models across OpenAI, Anthropic, Groq. Auto-failover, transparent cost tracking. |
| **Tool Registry** | Register, discover, and execute tools via REST or MCP (JSON-RPC 2.0). Agent-discoverable with JSON Schema contracts. |
| **Knowledge Base** | Ingest documents with chunking + embedding. Semantic vector search (sqlite-vec) with keyword fallback. |
| **Agent Memory** | Persistent conversation storage with context window management and auto-truncation. |

**Target audience:** Indonesian AI indie hackers, dev agencies, and SEA developers who want a self-hosted, affordable agent infrastructure.

**Pricing:** Free tier (10K calls/mo), Pro Rp 150K/mo (~$9), Team Rp 500K/mo (~$30). Self-host: free (MIT).

---

## Quick Start

```bash
# Clone
git clone https://github.com/phiconsulting/phi-gateway
cd phi-gateway

# Install
pip install -e ".[dev]"
cp .env.example .env  # Edit with your API keys

# Run
uvicorn phi_gateway.main:app --reload

# Create an API key
curl -X POST http://localhost:8000/v1/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "dev", "tier": "free"}'

# Chat with Groq
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer <your-key>" \
  -H "Content-Type: application/json" \
  -d '{"model": "groq/llama-3.3-70b", "messages": [{"role": "user", "content": "Hello!"}]}'
```

Or deploy with Docker:

```bash
docker compose up -d
```

---

## Features

### 🔌 LLM Proxy
- OpenAI-compatible request/response format
- Multi-provider routing by model name (`groq/llama-3.3-70b`)
- SSE streaming support
- Transparent cost per request (`cost_usd` field in response)
- Request logging with token counts and latency

### 🛠 Tool Registry (MCP-Native)
- Register tools with JSON Schema contracts
- Execute tools via proxied HTTP calls
- MCP endpoint (`POST /mcp`) with `tools/list`, `tools/call`
- Schema validation on tool params

### 📚 Knowledge Base
- Create multiple knowledge bases per API key
- Ingest documents with paragraph-aware chunking (~1000 chars, 200 overlap)
- OpenAI embedding generation (batch support)
- Semantic search via cosine similarity
- Keyword fallback when embeddings unavailable

### 🧠 Agent Memory
- Conversation CRUD with session IDs
- Message history with pagination
- Context window management with auto-truncation
- `X-Context-Truncated` header on trimming

### 📊 Dashboard
- Overview with usage stats
- API key management (create, list, revoke)
- Usage breakdown by provider and model
- Built with HTMX + Tailwind CSS

---

## Architecture

```
Caddy (reverse proxy, auto SSL)
  └── FastAPI (2 uvicorn workers, ~300MB RAM)
        ├── /v1/chat         → LLM proxy → OpenAI/Anthropic/Groq
        ├── /v1/tools        → Tool registry (MCP-native)
        ├── /v1/kb           → RAG (SQLite + sqlite-vec)
        ├── /v1/memory       → Agent memory
        ├── /v1/keys         → API key management
        ├── /v1/usage        → Usage analytics
        ├── /mcp             → JSON-RPC 2.0 MCP endpoint
        ├── /dashboard       → HTMX admin UI
        └── /docs            → Swagger UI
              └── SQLite (single file, ~20MB + ~200MB vector index)
```

**RAM budget:** ~800-900MB base idle on 4GB VPS → ~3.2GB headroom.

See `docs/02-architecture.md` for full details.

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| Python + FastAPI | AI ecosystem, async native, auto OpenAPI 3.1 |
| SQLite + sqlite-vec | Zero ops, single file, fits RAM budget |
| Caddy proxy | Auto SSL, single binary, ~50MB RAM |
| Proxy-first (not local LLM) | 4GB can't run Ollama + app; Groq free tier exists |
| MCP protocol from day 1 | JSON-RPC 2.0, de facto standard for agent-tool |
| Indonesia beachhead | Zero local competitors, IDR pricing moat |
| API-key-only auth | Stripe's model — simpler to ship |

Full ADRs in `docs/03-decisions.md`.

## Project Structure

```
D:/PhiConsulting/
├── AGENTS.md                 # Agent handoff protocol
├── src/phi_gateway/          # Application code
│   ├── api/                  # FastAPI route handlers
│   ├── core/                 # Business logic
│   ├── dashboard/            # HTMX + Tailwind UI templates
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas/              # Pydantic schemas
│   ├── services/             # Service layer
│   ├── config.py             # pydantic-settings
│   ├── database.py           # Async SQLAlchemy engine
│   ├── dependencies.py       # FastAPI DI
│   └── main.py               # App factory
├── docs/                     # Architecture docs
├── srv/                      # Landing page + deploy guide
├── tests/                    # pytest suite (28+ tests)
├── alembic/                  # Database migrations (003)
├── docker-compose.yml        # Caddy + API
├── Dockerfile                # Multi-stage build
└── Caddyfile                 # Reverse proxy config
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

MIT — see [LICENSE](LICENSE).
