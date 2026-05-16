# PhiGateway

<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+"></a>
  <a href="https://github.com/raindragon14/phi-gateway/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License"></a>
</p>

**Production-grade self-hosted AI gateway.** LLM proxy, MCP tool registry, RAG knowledge base, agent memory — one API.

<p align="center">
  <a href="#quick-start">Quick Start</a> ·
  <a href="#agent-workflow">Agent Workflow</a> ·
  <a href="#self-hosting">Self-Hosting</a> ·
  <a href="#architecture">Architecture</a> ·
  <a href="#license">License</a>
</p>

---

## What is PhiGateway?

When building an AI agent, you need four things: a way to call LLMs, tools the agent can use, a place to store knowledge, and memory across conversations. PhiGateway provides all four behind a single OpenAI-compatible API. Self-hosted, open source, no strings attached.

| Primitive | What it does |
|---|---|
| **LLM Proxy** | Route chat completions to OpenAI, Anthropic, Groq, and OpenRouter. Streaming, cost tracking, request logging. |
| **Tool Registry** | Register tools with JSON Schema. Agents discover them via REST or MCP (JSON-RPC 2.0). The gateway proxies execution. |
| **Knowledge Base** | Chunk, embed, and search documents. Cosine similarity with keyword fallback. No external vector DB required. |
| **Agent Memory** | Store conversations, paginate history, auto-trim context windows. Returns `X-Context-Truncated` header when trimming occurs. |

## Quick Start

```bash
git clone https://github.com/raindragon14/phi-gateway
cd phi-gateway
cp .env.example .env    # add your LLM provider keys here
docker compose up -d
```

The gateway starts on port 8000. Create an API key and chat:

```bash
# Step 1: Create a gateway API key
curl -sX POST http://localhost:8000/v1/keys \
  -H "Content-Type: application/json" \
  -d '{"name":"my-agent","tier":"free"}'

# Step 2: Use it
curl -s http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer <your-key>" \
  -H "Content-Type: application/json" \
  -d '{"model":"groq/llama-3.3-70b","messages":[{"role":"user","content":"Hello"}]}'
```

## Agent Workflow

Here is how an AI agent uses the gateway programmatically:

```
┌─ Agent (your code) ────────────────────────────────────────┐
│                                                             │
│  1. Authenticate  →  POST /v1/keys  →  get phi‑sk‑...      │
│  2. Think          →  POST /v1/chat/completions  →  LLM    │
│  3. Use tools      →  POST /v1/tools  →  tool execution    │
│  4. Search docs    →  POST /v1/kb/*/search  →  RAG         │
│  5. Remember       →  POST /v1/memory/*  →  conversation   │
│  6. Monitor        →  GET  /v1/usage  →  cost breakdown    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Step-by-step (Python agent example)

```python
import httpx

async def agent_workflow():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as c:
        # 1. Create a key (do this once, save it)
        r = await c.post("/v1/keys", json={"name": "agent", "tier": "free"})
        key = r.json()["key"]

        headers = {"Authorization": f"Bearer {key}"}

        # 2. Chat with any model
        r = await c.post("/v1/chat/completions", json={
            "model": "groq/llama-3.3-70b",
            "messages": [{"role": "user", "content": "What tools do I have?"}]
        }, headers=headers)
        reply = r.json()["choices"][0]["message"]["content"]

        # 3. Register a tool the agent can call
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

        # 4. Search a knowledge base (after ingesting docs)
        r = await c.post("/v1/kb", json={"name": "docs"}, headers=headers)
        kb_id = r.json()["id"]
        await c.post(f"/v1/kb/{kb_id}/search", json={
            "query": "deployment guide", "top_k": 5
        }, headers=headers)

        # 5. Persist conversation for context
        r = await c.post("/v1/memory/conversations", json={
            "session_id": "agent-session-42", "title": "User inquiry"
        }, headers=headers)

        # 6. Check usage and cost
        r = await c.get("/v1/usage", headers=headers)
        usage = r.json()
        print(f"Cost so far: ${usage['total_cost_usd']:.4f}")
```

## Features

### LLM Proxy

Single endpoint (`/v1/chat/completions`) routes to multiple providers. Model string determines the backend — your agent code never changes:

| Model | Provider | Pricing (1M tokens) | Context |
|---|---|---|---|
| `gpt-5-nano` | OpenAI | $0.05 / $0.40 | 400k |
| `gpt-5.2` | OpenAI | $1.75 / $14.00 | 400k |
| `claude-sonnet-4.6` | Anthropic | $3.00 / $15.00 | 200k |
| `groq/llama-3.3-70b` | Groq | Free | 128k |
| `openrouter/*` | OpenRouter | Varies | Varies |

Streaming (SSE), cost tracking per request, and transparent error handling included.

### Tool Registry (MCP-native)

Agents register external capabilities with JSON Schema contracts. The gateway validates inputs and proxies executions:

```bash
# Register
curl -sX POST /v1/tools -H "Authorization: Bearer <key>" \
  -d '{"name":"search","description":"Web search","json_schema":{...},"endpoint":"https://..."}'

# Discover (MCP)
curl -sX POST /mcp -H "Authorization: Bearer <key>" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":"1"}'

# Execute
curl -sX POST /v1/tools/{id}/call -H "Authorization: Bearer <key>" \
  -d '{"method":"search","params":{"query":"phi gateway"}}'
```

### Knowledge Base

Paragraph-aware chunking, embeddings via OpenAI, cosine similarity search. Falls back to keyword search when embeddings are unavailable. No external vector database needed — everything lives in SQLite.

### Agent Memory

Full CRUD for conversations with pagination and context window management. The gateway automatically trims oldest messages when token count exceeds the model's context limit, returning an `X-Context-Truncated` header so your agent can react.

## Self-Hosting

```bash
# Requirements: Docker, a domain (for SSL), provider API keys
git clone https://github.com/raindragon14/phi-gateway
cd phi-gateway
cp .env.example .env   # add your OpenAI / Anthropic / Groq / OpenRouter keys
docker compose up -d
```

The `.env.example` file documents every provider key you need. The gateway does **not** ship with any keys — you bring your own and pay your own provider bills. Rate limits are configurable per API key tier in the database.

## Architecture

```
Caddy (reverse proxy, auto SSL)
  └── FastAPI (uvicorn, 2 workers)
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

Idle RAM: approximately 250 MB.

## Design Decisions

| Decision | Rationale |
|---|---|
| Python + FastAPI | AI ecosystem standard, async-native, auto OpenAPI 3.1 |
| SQLite + pure Python vectors | Zero ops, single file, no external vector DB needed |
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
├── tests/                    # pytest suite (unit + integration)
├── docker-compose.yml        # Local dev (Caddy + API)
├── Dockerfile                # Production build
└── pyproject.toml            # Package metadata
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest -v

# Lint
ruff check src/ tests/

# Run with auto-reload
uvicorn phi_gateway.main:app --reload
```

## License

MIT. See [LICENSE](LICENSE).
