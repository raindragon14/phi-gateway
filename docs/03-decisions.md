# 03 — Architecture Decision Records

> Part of Phi AI Gateway documentation
> Date: 2026-05-11
> Status: ALL DECISIONS FINALIZED

---

## ADR-001: Path A — Pure Infrastructure (No OpenClaw/Hermes Dependency)

**Date:** 2026-05-11
**Status:** Accepted

### Context

Two alternative paths were considered:
- **Path B:** Deploy OpenClaw or Hermes Agent and offer managed hosting
- **Path C:** Hybrid — build Phi Gateway as API backend + OpenClaw/Hermes as showcase agent

### Decision

**Choose Path A: Build Phi AI Gateway as a pure infrastructure platform.**

No dependency on OpenClaw, Hermes Agent, or any existing agent framework.

### Rationale

1. OpenClaw and Hermes are consumer products (personal AI assistants). Phi Gateway is B2B developer infrastructure. Different markets, different DNA.
2. Depending on upstream open-source projects creates fragility. OpenClaw had 400+ malicious plugins on launch. Hermes is governed by Nous Research's roadmap.
3. Pure infrastructure has a cleaner monetization path: API usage billing.
4. Building from scratch = full control over architecture, security, MCP compliance, RAM optimization.
5. OpenClaw/Hermes can still be integration targets later (they need infrastructure backends — Phi Gateway could serve them).

### Consequences

- Longer time to first demo (build from scratch vs deploy existing)
- Full control over roadmap and architecture
- Clearer competitive differentiation
- No upstream dependency risk

---

## ADR-002: Python + FastAPI over Go/Rust/Node.js

**Date:** 2026-05-11
**Status:** Accepted

### Context

Backend language/framework selected for a developer-tools API platform running on 4GB VPS.

### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **Python + FastAPI** | AI ecosystem (LangChain, OpenAI SDK), async native, Pydantic validation, auto OpenAPI | GIL, slower than Go/Rust |
| Go + Chi/Fiber | Fast, low memory, single binary | Smaller AI ecosystem, fewer SDKs |
| Rust + Axum | Fastest, safest, lowest memory | Longest dev time, steep learning curve |
| Node.js + Express/Fastify | Large ecosystem | Memory heavy, callback complexity |

### Decision

**Choose Python 3.12 + FastAPI.**

### Rationale

1. **AI ecosystem dominance.** OpenAI SDK, Anthropic SDK, LangChain, LlamaIndex, sentence-transformers — all Python-first. Using anything else means wrapper maintenance burden.
2. **FastAPI's auto OpenAPI 3.1** aligns with "agent-first" philosophy — machine-readable API docs by default.
3. **Pydantic v2** gives fast validation with JSON Schema export — perfect for MCP tool definitions.
4. **Development speed.** For a solo developer, Python development is 2-3x faster than Go/Rust.
5. **4GB RAM is sufficient.** FastAPI + uvicorn with 2 workers uses ~300MB. The 4GB constraint is about service count, not language choice.
6. **Go/Rust advantages** (lower RAM, faster) don't matter at MVP scale. Premature optimization.

### Consequences

- ~300MB RAM for API workers (acceptable within budget)
- Need to be mindful of async patterns (avoid blocking calls)
- Migration path: if scale demands it, individual services can be rewritten in Go/Rust later

---

## ADR-003: SQLite + sqlite-vec over PostgreSQL + ChromaDB

**Date:** 2026-05-11
**Status:** Accepted

### Context

Database selection for MVP running on 4GB VPS. Needs to store: API keys, LLM request logs, tool definitions, knowledge base documents + vectors, conversation memory.

### Options Considered

| Option | RAM Usage | Ops Burden | Vector Support |
|--------|-----------|------------|----------------|
| **SQLite + sqlite-vec** | ~20-200 MB | Zero (single file) | sqlite-vec extension |
| PostgreSQL + pgvector | ~300+ MB | Service management | Built-in |
| PostgreSQL + ChromaDB | ~500+ MB | Two services | Dedicated vector DB |
| Supabase (managed) | N/A (external) | Zero (but vendor lock) | pgvector |

### Decision

**Choose SQLite + sqlite-vec for MVP.**

### Rationale

1. **Zero operational overhead.** Single file, no separate service, no connection pool management.
2. **sqlite-vec is designed for fast vector search at small-to-medium scale** (community benchmarks show significant speed advantages over pgvector for single-node deployments — [sqlite-vec GitHub issue #94](https://github.com/asg017/sqlite-vec/issues/94)).
3. **RAM fits budget.** SQLite ~20MB + vector index ~200MB = well within 4GB.
4. **PostgreSQL needs 300MB+** just for the service, plus connection pool overhead.
5. **No vendor lock-in.** sqlite-vec is an extension, not a separate service.
6. **Easy migration path.** SQLAlchemy abstracts the DB. When >100 concurrent users need write scaling, migrate to PostgreSQL by changing one connection string.

### Consequences

- Single-writer limitation (acceptable for MVP — if we hit this bottleneck, we're succeeding)
- No built-in replication (not needed for single VPS)
- Alembic migrations work the same — schema changes are DB-agnostic

---

## ADR-004: Caddy over Nginx

**Date:** 2026-05-11
**Status:** Accepted

### Context

Reverse proxy needed to terminate SSL and route traffic to FastAPI on the VPS.

### Options Considered

| Option | RAM | Config Complexity | SSL |
|--------|-----|-------------------|-----|
| **Caddy** | ~50 MB | Minimal (Caddyfile) | Automatic |
| Nginx | ~50 MB | Complex (nginx.conf) | Certbot needed |
| Traefik | ~100+ MB | Moderate | Automatic |
| No proxy (FastAPI direct) | 0 MB | None | Manual SSL |

### Decision

**Choose Caddy.**

### Rationale

1. **Auto SSL via Let's Encrypt** with zero configuration. Nginx needs Certbot + cron.
2. **Single binary, ~50MB RAM.**
3. **Caddyfile is readable** — 5 lines for basic reverse proxy with SSL.
4. **HTTP/3 support** built-in.
5. No proxy is not an option — need SSL termination and static file serving for landing page.

### Consequences

- Caddyfile syntax is different from Nginx (but simpler)
- Caddy is less common in enterprise — fine for our indie/startup target

---

## ADR-005: Proxy-First, Not Local LLM

**Date:** 2026-05-11
**Status:** Accepted

### Context

Should the platform run LLMs locally (via Ollama) or proxy to external APIs?

### Options Considered

| Option | RAM Needed | Model Quality | Latency | Privacy |
|--------|-----------|---------------|---------|---------|
| **Proxy-only** | 0 MB extra | Best (GPT-5, Claude) | ~500ms | API provider sees data |
| **Local Ollama** | ~2.5 GB | Limited (Qwen 2.5 3B, Llama 3.2 3B) | ~5-30s on CPU | Full privacy |
| **Hybrid** | ~3.3 GB total | Flexible | Varies | Configurable |

### Decision

**Proxy-first. Local LLM is optional, not default.**

### Rationale

1. **4GB RAM constraint.** Ollama + a small 3B model uses ~2.5GB. That leaves only ~700MB for everything else — too tight.
2. **Model quality gap.** Qwen 2.5 3B cannot match GPT-5 mini or Claude Haiku for agent tasks.
3. **Groq has a generous free tier** — developers can start with zero LLM cost.
4. **Developers can bring their own API keys** — Phi Gateway just routes.
5. **Local LLM can be a premium feature later** — when VPS is resized to 8GB+.

### Consequences

- Must handle API key management for multiple LLM providers
- Must implement auto-failover between providers
- Privacy-conscious users may want local option — keep architecture extensible for it

---

## ADR-006: MCP Protocol from Day 1

**Date:** 2026-05-11
**Status:** Accepted

### Context

Which agent-tool communication protocol to support?

### Options

| Option | Status | Backed By |
|--------|--------|-----------|
| **MCP (JSON-RPC 2.0)** | Growing fast | Anthropic + community |
| A2A | Early, complementary | Google |
| Custom REST | Full control | Nobody (standard preferred) |

### Decision

**Implement MCP (Model Context Protocol) natively from day 1. Add A2A later.**

### Rationale

1. MCP is becoming the de facto standard. Claude Desktop, Continue.dev, Sourcegraph Cody, and 100+ tools already support it.
2. Google explicitly stated A2A is **complementary** to MCP, not competing.
3. MCP uses JSON-RPC 2.0, which is simple, well-documented, and fits FastAPI.
4. Being MCP-native = instant compatibility with the growing MCP ecosystem.
5. A2A (agent-to-agent communication) is lower priority for MVP. Our initial users will build single-agent systems.

### Consequences

- Tool registry must follow MCP specification
- `/mcp` endpoint implements JSON-RPC 2.0 methods: `tools/list`, `tools/call`, `resources/list`, `resources/read`
- Future: add `/a2a` endpoint when multi-agent orchestration is needed

---

## ADR-007: Beachhead — Indonesian AI Indie Hackers + Dev Agencies

**Date:** 2026-05-11
**Status:** Accepted

### Context

Initial target market selection. Global vs regional vs local focus.

### Options Considered

| Option | TAM | Competition | Localization |
|--------|-----|-------------|--------------|
| **Global from day 1** | Huge | Intense (LiteLLM, LangSmith) | English only |
| **SEA region** | Growing | Moderate | English + partial localization |
| **Indonesia first** | Smaller but underserved | **Zero local competitors** | Full Bahasa + IDR pricing |

### Decision

**Indonesia-first beachhead. Expand to SEA later, global last.**

### Rationale

1. **Zero local competitors** in agent infrastructure. First-mover advantage.
2. **IDR pricing** is a competitive moat. No global player offers Rupiah billing.
3. **Bahasa Indonesia documentation** reduces barrier for local devs.
4. **Smaller market = easier to dominate.** Indonesia's 45+ AI startups + 600K tech workers = sufficient initial TAM.
5. **Community channels exist** — AI Telegram/Discord groups, GDG Indonesia, AI Alliance Indonesia.
6. **Pivot option:** if Indonesia adoption is too slow, the product is inherently global (REST APIs are language-agnostic).

### Consequences

- Documentation must be bilingual (English primary for code, Bahasa for guides)
- Pricing page in IDR with USD equivalent
- Marketing focused on Indonesian dev communities
- Must comply with Indonesia PDP Law (mirrors GDPR) for user data handling
- Pivot signal: <50 signups in 3 months → reassess

---

## ADR-008: API-Key-Only Auth (No User Accounts for MVP)

**Date:** 2026-05-11
**Status:** Accepted

### Context

Authentication model: full user accounts (email, password, OAuth) vs simple API keys.

### Decision

**API keys only for MVP. No user accounts, no OAuth, no sessions.**

### Rationale

1. This is a developer-tools API platform — devs expect API key auth.
2. User accounts add: email verification, password hashing, session management, password reset, OAuth integration — all unnecessary complexity for MVP.
3. API key = the user. One person can have multiple keys (dev, prod, testing).
4. Future: add user accounts when dashboard needs login. MVP dashboard can be key-only.
5. Follows Stripe's early model: simple API keys, add accounts later.

### Consequences

- No "forgot password" flow needed (simpler)
- Key shown only once on creation (like Stripe/OpenAI)
- Must implement key hashing (bcrypt) — never store plaintext
- Dashboard access via API key in URL or header (temporary — add sessions later)

---

## Decision Summary

```yaml
adrs:
  "001": "Path A — Pure infrastructure, no OpenClaw/Hermes dependency"
  "002": "Python 3.12 + FastAPI"
  "003": "SQLite + sqlite-vec (not PostgreSQL + ChromaDB)"
  "004": "Caddy (not Nginx)"
  "005": "Proxy-first, local LLM optional (not default local LLM)"
  "006": "MCP protocol from day 1, A2A later"
  "007": "Indonesia-first beachhead"
  "008": "API-key-only auth, no user accounts for MVP"
```

---

*Next: docs/04-implementation.md*
