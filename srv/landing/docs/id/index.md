# Phi AI Gateway — Panduan Cepat

> Platform API untuk Agen AI

## Memulai

### 1. Dapatkan API Key

```bash
curl -X POST https://api.phiconsulting.biz.id/v1/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "dev", "tier": "free"}'
```

Respons: `{"key": "phi-sk-...", "prefix": "phi-sk-...", "name": "dev", "tier": "free"}`

### 2. Chat dengan LLM

```bash
curl https://api.phiconsulting.biz.id/v1/chat/completions \
  -H "Authorization: Bearer <key-anda>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "groq/llama-3.3-70b",
    "messages": [{"role": "user", "content": "Halo!"}]
  }'
```

### 3. Daftarkan Tools

```bash
curl -X POST https://api.phiconsulting.biz.id/v1/tools \
  -H "Authorization: Bearer <key-anda>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "cari_web",
    "description": "Mencari informasi di web",
    "json_schema": {
      "type": "object",
      "properties": {"q": {"type": "string"}},
      "required": ["q"]
    },
    "endpoint": "https://endpoint-tools-anda.com/cari"
  }'
```

### 4. Gunakan MCP

```bash
curl -X POST https://api.phiconsulting.biz.id/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":"1"}'
```

### 5. Buat Knowledge Base

```bash
# Buat KB
curl -X POST https://api.phiconsulting.biz.id/v1/kb \
  -H "Authorization: Bearer <key-anda>" \
  -H "Content-Type: application/json" \
  -d '{"name": "dokumen", "description": "Dokumentasi produk"}'

# Masukkan dokumen
curl -X POST https://api.phiconsulting.biz.id/v1/kb/{kb_id}/documents \
  -H "Authorization: Bearer <key-anda>" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {"title": "Panduan", "content": "Isi dokumen...", "metadata": {"source": "docs"}}
    ]
  }'

# Cari
curl -X POST https://api.phiconsulting.biz.id/v1/kb/{kb_id}/search \
  -H "Authorization: Bearer <key-anda>" \
  -H "Content-Type: application/json" \
  -d '{"query": "pertanyaan anda", "top_k": 5}'
```

### 6. Gunakan Agent Memory

```bash
# Buat percakapan
curl -X POST https://api.phiconsulting.biz.id/v1/memory/conversations \
  -H "Authorization: Bearer <key-anda>" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "session-1", "title": "Chat Saya"}'

# Tambah pesan
curl -X POST https://api.phiconsulting.biz.id/v1/memory/conversations/{id}/messages \
  -H "Authorization: Bearer <key-anda>" \
  -H "Content-Type: application/json" \
  -d '{"role": "user", "content": "Halo!", "token_count": 5}'

# Lihat riwayat
curl -X GET https://api.phiconsulting.biz.id/v1/memory/conversations/{id}/messages?limit=50 \
  -H "Authorization: Bearer <key-anda>"
```

## Referensi API

Spesifikasi OpenAPI 3.1 tersedia di `/docs` (Swagger UI) atau `/openapi.json`.

## Self-Hosting

```bash
git clone https://github.com/phiconsulting/phi-gateway
cd phi-gateway
cp .env.example .env
# Edit .env dengan API keys LLM anda
docker compose up -d
```

Persyaratan: VPS 4GB, Docker, nama domain dengan DNS mengarah ke server anda.
