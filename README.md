# PhiGateway

<p align="center">
  <a href="https://github.com/raindragon14/phi-gateway/actions"><img src="https://img.shields.io/github/actions/workflow/status/raindragon14/phi-gateway/ci.yml?branch=main&label=CI&logo=github&style=flat" alt="CI"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+"></a>
  <a href="https://github.com/raindragon14/phi-gateway/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License"></a>
  <a href="https://phiconsulting.biz.id"><img src="https://img.shields.io/website?url=https%3A%2F%2Fphiconsulting.biz.id&label=live%20demo&style=flat" alt="Live Demo"></a>
</p>

**Self-hosted AI gateway — LLM proxy, MCP tool registry, RAG knowledge base, and agent memory behind a single API. Docker up in under a minute, zero SaaS lock-in.**

<p align="center">
  <a href="#what-is-phigateway">What is it?</a> ·
  <a href="#quick-start">Quick Start</a> ·
  <a href="#use-cases">Use Cases</a> ·
  <a href="#screenshots">Screenshots</a> ·
  <a href="#roadmap">Roadmap</a>
</p>

---

## What is PhiGateway?

Every AI agent needs an LLM, tools, knowledge, and memory. PhiGateway puts all four behind **one OpenAI-compatible endpoint**:

```bash
curl https://phiconsulting.biz.id/v1/chat/completions \
  -H "Authorization: Bearer $PHI_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemini-2.5-flash",
    "messages": [{"role": "user", "content": "Summarize my last conversation"}]
  }'
# → routes to provider, searches memory, returns answer + logs cost
```

| Primitive | What it does | Why it matters |
|-----------|-------------|----------------|
| **LLM Proxy** | Route chat to OpenAI / Anthropic / Groq / OpenRouter. Streaming, cost tracking, logging. | Switch providers, free tiers, fallback — without changing agent code. |
| **Tool Registry** | Register tools with JSON Schema. Agents discover + call via REST or MCP (JSON-RPC 2.0). | One registry for every tool. MCP-native, compatible with any MCP client. |
| **Knowledge Base** | Chunk, embed, and search documents. Cosine similarity + keyword fallback. No external vector DB. | Ship a knowledge base inside a single SQLite file. Zero ops, zero new infra. |
| **Agent Memory** | Store conversations, paginate history, auto-trim context. Returns `X-Context-Truncated` header. | Agent remembers past turns. Trimming keeps token costs under control. |

## Screenshots

| Interactive API Reference (Scalar) | Admin Dashboard (HTMX) |
|:-:|:-:|
| ![API Docs](assets/api-docs.png) | ![Dashboard](assets/dashboard.png) |

## Quick Start

```bash
git clone https://github.com/raindragon14/phi-gateway
cd phi-gateway
cp .env.example .env    # add your LLM provider keys
docker compose up -d
```

Gateway starts on port 8000. Create a key and make your first request:

```bash
# 1. Create a gateway API key
curl -sX POST http://localhost:8000/v1/keys \
  -H "Content-Type: application/json" \
  -d '{"name":"my-agent","tier":"free"}'
# → {"key": "phi-sk-...", ...}

# 2. Chat through the gateway
curl -s http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer phi-sk-YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"groq/llama-3.3-70b","messages":[{"role":"user","content":"Hello"}]}'
```

**Live instance:** <https://phiconsulting.biz.id> — the same gateway, deployed with Caddy + Docker.

## Business Impact

### Cost Comparison

| Approach | Monthly Cost (10K req/day) | Ops Overhead | Lock-in |
|----------|----------------------------|--------------|---------|
| **PhiGateway (self-hosted)** | **~$80–250** (your provider bills only) | Docker + SQLite | None |
| Managed gateway (Portkey, Helicone) | $500–2,000 + provider bills | Low | Medium |
| Build from scratch | Dev time: 2–4 weeks | High | Yours |
| Direct API per service | Same provider cost, no routing/fallback | Low | High |

PhiGateway doesn't charge per-request, per-seat, or per-feature. You pay your own LLM provider bills — the gateway is free and open source.

### Time to Value

| Task | Without PhiGateway | With PhiGateway |
|------|-------------------|-----------------|
| Set up agent with tools + RAG + memory | 2–4 weeks | **5 minutes** (`docker compose up`) |
| Add a new LLM provider | Rewrite provider client | **Zero** — just change model name |
| Add a tool for your agent | Build webhook + auth + validation | **1 curl** — register with JSON Schema |
| Deploy a knowledge base | Spin up vector DB, embedding pipeline | **Zero new infra** — SQLite + built-in embeddings |

### Security

- **No data leaves your infrastructure** — your keys, logs, and usage data stay on your server.
- **API-key-only auth** — simple, auditable, no OAuth complexity.
- **BYO keys** — the gateway ships with zero provider keys. You bring your own and control rate limits per tier.

## Use Cases

**Internal AI Assistant** — Deploy behind your VPN. Give your team a company-wide AI agent with access to internal docs, codebases, and tools — no data sent to third-party gateways.

**Customer Support Bot** — Register tools to look up orders, check statuses, and escalate. Use RAG to ground answers in your knowledge base. Track every conversation via agent memory.

**Documentation QA** — Ingest product docs into the knowledge base. Users ask natural-language questions and get grounded answers with source citations.

**Multi-Provider Fallback** — Route `gpt-5-nano` to OpenAI, `claude-sonnet-4.6` to Anthropic, `groq/llama-3.3-70b` to Groq. If one provider is down, switch models — your agent code never changes.

## Features

### LLM Proxy

Single endpoint (`/v1/chat/completions`) routes to multiple providers. Model string determines the backend — your agent code never changes. Streaming (SSE) and cost tracking included.

Available on the live instance:

| Model | Provider | Context |
|-------|----------|---------|
| `gpt-5-nano` | OpenAI | 400k |
| `gpt-5.2` | OpenAI | 400k |
| `claude-sonnet-4.6` | Anthropic | 200k |
| `groq/llama-3.3-70b` | Groq | 128k |
| `google/gemini-2.5-flash` | OpenRouter | 1M |
| `google/gemini-2.5-pro` | OpenRouter | 1M |
| `openai/gpt-oss-120b` | OpenRouter | varies |
| `anthropic/claude-sonnet-4` | OpenRouter | 200k |

Full model list available at `/v1/models`.

### Tool Registry (MCP-native)

Register external capabilities with JSON Schema contracts. The gateway validates inputs and proxies executions. Supports both REST and MCP (JSON-RPC 2.0).

```bash
# Register a tool
curl -sX POST http://localhost:8000/v1/tools \
  -H "Authorization: Bearer phi-sk-YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"search","description":"Web search","json_schema":{...},"endpoint":"https://..."}'

# Discover via MCP
curl -sX POST http://localhost:8000/mcp \
  -H "Authorization: Bearer phi-sk-YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":"1"}'
```

### Knowledge Base

Paragraph-aware chunking, embeddings via OpenAI, cosine similarity search. Falls back to keyword search when embeddings are unavailable. Everything in SQLite — no external vector DB.

```bash
# Create a knowledge base
curl -sX POST http://localhost:8000/v1/kb \
  -H "Authorization: Bearer phi-sk-YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"product-docs"}'

# Search it
curl -sX POST http://localhost:8000/v1/kb/{id}/search \
  -H "Authorization: Bearer phi-sk-YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"deployment guide","top_k":5}'
```

### Agent Memory

Full CRUD for conversations with pagination and context window management. Auto-trims oldest messages when token count exceeds the model's context limit, returning `X-Context-Truncated`.

## Agent Workflow

```
┌─ Agent ─────────────────────────────────────────────────┐
│                                                           │
│  1. Authenticate  →  POST /v1/keys  →  get phi-sk-...    │
│  2. Think          →  POST /v1/chat/completions  →  LLM  │
│  3. Use tools      →  POST /v1/tools         →  execute  │
│  4. Search docs    →  POST /v1/kb/*/search   →  RAG      │
│  5. Remember       →  POST /v1/memory/*      →  history  │
│  6. Monitor        →  GET  /v1/usage         →  cost     │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

### Python Example

```python
import httpx

async def agent_workflow():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as c:
        # 1. Create a key (do this once)
        r = await c.post("/v1/keys", json={"name": "agent", "tier": "free"})
        key = r.json()["key"]
        headers = {"Authorization": f"Bearer {key}"}

        # 2. Chat
        r = await c.post("/v1/chat/completions", json={
            "model": "groq/llama-3.3-70b",
            "messages": [{"role": "user", "content": "What tools do I have?"}]
        }, headers=headers)
        print(r.json()["choices"][0]["message"]["content"])

        # 3. Register a tool
        await c.post("/v1/tools", json={
            "name": "calculator",
            "description": "Evaluate math expressions",
            "json_schema": {
                "type": "object",
                "properties": {"expr": {"type": "string"}},
                "required": ["expr"]
            },
            "endpoint": "https://api.mathjs.org/v4/"
        }, headers=headers)

        # 4. Create a knowledge base and search
        r = await c.post("/v1/kb", json={"name": "docs"}, headers=headers)
        kb_id = r.json()["id"]

        # 5. Store conversation
        await c.post("/v1/memory/conversations", json={
            "session_id": "session-42", "title": "User inquiry"
        }, headers=headers)

        # 6. Check usage
        r = await c.get("/v1/usage", headers=headers)
        print(f"Cost: ${r.json()['total_cost_usd']:.4f}")
```

## Self-Hosting

```bash
# Requirements: Docker, a domain (for SSL), provider API keys
git clone https://github.com/raindragon14/phi-gateway
cd phi-gateway
cp .env.example .env   # add your OpenAI / Anthropic / Groq / OpenRouter keys
docker compose up -d
```

The `.env.example` file documents every provider key. The gateway ships with **zero keys** — you bring your own. Rate limits are configurable per API key tier.

For production deployment with Caddy reverse proxy and SSL:

```
Internet → Caddy (auto TLS) → phi-gateway:8000
```

See `docker-compose.yml` and `Caddyfile` for the reference setup.

## Architecture

```
Caddy (reverse proxy, auto TLS)
  └── FastAPI (uvicorn)
        ├── /v1/chat/completions  →  LLM proxy  →  provider APIs
        ├── /v1/tools             →  tool registry
        ├── /v1/kb                →  RAG (SQLite + cosine similarity)
        ├── /v1/memory            →  agent memory
        ├── /v1/keys              →  API key management
        ├── /v1/usage             →  cost analytics
        ├── /mcp                  →  JSON-RPC 2.0 (MCP)
        ├── /dashboard            →  HTMX admin UI
        └── /docs                 →  interactive API ref (Scalar OpenAPI)
              └── SQLite (single file)
```

Idle RAM: **~250 MB**.

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Python + FastAPI | AI ecosystem standard, async-native, auto OpenAPI 3.1 |
| SQLite + pure Python vectors | Zero ops, single file, no external vector DB |
| Caddy reverse proxy | Auto Let's Encrypt SSL, ~50 MB RAM, single binary |
| Proxy-first architecture | No local models — routes to provider APIs via your keys |
| MCP from day one | JSON-RPC 2.0, de facto standard for agent-tool communication |
| API-key-only auth | Simple, developer-familiar, no OAuth complexity |
| In-memory rate limiter | Adequate for single-worker; Redis-ready for multi-worker |

## Project Structure

```
phi-gateway/
├── src/phi_gateway/
│   ├── api/                  # FastAPI routes (10 modules)
│   ├── core/                 # LLM proxy, auth, cost, embeddings, rate limiter
│   ├── dashboard/templates/  # HTMX admin UI
│   ├── models/               # SQLAlchemy ORM (6 tables)
│   ├── schemas/              # Pydantic request/response schemas
│   ├── services/             # Business logic orchestration
│   ├── config.py             # Environment configuration
│   ├── database.py           # Async SQLAlchemy engine
│   ├── dependencies.py       # Dependency injection (auth + rate limiting)
│   └── main.py               # App factory + lifespan
├── tests/                    # pytest suite (41 passed, 6 xfail)
│   ├── unit/                 # cost tracker, security
│   └── integration/          # chat, keys, KB, memory, tools, MCP, usage
├── docker-compose.yml        # Local dev (Caddy + API)
├── Dockerfile                # Production build
└── pyproject.toml            # Package metadata
```

## Testing

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run full test suite
pytest -v

# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v

# Lint
ruff check src/ tests/
```

## Roadmap

> PhiGateway is actively being built. These are the next milestones.

**Q2 2026**
- [x] Multi-provider LLM proxy (OpenAI, Anthropic, Groq, OpenRouter)
- [x] MCP-native tool registry with discovery and execution
- [x] RAG knowledge base with SQLite embeddings
- [x] Agent memory with auto context trimming
- [x] HTMX admin dashboard
- [ ] API key tiers with granular rate limits (done in code, pending admin UI)
- [ ] Document ingestion API (upload PDFs/markdown directly)

**Q3 2026**
- [ ] Support for Ollama / local models
- [ ] Webhook integration for tool execution callbacks
- [ ] Redis-backed rate limiting for multi-worker deployments
- [ ] Usage analytics charting in dashboard
- [ ] OpenTelemetry tracing

**Future**
- [ ] Plugin system for custom authentication backends
- [ ] Streaming tool execution (SSE for real-time tool output)
- [ ] Multi-user workspace with team management

## License

MIT. See [LICENSE](LICENSE).