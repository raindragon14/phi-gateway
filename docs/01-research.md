# 01 — Market Research

> Part of Phi AI Gateway documentation
> Sources: GMInsights, Grand View Research, Postman State of API 2025, Google Cloud Summit Jakarta, AI Alliance Indonesia, various industry reports
> Date: 2026-05-11

---

## 1. GLOBAL AI AGENTS MARKET

```yaml
market_size:
  2024: "USD 5.9 billion (GMInsights)"
  2025: "USD 7.63 billion (Grand View Research)"
  2033: "USD 182.97 billion projected (Grand View Research, CAGR 49.6%)"
  2034: "USD 105.6 billion projected (GMInsights, CAGR 38.5%)"

key_signals:
  - "99% of developers exploring agent development (Runpod)"
  - "23% of organizations scaling agentic systems in at least one function (McKinsey State of AI 2025)"
  - "APIs no longer just powering apps — they're powering agents (Postman State of API 2025)"
  - "AI agent companies defy traditional SaaS valuation models (Finro)"
```

### Ceruk Spesifik: Agent Infrastructure

`Agentic AI in Tool Use & API Integration Market` adalah sub-segmen yang paling relevan. Infrastructure layer ("picks and shovels") lebih defensible daripada application layer.

---

## 2. COMPETITOR LANDSCAPE

### 2.1 LLM Gateways (Direct Competitors)

| Player | Positioning | Weakness vs Phi |
|--------|-------------|-----------------|
| **LiteLLM** | Open-source LLM proxy, 100+ providers, YC-backed | LLM proxy + MCP gateway (routes to external servers). No built-in tool registry or knowledge base. Basic KV memory only. |
| **OpenRouter** | Unified LLM API, cloud-native | Closed source, not self-hostable |
| **Portkey** | AI gateway + observability | Enterprise-focused, too heavy |
| **Kong AI Gateway** | Enterprise API + LLM gateway | Overkill for indie devs |
| **Cloudflare AI Gateway** | Edge LLM proxy | Vendor lock-in, no self-host |

### 2.2 Agent Frameworks (Indirect Competitors)

| Player | Type | Weakness |
|--------|------|----------|
| **LangChain / LangGraph** | Agent orchestration framework | Framework, not platform — devs still build own infra |
| **LangSmith** | Observability + deployment | $39/seat/month, enterprise-only, monitoring focus |
| **CrewAI** | Multi-agent orchestration | Python-only framework, not an API service |
| **AutoGPT / AutoGen** | Autonomous agent frameworks | Overengineered, niche |
| **Letta** | Agent memory platform | Memory only, not a full gateway |

### 2.3 Agent-Native Platforms (Adjacent)

| Player | Description | Status |
|--------|-------------|--------|
| **Zatanna (YC W2026)** | "Turning all software into agent-first APIs" | Early stage |
| **Firecrawl** | Web scraping API for agents | Specific tool, not platform |
| **OpenClaw** | Self-hosted personal AI assistant (100K+ GitHub stars) | Consumer, not B2B |
| **Hermes Agent** | Self-learning AI companion (Nous Research) | Consumer, not B2B |

### Key Insight

```text
No existing platform combines:
  LLM Proxy + Tool Registry (MCP) + Knowledge Base (RAG) + Agent Memory

in one lightweight, self-hostable package.

The infrastructure layer is FRAGMENTED. Developers must stitch together
4-5 different services. Phi AI Gateway unifies them.

OpenClaw and Hermes Agent are potential CUSTOMERS, not competitors.
They need backend infrastructure that Phi Gateway could provide.
```

---

## 3. TECHNOLOGY PROTOCOL LANDSCAPE

| Protocol | Creator | Purpose | Status |
|----------|---------|---------|--------|
| **MCP** (Model Context Protocol) | Anthropic | Agent ↔ Tools (JSON-RPC 2.0) | Becoming de facto standard |
| **A2A** (Agent-to-Agent) | Google | Agent ↔ Agent communication | Early, complementary to MCP |
| **ACP** (Agent Communication Protocol) | Community | Agent interoperability | Nascent |
| **ANP** (Agent Network Protocol) | Community | Agent networking | Experimental |

**Decision:** Phi Gateway must be **MCP-native** from day 1. A2A support can be added later. Google explicitly stated A2A is complementary to MCP, not competing.

---

## 4. INDONESIA OPPORTUNITY

### Data Points

```yaml
indonesia_tech:
  tech_jobs_demand_2025: "600,000+ positions (RainTech Outlook)"
  ai_startups: "35+ AI-focused companies (f6s, Tracxn, TechBehemoths directories)"
  google_accelerator: "1 in 4 SEA participants from Indonesia"
  ai_adoption_growth_2024: "47% surge (Asosiasi AI Indonesia)"
  digital_economy_2029: "USD 49.57 billion projected"
  coding_bootcamp_market: "Growing at 10.4% CAGR"

government_initiatives:
  - "National AI Roadmap White Paper (July 2025)"
  - "Bangkit Bersama AI — Google + Komdigi accelerator"
  - "GenAI Open Innovation Indonesia 2025"
  - "AI Alliance Indonesia Chapter (IBM + Meta, Feb 2025)"
```

### Gap Analysis

| Need | Global Solution | Indonesia | Gap |
|------|----------------|-----------|-----|
| LLM Access | OpenAI, Anthropic API | Partial (USD pricing hurts) | Price |
| Agent Infrastructure | LangSmith, Letta | **None** | **OUR OPPORTUNITY** |
| IDR-native Pricing | None | None | **OUR ADVANTAGE** |
| Bahasa Docs | None | None | **OUR ADVANTAGE** |
| Self-hosting Guide | LiteLLM (English) | No localized guide | Community play |

---

## 5. PRICING BENCHMARKS

### LLM API (per 1M output tokens, 2026)

```yaml
cheapest_models:
  deepseek_v3_2: "USD 0.42"
  gpt5_nano: "USD 0.40"
  groq_llama_70b: "~USD 0.60"
  gemini_flash: "~USD 0.50"

sweet_spot:
  gpt5_mini: "USD 2.00"
  claude_haiku_4_5: "USD 5.00"

expensive:
  gpt5_2: "USD 14.00"
  claude_opus_4_6: "USD 25.00"
  gpt5_pro: "USD 14.00+"
```

### Platform/Infrastructure Pricing

| Platform | Free | Paid |
|----------|------|------|
| LangSmith | 5K traces/mo, 1 seat | $39/seat/month |
| LiteLLM (self-host) | Free | $0 (own infra) |
| Vercel AI SDK | Generous free | Pro $20/month |

### Phi Gateway Proposed Pricing

```yaml
tiers:
  free:
    price_idr: 0
    limits: "10K API calls/month, 1 project, community support"

  pro:
    price_idr: 150000
    price_usd_approx: "~$9"
    limits: "100K calls/month, 5 projects, email support"

  team:
    price_idr: 500000
    price_usd_approx: "~$30"
    limits: "500K calls/month, unlimited projects, priority"

  self_host:
    price_idr: 0
    note: "Bring your own API keys, open source (MIT)"
```

**Why this works:**
- Free tier generous enough for indie hackers to try → converts to Pro
- Rp 150K is 4x cheaper than LangSmith's $39
- IDR pricing = competitive moat vs all USD-based global players
- Self-host option for privacy-maximalists and cost-sensitive users

---

## 6. TARGET BEACHHEAD

```yaml
primary_segment: "AI indie hackers & dev agencies in Indonesia"
secondary_segment: "SEA developers building AI agents"
tertiary_segment: "Global indie devs who want lightweight self-hosted agent infra"

channels:
  - "Indonesian AI Telegram/Discord communities"
  - "Twitter/X AI dev circles"
  - "GitHub (open source + README in Bahasa + English)"
  - "Google Developer Groups Indonesia"
  - "AI Alliance Indonesia network"

pivot_signal: "If <50 signups in 3 months → pivot to enterprise/internal tools play"
```

---

## 7. RISK ASSESSMENT (MINI PRE-MORTEM)

| # | Risk | Impact | Likelihood | Score | Mitigation |
|---|------|--------|-----------|-------|------------|
| 1 | Vendor lock-in to upstream LLM APIs | 8 | 7 | 56 | Multi-provider proxy + auto-failover |
| 2 | Developers don't understand "agent-first" concept | 7 | 5 | 35 | Tutorial, demo agent, AGENTS.md education |
| 3 | Low adoption in Indonesia (market too early) | 8 | 4 | 32 | Community building, patience, pivot option |
| 4 | RAM insufficient at scale (>100 users) | 5 | 6 | 30 | VPS resizable, architecture supports horizontal scale |
| 5 | LiteLLM copies our differentiators | 6 | 5 | 30 | Indonesia/SEA localization moat |
| 6 | MCP/A2A standard fragmentation | 7 | 4 | 28 | Support both, abstraction layer |
| 7 | Big tech (Google/OpenAI) enters space | 9 | 3 | 27 | They target enterprise; we target indie/SEA |
| 8 | Data privacy compliance (PDP/GDPR) | 6 | 5 | 30 | Privacy-by-design, data residency in ID, clear DPA |

**Top 4 fatal risks:**
1. **Vendor lock-in (56)** — upstream LLM dependency is existential. Mitigated by multi-provider.
2. **Market education gap (35)** — "agent-first API" is a new category. Need content marketing.
3. **Compliance risk (30)** — Indonesia PDP Law mirrors GDPR; user data handling must be compliant from day 1. Mitigated by privacy-by-design, minimal data collection, clear DPA.
4. **Indonesia adoption risk (32)** — market might not be ready. Have pivot strategy ready.

---

## 8. COMPETITIVE POSITIONING

```yaml
positioning_statement: >
  Phi AI Gateway is an agent-first API platform providing all primitives
  AI agents need (LLM proxy, tool registry, knowledge base, memory) in
  one lightweight service. Designed for Indonesian developers who want to
  build AI agents without stitching together 5 different services.
  docker compose up. Harga Rupiah.

differentiators:
  indonesia_first: "Bilingual docs, IDR pricing, local community focus"
  all_in_one: "LLM + Tools + KB + Memory = single API endpoint"
  self_host_friendly: "Runs on 4GB VPS, single docker compose up"
  agent_first: "AGENTS.md, MCP-native, machine-readable contracts"
  open_source_core: "MIT license, transparent, auditable"
  affordable: "Free tier, Pro Rp 150K/month"

market_gap: >
  Infrastructure layer of the AI agent stack is FRAGMENTED.
  No dominant player. LiteLLM covers LLM proxy (+ basic KV memory).
  Letta covers memory. No one covers all four primitives (LLM proxy +
  built-in tool registry + RAG knowledge base + structured agent memory)
  in one package. Window of opportunity is open NOW — but won't stay open forever.
```

---

*Next: docs/02-architecture.md*
