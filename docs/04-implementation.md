# 04 — Implementation Plan

> Part of Phi AI Gateway documentation
> Date: 2026-05-11
> Updated: 2026-05-11 — Phase 1 complete
> Status: Phase 1 COMPLETE — Phase 2 ready

---

## PHASE OVERVIEW

```text
Phase 1 (Week 1-2):  Core API + LLM Proxy            [✅ COMPLETE — 2026-05-11]
Phase 2 (Week 3-4):  Tool Registry + Knowledge Base   [✅ COMPLETE — 2026-05-11]
Phase 3 (Week 5-6):  Agent Memory + Dashboard         [✅ COMPLETE — 2026-05-11]
Phase 4 (Week 7-8):  Landing Page + Deploy + Docs     [LAUNCH READY]
```

---

## PHASE 1: Core API + LLM Proxy (Week 1-2)

**Goal:** Working API with LLM proxy that routes to multiple providers.

### Deliverables

```yaml
phase_1_deliverables:
  - "Project scaffold (src/, docker-compose.yml, Caddyfile, .env.example)"
  - "FastAPI app with health check, CORS, error handling"
  - "Configuration management (pydantic-settings, .env)"
  - "API key management CRUD (/v1/keys/*)"
  - "API key authentication middleware"
  - "LLM Proxy (/v1/chat/completions) with multi-provider routing"
  - "GET /v1/models — list available models"
  - "POST /v1/embeddings — embedding endpoint"
  - "Rate limiting skeleton"
  - "Request logging (SQLite)"
  - "Docker compose working (caddy + api)"
  - "Basic test suite (pytest + httpx)"
```

### Tasks (ordered)

```yaml
tasks:
  T1.1:
    action: "Create project directory structure"
    files: ["src/phi_gateway/__init__.py", "src/phi_gateway/main.py skeleton"]

  T1.2:
    action: "Create docker-compose.yml and Dockerfile"
    files: ["Dockerfile", "docker-compose.yml"]

  T1.3:
    action: "Create Caddyfile"
    config: "Reverse proxy api:8000, minimal config"

  T1.4:
    action: "Implement config.py"
    modules: ["pydantic-settings"]
    env_vars: ["DATABASE_URL", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GROQ_API_KEY"]

  T1.5:
    action: "Implement SQLAlchemy models"
    models: ["ApiKey", "LLMRequest"]
    migration: "Alembic init + first migration"

  T1.6:
    action: "Implement API key CRUD"
    endpoints: ["POST /v1/keys", "GET /v1/keys", "DELETE /v1/keys/{id}"]
    security: "bcrypt hash, prefix-based identification"

  T1.7:
    action: "Implement auth middleware"
    method: "FastAPI dependency, Bearer token extraction, key lookup + verification"

  T1.8:
    action: "Implement LLM proxy service"
    providers: ["OpenAI", "Anthropic", "Groq"]
    pattern: "Route by model name prefix or explicit provider"
    format: "OpenAI-compatible request/response"

  T1.9:
    action: "Implement /v1/chat/completions endpoint"
    features: ["streaming (SSE)", "non-streaming", "tool calling passthrough"]

  T1.10:
    action: "Implement /v1/models endpoint"
    response: "List of all available models across all configured providers"

  T1.11:
    action: "Implement /v1/embeddings endpoint"
    note: "Passthrough to configured embedding provider"

  T1.12:
    action: "Implement request logging"
    log: ["model", "tokens_in", "tokens_out", "cost", "latency", "status"]

  T1.13:
    action: "Implement basic rate limiting"
    method: "In-memory counter per API key"
    limits: "free=10/min, pro=60/min, team=300/min"

  T1.14:
    action: "Write tests"
    coverage: "API key CRUD, auth middleware, LLM proxy routing"
    tools: ["pytest", "httpx", "pytest-asyncio"]

  T1.15:
    action: "Docker compose up — verify everything works"
    verify: ["health check passes", "SSL works via Caddy", "API key flow E2E"]
```

### Phase 1 Success Criteria

```yaml
success:
  - "curl /v1/chat/completions returns valid OpenAI-format response"
  - "API key created, used for auth, request logged"
  - "Streaming works via SSE"
  - "docker compose up runs on <1GB RAM"
  - "All tests pass"
```

---

## PHASE 2: Tool Registry + Knowledge Base (Week 3-4)

**Goal:** Agents can discover tools and query knowledge bases.

### Deliverables

```yaml
phase_2_deliverables:
  - "Tool Registry CRUD (/v1/tools/*)"
  - "MCP endpoint (/mcp) with tools/list and tools/call"
  - "Knowledge Base CRUD (/v1/kb/*)"
  - "Document ingest with chunking"
  - "sqlite-vec integration for embeddings"
  - "Semantic search endpoint"
  - "Pydantic schemas for all new endpoints"
  - "Tests for tool execution and KB search"
```

### Tasks

```yaml
tasks:
  T2.1:
    action: "Add ToolDefinition and KnowledgeBase SQLAlchemy models"
    migration: "Alembic revision"

  T2.2:
    action: "Install and configure sqlite-vec"
    note: "Python bindings: pip install sqlite-vec"

  T2.3:
    action: "Implement Tool Registry CRUD"
    endpoints: ["POST /v1/tools", "GET /v1/tools", "GET /v1/tools/{id}/schema"]

  T2.4:
    action: "Implement tool execution"
    endpoint: "POST /v1/tools/{id}/call"
    note: "Proxy to tool's endpoint, validate response against schema"

  T2.5:
    action: "Implement MCP endpoint"
    endpoint: "POST /mcp"
    methods: ["tools/list", "tools/call", "resources/list", "resources/read"]
    format: "JSON-RPC 2.0"

  T2.6:
    action: "Implement Knowledge Base CRUD"
    endpoints: ["POST /v1/kb", "DELETE /v1/kb/{id}"]

  T2.7:
    action: "Implement document ingest + chunking"
    logic: "RecursiveCharacterTextSplitter (or simple paragraph split)"
    chunk_size: "~1000 chars with 200 char overlap"

  T2.8:
    action: "Implement embedding generation"
    method: "Call /v1/embeddings internally (dogfooding our own API)"

  T2.9:
    action: "Implement semantic search"
    endpoint: "POST /v1/kb/{kb_id}/search"
    logic: "Embed query → sqlite-vec cosine similarity → return top_k"

  T2.10:
    action: "Write tests"
    coverage: ["Tool CRUD", "MCP endpoint", "KB ingest + search", "Edge cases"]
```

---

## PHASE 3: Agent Memory + Dashboard (Week 5-6)

**Goal:** Persistent conversation storage and simple dashboard UI.

### Deliverables

```yaml
phase_3_deliverables:
  - "Agent Memory API (/v1/memory/*)"
  - "Conversation + Message models"
  - "Usage analytics endpoint (/v1/usage)"
  - "Simple dashboard (HTMX + Tailwind CSS)"
  - "Dashboard: API key management UI"
  - "Dashboard: usage charts"
  - "Dashboard: cost breakdown"
```

### Tasks

```yaml
tasks:
  T3.1:
    action: "Add Conversation and Message SQLAlchemy models"
    migration: "Alembic revision"

  T3.2:
    action: "Implement Agent Memory CRUD"
    endpoints:
      - "POST /v1/memory/conversations"
      - "POST /v1/memory/conversations/{id}/messages"
      - "GET /v1/memory/conversations/{id}/messages"
      - "GET /v1/memory/conversations"
      - "DELETE /v1/memory/conversations/{id}"

  T3.3:
    action: "Implement context window management"
    logic: "When total tokens > context limit, auto-truncate oldest messages"
    note: "Return warning header: X-Context-Truncated: true"

  T3.4:
    action: "Implement /v1/usage endpoint"
    response: "Token counts, cost breakdown by provider/model, time series"

  T3.5:
    action: "Set up dashboard (HTMX + Tailwind CSS)"
    files: ["src/phi_gateway/dashboard/"]
    note: "Serve as part of FastAPI app (Jinja2 templates) or separate static"

  T3.6:
    action: "Dashboard: API key management page"
    features: ["Create key", "List keys", "Revoke key", "Copy key (shown once)"]

  T3.7:
    action: "Dashboard: usage page"
    features: ["Token usage chart", "Cost by provider", "Request history"]

  T3.8:
    action: "Dashboard: docs browser"
    features: ["OpenAPI/Swagger embed", "Quick-start guide"]
```

---

## PHASE 4: Landing Page + Deploy + Docs (Week 7-8)

**Goal:** Public launch ready.

### Deliverables

```yaml
phase_4_deliverables:
  - "Landing page (phiconsulting.biz.id)"
  - "Bilingual documentation (EN + ID)"
  - "Deployment guide for VPS"
  - "Caddy configuration for both api. and root domain"
  - "Waitlist/signup form"
  - "README.md (human-readable)"
  - "CONTRIBUTING.md"
  - "LICENSE (MIT)"
```

### Tasks

```yaml
tasks:
  T4.1:
    action: "Create landing page"
    stack: "Static HTML + Tailwind CSS (CDN) + minimal JS"
    sections:
      - "Hero: 'Agent-First API Platform'"
      - "What it does (4 primitives: Proxy, Tools, KB, Memory)"
      - "Code snippet (curl example)"
      - "Pricing tiers"
      - "Waitlist/CTA"
    file: "Serve via Caddy static file from /srv/landing"

  T4.2:
    action: "Create bilingual docs"
    format: "Markdown → serve as static site or embed in dashboard"
    content: "Quick start, API reference, examples in Python + JS"

  T4.3:
    action: "Write deployment guide"
    steps:
      - "Provision Ubuntu VPS"
      - "Install Docker + docker compose"
      - "Clone repo"
      - "Configure .env with API keys"
      - "docker compose up -d"
      - "Point DNS A record to VPS IP"
      - "SSL auto-provisioned by Caddy"

  T4.4:
    action: "Configure DNS"
    records:
      - "phiconsulting.biz.id → VPS IP (A record)"
      - "api.phiconsulting.biz.id → VPS IP (CNAME or A record)"

  T4.5:
    action: "Final review + hardening"
    checklist:
      - "All tests pass"
      - "Rate limiting verified"
      - "Error handling for all endpoints"
      - "No secrets in codebase"
      - "AGENTS.md is accurate"
```

---

## TESTING STRATEGY

```yaml
testing:
  unit: "pytest for services, models, utilities"
  integration: "httpx + pytest-asyncio for API endpoints"
  coverage_target: ">80% for core services (LLM proxy, auth, tool registry)"

  test_organization:
    path: "tests/"
    structure:
      - "tests/unit/ — pure function tests"
      - "tests/integration/ — API endpoint tests (uses TestClient)"
      - "tests/conftest.py — fixtures: test DB, test API key, mock LLM responses"

  ci_plan: "GitHub Actions: pytest on push, lint with ruff"
```

---

## DEPENDENCIES (requirements.txt / pyproject.toml)

```text
# Core
fastapi>=0.115.0
uvicorn[standard]>=0.34.0
pydantic>=2.10.0
pydantic-settings>=2.7.0

# Database
sqlalchemy[asyncio]>=2.0.36
aiosqlite>=0.20.0
alembic>=1.14.0
sqlite-vec>=0.1.0

# LLM Clients
openai>=1.60.0
anthropic>=0.40.0
groq>=0.15.0

# Auth
bcrypt>=4.2.0

# HTTP (for tool proxy calls)
httpx>=0.28.0

# Dev
pytest>=8.3.0
pytest-asyncio>=0.24.0
httpx>=0.28.0
ruff>=0.8.0
```

---

## PHASE GATES

```yaml
gate_1_end_of_phase_1:
  condition: "LLM proxy works E2E with all configured providers"
  proceed: "Phase 2"

gate_2_end_of_phase_2:
  condition: "Tool registry + KB search works; MCP endpoint functional"
  proceed: "Phase 3"

gate_3_end_of_phase_3:
  condition: "Memory API + dashboard functional; usage tracking works"
  proceed: "Phase 4"

gate_4_launch:
  condition: "Landing page live, docs published, deployment guide tested"
  action: "LAUNCH"
```

---

## QUICK-START (FUTURE DEVELOPER)

```bash
# What the end-user experience will be (Phase 4 deliverable)

# 1. Clone
git clone https://github.com/raindragon14/phi-gateway
cd phi-gateway

# 2. Configure
cp .env.example .env
# Edit .env: add OPENAI_API_KEY, ANTHROPIC_API_KEY, GROQ_API_KEY

# 3. Deploy
docker compose up -d

# 4. Create API key
curl -X POST https://api.phiconsulting.biz.id/v1/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "dev", "tier": "free"}'

# 5. Use it
curl https://api.phiconsulting.biz.id/v1/chat/completions \
  -H "Authorization: Bearer phi-sk-abc12345..." \
  -H "Content-Type: application/json" \
  -d '{
    "model": "groq/llama-3.3-70b",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

---

*End of implementation plan. Return to AGENTS.md for handoff instructions.*
