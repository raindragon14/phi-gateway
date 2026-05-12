# Phi AI Gateway — Deployment Checklist

## Before deploying

- [ ] Edit `.env` and add your LLM API keys (at least one)
- [ ] Ensure your domain DNS is pointed to the VPS IP
- [ ] Verify the VPS has 4GB+ RAM

## Quick deploy (one command)

```bash
cd /opt
git clone https://github.com/raindragon14/phi-gateway.git
cd phi-gateway
cp .env.example .env
# EDIT .env NOW with your API keys
bash deploy.sh your-domain.com
```

## Manual deploy steps

### 1. Install Docker on the VPS

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Log out and back in
```

### 2. Clone and configure

```bash
cd /opt
git clone https://github.com/raindragon14/phi-gateway.git
cd phi-gateway
cp .env.example .env
nano .env  # Add your LLM API keys
```

### 3. Configure the domain in Caddyfile

```bash
# Edit Caddyfile, replace phiconsulting.biz.id with your domain
nano Caddyfile
```

### 4. Build and start

```bash
docker compose build --no-cache api
docker compose up -d
```

### 5. Verify

```bash
# Check services
docker compose ps

# Wait 10 seconds, then test
curl http://localhost:8000/health
```

### 6. Create first API key

```bash
curl -X POST https://api.your-domain.com/v1/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "admin", "tier": "pro"}'
```

### 7. Test chat

```bash
curl https://api.your-domain.com/v1/chat/completions \
  -H "Authorization: Bearer <your-key>" \
  -H "Content-Type: application/json" \
  -d '{"model": "groq/llama-3.3-70b", "messages": [{"role": "user", "content": "Hello!"}]}'
```

## Systemd (for auto-restart on reboot)

```bash
sudo cp deploy/phi-gateway.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable phi-gateway
sudo systemctl start phi-gateway
```

## Ports

| Port | Service | Notes |
|------|---------|-------|
| 80 | Caddy (HTTP) | Redirects to 443 |
| 443 | Caddy (HTTPS) | Auto SSL via Let's Encrypt |
| 8000 | FastAPI | Internal only (not exposed to internet) |

## Troubleshooting

| Problem | Check |
|---------|-------|
| Container won't start | `docker compose logs api --tail=50` |
| 502 on chat | Check `.env` has valid API keys for that provider |
| SSL not provisioned | Wait 1-2 minutes, verify DNS propagated with `dig api.your-domain.com` |
| Database locked | SQLite single-writer limit — migrate to PostgreSQL at >100 concurrent users |
| RAM full | Check `docker stats`, resize VPS if needed |
