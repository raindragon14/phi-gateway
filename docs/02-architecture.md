# 02 — Architecture & System Design

> Part of Phi AI Gateway documentation
> Date: 2026-05-11
> Status: DESIGN PHASE — not yet implemented

---

## 1. SYSTEM OVERVIEW

```text
                               INTERNET
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                        VPS (4GB RAM)                         │
│                                                              │
│  ┌──────────────────┐      ┌─────────────────────────────┐  │
│  │     CADDY        │      │       PHI GATEWAY API        │  │
│  │  (Reverse Proxy)  │─────▶│     (FastAPI + Uvicorn)      │  │
│  │                  │      │                              │  │
│  │  • Auto SSL      │      │  ┌────────────────────────┐  │  │
│  │  • Port 80→443   │      │  │   /v1/chat             │  │  │
│  │  • Static files  │      │  │   LLM Proxy            │  │  │
│  │                  │      │  └────────────────────────┘  │  │
│  └──────────────────┘      │                              │  │
│                             │  ┌────────────────────────┐  │  │
│                             │  │   /v1/tools            │  │  │
│                             │  │   Tool Registry (MCP)  │  │  │
│                             │  └────────────────────────┘  │  │
│                             │                              │  │
│                             │  ┌────────────────────────┐  │  │
│                             │  │   /v1/kb               │  │  │
│                             │  │   Knowledge Base (RAG) │  │  │
│                             │  └────────────────────────┘  │  │
│                             │                              │  │
│                             │  ┌────────────────────────┐  │  │
│                             │  │   /v1/memory           │  │  │
│                             │  │   Agent Memory         │  │  │
│                             │  └────────────────────────┘  │  │
│                             │                              │  │
│                             │  ┌────────────────────────┐  │  │
│                             │  │   /v1/keys             │  │  │
│                             │  │   API Key Management   │  │  │
│                             │  └────────────────────────┘  │  │
│                             └──────────┬───────────────────┘  │
│                                        │                      │
│                          ┌─────────────┼─────────────┐        │
│                          ▼             ▼             ▼        │
│                    ┌──────────┐ ┌───────────┐ ┌──────────┐   │
│                    │  SQLite  │ │ sqlite-vec│ │  Cache   │   │
│                    │ (Primary)│ │ (Vectors) │ │ (Memory) │   │
│                    └──────────┘ └───────────┘ └──────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
              ┌───────────────────────────────────┐
              │        EXTERNAL LLM APIs           │
              │  OpenAI | Anthropic | Groq | etc.  │
              └───────────────────────────────────┘
```

---

## 2. RAM BUDGET (CRITICAL CONSTRAINT)

```yaml
allocations:
  os_ubuntu_minimal: "~400 MB"
  caddy: "~50 MB"
  fastapi_2_workers: "~300 MB"
  sqlite_primary: "~20 MB (minimal — disk-based, not in-memory)"
  sqlite_vec_index: "~200 MB (depends on document volume)"
  docker_overhead: "~200 MB"
  python_runtime_overhead: "~100 MB"

  total_base_idle: "~800-900 MB"
  remaining_headroom: "~3.1-3.2 GB"

warning: "Do NOT add Redis, PostgreSQL, or ChromaDB as separate services."
note: "Redis can be added later if VPS is resized. For MVP, use in-memory
       caching (Python dict or lru_cache)."

future_scale_path: >
  When user base grows beyond single VPS capacity:
  1. Resize VPS (cloud-based, easy)
  2. Extract SQLite → managed PostgreSQL
  3. Add Redis for rate limiting cache
  4. Add multiple API workers behind load balancer
  5. All of this is designed to be incremental, not rewrite
```

---

## 3. DATA MODELS

### 3.1 API Keys

```python
# Conceptual — not actual code
class ApiKey:
    id: UUID
    key_hash: str          # bcrypt hash of the API key
    prefix: str            # First 8 chars for display: "phi-sk-abc12345..."
    name: str              # Human label: "My Production Key"
    user_id: str
    tier: "free" | "pro" | "team"
    rate_limit_per_min: int
    rate_limit_per_day: int
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None
    expires_at: datetime | None
```

### 3.2 LLM Request Log

```python
class LLMRequest:
    id: UUID
    api_key_id: UUID
    provider: str           # "openai", "anthropic", "groq", "ollama"
    model: str              # "gpt-5-mini", "claude-haiku-4.5"
    input_tokens: int
    output_tokens: int
    cost_usd_micro: int     # Cost in micro-dollars (x1,000,000) for precision
    latency_ms: int
    status: "success" | "error"
    error_message: str | None
    created_at: datetime
```

### 3.3 Tool Definition (MCP)

```python
class ToolDefinition:
    id: UUID
    name: str               # Unique: "web_search", "send_email"
    description: str        # Human + agent readable
    json_schema: dict       # JSON Schema for tool parameters
    endpoint: str           # Internal or external endpoint
    auth_type: "none" | "api_key" | "oauth"
    is_active: bool
    owner_api_key_id: UUID | None  # Who registered this tool
    created_at: datetime
```

### 3.4 Knowledge Base

```python
class Document:
    id: UUID
    kb_id: UUID
    title: str
    content: str            # Original text
    chunk_index: int        # Which chunk within the document
    embedding: bytes | None # Vector embedding (sqlite-vec blob)
    metadata: dict          # {"source": "url", "tags": [...]}
    created_at: datetime

class KnowledgeBase:
    id: UUID
    name: str
    description: str
    api_key_id: UUID        # Owner
    document_count: int
    created_at: datetime
```

### 3.5 Agent Memory

```python
class Conversation:
    id: UUID
    api_key_id: UUID
    session_id: str         # External session reference
    title: str | None       # Auto-generated summary
    created_at: datetime
    updated_at: datetime

class Message:
    id: UUID
    conversation_id: UUID
    role: "user" | "assistant" | "system" | "tool"
    content: str
    tool_calls: dict | None
    token_count: int
    created_at: datetime
```

---

## 4. API CONTRACTS

### 4.1 LLM Proxy

```yaml
POST /v1/chat/completions:
  description: "OpenAI-compatible chat completions. Routes to configured LLM."
  auth: "Bearer <api_key>"
  request:
    model: str              # "gpt-5-mini", "claude-haiku-4.5", "groq/llama-3.3-70b"
    messages: list[Message]
    temperature: float = 0.7
    max_tokens: int | None
    stream: bool = false
    tools: list[ToolDef] | None   # Tool definitions for function calling
  response:
    id: str
    choices: list[Choice]
    usage: {prompt_tokens, completion_tokens, total_tokens}
    provider: str           # Which provider actually served the request
    cost_usd: float         # Transparent cost

GET /v1/models:
  description: "List available models across all configured providers"
  response: list[ModelInfo] # {id, provider, pricing, context_window}

POST /v1/embeddings:
  description: "Get embeddings from configured provider"
  request: {model, input: str | list[str]}
  response: {data: list[Embedding], usage}
```

### 4.2 Tool Registry (MCP-Native)

```yaml
GET /v1/tools:
  description: "List all available tools (agent-discoverable)"
  response: list[ToolDefinition]

POST /v1/tools:
  description: "Register a new tool"
  auth: required
  request: {name, description, json_schema, endpoint}

POST /v1/tools/{tool_id}/call:
  description: "Execute a tool (MCP-compatible JSON-RPC 2.0)"
  request: {method: str, params: dict}
  response: {result: any, error: str | null}

GET /v1/tools/{tool_id}/schema:
  description: "Get JSON Schema for a specific tool"
  response: JSONSchema
```

### 4.3 Knowledge Base

```yaml
POST /v1/kb:
  description: "Create a new knowledge base"
  request: {name, description}

POST /v1/kb/{kb_id}/documents:
  description: "Ingest documents into KB"
  request: {documents: list[{title, content, metadata}]}
  note: "Documents are chunked and embedded server-side"

POST /v1/kb/{kb_id}/search:
  description: "Semantic search across KB"
  request: {query: str, top_k: int = 5}
  response: {results: list[{content, score, metadata}]}

DELETE /v1/kb/{kb_id}:
  description: "Delete entire knowledge base"
```

### 4.4 Agent Memory

```yaml
POST /v1/memory/conversations:
  description: "Create a new conversation"
  request: {session_id: str, title?: str}
  response: Conversation

POST /v1/memory/conversations/{id}/messages:
  description: "Add message to conversation"
  request: {role, content, tool_calls?}
  response: Message

GET /v1/memory/conversations/{id}/messages:
  description: "Get conversation history"
  query: {limit: int = 50, before_id?: str}
  response: list[Message]

GET /v1/memory/conversations:
  description: "List conversations for this API key"
  response: list[Conversation]

DELETE /v1/memory/conversations/{id}:
  description: "Delete conversation and all messages"
```

### 4.5 API Key Management

```yaml
POST /v1/keys:
  description: "Create new API key"
  request: {name, tier}
  response: {id, key: str, prefix, name}  # key shown ONCE

GET /v1/keys:
  description: "List API keys"
  response: list[{id, prefix, name, tier, is_active, last_used_at}]

DELETE /v1/keys/{id}:
  description: "Revoke API key"

GET /v1/usage:
  description: "Get usage statistics"
  query: {from?, to?, granularity: "day"|"hour"}
  response: {total_tokens, total_cost_usd, by_provider, by_model}
```

### 4.6 MCP Endpoint

```yaml
POST /mcp:
  description: "Model Context Protocol endpoint (JSON-RPC 2.0)"
  request: {jsonrpc: "2.0", method: str, params: dict, id: str}
  methods:
    - "tools/list"         # Discover available tools
    - "tools/call"         # Execute a tool
    - "resources/list"     # List available resources (KB)
    - "resources/read"     # Read a resource
  note: "This is the primary agent-to-platform interface"
```

---

## 5. DOCKER SETUP (PLANNED)

```yaml
# docker-compose.yml (Phase 1 deliverable)
version: "3.8"
services:
  caddy:
    image: caddy:2-alpine
    ports: ["80:80", "443:443"]
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data

  api:
    build: .
    environment:
      - DATABASE_URL=sqlite:///data/phi.db
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GROQ_API_KEY=${GROQ_API_KEY}
    volumes:
      - phi_data:/app/data
    restart: unless-stopped
    mem_limit: 1g

volumes:
  caddy_data:
  phi_data:
```

```text
# Caddyfile
api.phiconsulting.biz.id {
    reverse_proxy api:8000
}

phiconsulting.biz.id {
    root * /srv/landing
    file_server
}
```

---

## 6. DIRECTORY STRUCTURE (TO BE CREATED)

```text
src/phi_gateway/
├── __init__.py
├── main.py                  # FastAPI app factory, middleware, routers
├── config.py                # Settings via pydantic-settings
├── dependencies.py          # FastAPI dependency injection
│
├── api/
│   ├── __init__.py
│   ├── router.py            # Main router aggregation
│   ├── chat.py              # /v1/chat/*
│   ├── tools.py             # /v1/tools/* + /mcp/*
│   ├── knowledge.py         # /v1/kb/*
│   ├── memory.py            # /v1/memory/*
│   ├── keys.py              # /v1/keys/* + /v1/usage
│   └── models.py            # /v1/models
│
├── core/
│   ├── __init__.py
│   ├── security.py          # API key hashing, verification
│   ├── rate_limit.py        # Rate limiting logic
│   ├── llm_proxy.py         # Multi-provider LLM router
│   └── cost_tracker.py      # Token counting, cost calculation
│
├── models/
│   ├── __init__.py
│   ├── api_key.py           # SQLAlchemy model
│   ├── llm_request.py       # SQLAlchemy model
│   ├── tool.py              # SQLAlchemy model
│   ├── document.py          # SQLAlchemy model
│   ├── conversation.py      # SQLAlchemy model
│   └── message.py           # SQLAlchemy model
│
├── services/
│   ├── __init__.py
│   ├── llm_service.py       # LLM proxy business logic
│   ├── tool_service.py      # Tool registry + execution
│   ├── kb_service.py        # Document ingest, chunk, embed, search
│   ├── memory_service.py    # Conversation CRUD + context management
│   └── embedding_service.py # Embedding generation (via LLM proxy)
│
└── schemas/
    ├── __init__.py
    ├── chat.py              # Pydantic request/response schemas
    ├── tools.py
    ├── knowledge.py
    ├── memory.py
    └── keys.py
```

---

## 7. KEY DESIGN PRINCIPLES

```yaml
principles:
  - "OpenAI-compatible everywhere — any OpenAI SDK client should work"
  - "MCP-native — tool discovery and execution follows JSON-RPC 2.0"
  - "Zero external service dependencies for MVP"
  - "Everything is an API key — no user accounts, no OAuth for MVP"
  - "Cost transparency — every LLM response includes cost_usd"
  - "Fail gracefully — if one LLM provider is down, auto-failover"
  - "Stateless API — memory is explicit via /v1/memory, not server-side sessions"
```

---

*Next: docs/03-decisions.md*
