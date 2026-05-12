# Phi AI Gateway — Deployment Guide

> Deploy on a 4GB VPS with Docker

## Requirements

- VPS with 4GB RAM (Ubuntu 22.04+ or 24.04+)
- Docker Engine 24+ and Docker Compose v2+
- Domain name (e.g., `phiconsulting.biz.id`) with DNS pointing to your server IP
- LLM API keys (at least one): OpenAI, Anthropic, or Groq

## Step 1: Provision the VPS

```bash
# SSH into your server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh

# Enable Docker as non-root
usermod -aG docker $USER
# Log out and back in for changes to take effect

# Verify
docker --version
docker compose version
```

## Step 2: Clone and Configure

```bash
git clone https://github.com/raindragon14/phi-gateway.git
cd phi-gateway

# Create environment config
cp .env.example .env

# Edit .env with your API keys
nano .env
```

`.env` should look like:

```env
DATABASE_URL=sqlite+aiosqlite:///data/phi.db
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...
APP_HOST=0.0.0.0
APP_PORT=8000
```

> **Note:** Only configure the providers you actually use. Leave the rest blank.

## Step 3: Configure DNS

In your domain registrar's DNS settings:

| Record | Type | Value |
|--------|------|-------|
| `api.phiconsulting.biz.id` | A | `<your-vps-ip>` |
| `phiconsulting.biz.id` | A | `<your-vps-ip>` |

Allow 1-5 minutes for DNS propagation.

## Step 4: Start the Services

```bash
docker compose up -d
```

This starts two containers:
- `api` — FastAPI application (port 8000, internal)
- `caddy` — Reverse proxy with auto SSL (ports 80, 443)

## Step 5: Verify

```bash
# Check containers are running
docker compose ps

# Check logs
docker compose logs api --tail=50

# Test health endpoint
curl https://api.phiconsulting.biz.id/health

# Create your first API key
curl -X POST https://api.phiconsulting.biz.id/v1/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "admin", "tier": "free"}'

# Test chat completion (requires an LLM API key configured)
curl -X POST https://api.phiconsulting.biz.id/v1/chat/completions \
  -H "Authorization: Bearer <your-key>" \
  -H "Content-Type: application/json" \
  -d '{"model": "groq/llama-3.3-70b", "messages": [{"role": "user", "content": "Hello!"}]}'
```

## Step 6: (Optional) Add Monitoring

```bash
# Check resource usage
docker stats
```

Expected idle resource usage:
- RAM: ~800-900 MB (both containers)
- CPU: < 5% at idle
- Disk: ~500 MB for images + data

## Auto SSL

Caddy automatically provisions and renews Let's Encrypt SSL certificates. No manual Certbot steps needed.

## Updating

```bash
cd /opt/phi-gateway
git pull
docker compose up -d --build
```

## Backup

The SQLite database is stored in the `phi_data` Docker volume:

```bash
docker run --rm -v phi_data:/data -v $(pwd):/backup alpine \
  cp /data/phi.db /backup/phi-backup-$(date +%Y%m%d).db
```

## Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| `502 Bad Gateway` | Provider API key missing or invalid | Check `.env`, verify key is correct |
| `SSL certificate not ready` | DNS not propagated yet | Wait, or use `curl -k` for testing |
| Container exits immediately | Port 8000 or 80 already in use | `lsof -i :8000` to check |
| `Database is locked` errors | Multiple write-heavy processes | SQLite handles this at scale — migrate to PostgreSQL if persistent |
