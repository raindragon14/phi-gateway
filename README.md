# PhiGateway

Self-hosted AI gateway. LLM proxy, tool registry, RAG knowledge base, and agent memory behind one OpenAI-compatible endpoint.

[![CI](https://img.shields.io/github/actions/workflow/status/raindragon14/phi-gateway/ci.yml?branch=main&label=CI&logo=github)](https://github.com/raindragon14/phi-gateway/actions)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Install

```bash
pip install phi-gateway
```

## Quick Start

```bash
# Start the gateway
uvicorn phi_gateway.main:app

# Create an API key
curl -sX POST http://localhost:8000/v1/keys \
  -H "Content-Type: application/json" \
  -d '{"name":"my-agent","tier":"free"}'

# Chat through the gateway
curl -s http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer phi-sk-..." \
  -H "Content-Type: application/json" \
  -d '{"model":"groq/llama-3.3-70b","messages":[{"role":"user","content":"Hello"}]}'
```

With Docker:

```bash
git clone https://github.com/raindragon14/phi-gateway
cd phi-gateway
cp .env.example .env    # add your provider keys
docker compose up -d
```

## What It Does

**LLM Proxy** — Route to OpenAI, Anthropic, Groq, or OpenRouter. Switch providers or use fallback chains without changing agent code. Streaming, cost tracking, and logging included.

**Tool Registry** — Register tools with JSON Schema. Agents discover and call them via REST or MCP (JSON-RPC 2.0). MCP-native.

**Knowledge Base** — Chunk, embed, and search documents. Cosine similarity with keyword fallback. Everything in SQLite. No external vector database.

**Agent Memory** — Store conversations, paginate history, auto-trim context. Returns `X-Context-Truncated` header when messages are trimmed.

## Usage

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="phi-sk-...")
response = client.chat.completions.create(
    model="groq/llama-3.3-70b",
    messages=[{"role": "user", "content": "Hello"}],
)
```

Full API reference at `/docs` when the server is running.

## Architecture

```
Caddy (reverse proxy, auto TLS)
  └── FastAPI (uvicorn)
        ├── /v1/chat/completions  →  LLM proxy  →  provider APIs
        ├── /v1/tools             →  tool registry
        ├── /v1/kb                →  RAG (SQLite + cosine similarity)
        ├── /v1/memory            →  agent memory
        ├── /mcp                  →  JSON-RPC 2.0 (MCP)
        └── /dashboard            →  HTMX admin UI
              └── SQLite (single file)
```

Idle RAM: ~250 MB. Python 3.12+. MIT license.

## Development

```bash
pip install -e ".[dev]"
pytest -v
ruff check src/ tests/
```

Code style: Google docstrings, ruff format, pytest. See `pyproject.toml`.

## License

[MIT](LICENSE)
