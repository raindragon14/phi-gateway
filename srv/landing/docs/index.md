# Phi AI Gateway — Quick Start

> Agent-First API Platform

## Getting Started

### 1. Get an API Key

```bash
curl -X POST https://api.phiconsulting.biz.id/v1/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "dev", "tier": "free"}'
```

Returns: `{"key": "phi-sk-...", "prefix": "phi-sk-...", "name": "dev", "tier": "free"}`

### 2. Chat Completions

```bash
curl https://api.phiconsulting.biz.id/v1/chat/completions \
  -H "Authorization: Bearer <your-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "groq/llama-3.3-70b",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### 3. Register a Tool

```bash
curl -X POST https://api.phiconsulting.biz.id/v1/tools \
  -H "Authorization: Bearer <your-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "web_search",
    "description": "Search the web",
    "json_schema": {
      "type": "object",
      "properties": {"q": {"type": "string"}},
      "required": ["q"]
    },
    "endpoint": "https://your-tool-endpoint.com/search"
  }'
```

### 4. Use MCP

```bash
curl -X POST https://api.phiconsulting.biz.id/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":"1"}'
```

### 5. Create a Knowledge Base

```bash
# Create KB
curl -X POST https://api.phiconsulting.biz.id/v1/kb \
  -H "Authorization: Bearer <your-key>" \
  -H "Content-Type: application/json" \
  -d '{"name": "docs", "description": "Documentation"}'

# Ingest documents
curl -X POST https://api.phiconsulting.biz.id/v1/kb/{kb_id}/documents \
  -H "Authorization: Bearer <your-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {"title": "Getting Started", "content": "Content here...", "metadata": {"source": "docs"}}
    ]
  }'

# Search
curl -X POST https://api.phiconsulting.biz.id/v1/kb/{kb_id}/search \
  -H "Authorization: Bearer <your-key>" \
  -H "Content-Type: application/json" \
  -d '{"query": "your question", "top_k": 5}'
```

### 6. Use Agent Memory

```bash
# Create conversation
curl -X POST https://api.phiconsulting.biz.id/v1/memory/conversations \
  -H "Authorization: Bearer <your-key>" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "session-1", "title": "My Chat"}'

# Add messages
curl -X POST https://api.phiconsulting.biz.id/v1/memory/conversations/{id}/messages \
  -H "Authorization: Bearer <your-key>" \
  -H "Content-Type: application/json" \
  -d '{"role": "user", "content": "Hello!", "token_count": 5}'

# Get history
curl -X GET https://api.phiconsulting.biz.id/v1/memory/conversations/{id}/messages?limit=50 \
  -H "Authorization: Bearer <your-key>"
```

## API Reference

Full OpenAPI 3.1 specification available at `/docs` (Swagger UI) or `/openapi.json`.

## Available Models

| Model | Provider | Context Window |
|-------|----------|----------------|
| `gpt-5-nano` | OpenAI | 400K |
| `gpt-5-mini` | OpenAI | 400K |
| `gpt-5.2` | OpenAI | 400K |
| `claude-haiku-4.5` | Anthropic | 200K |
| `claude-sonnet-4.6` | Anthropic | 200K |
| `groq/llama-3.3-70b` | Groq | 128K |
| `groq/llama-4-scout` | Groq | 128K |

## Self-Hosting

```bash
git clone https://github.com/phiconsulting/phi-gateway
cd phi-gateway
cp .env.example .env
# Edit .env with your LLM API keys
docker compose up -d
```

Requirements: 4GB VPS, Docker, a domain name with DNS pointing to your server.
