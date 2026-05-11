#!/bin/bash
# Phi AI Gateway — VPS Deployment Script
# Run as root or user with Docker permissions (sudo usermod -aG docker $USER)

set -e

DOMAIN="${1:-phiconsulting.biz.id}"
REPO_URL="${2:-https://github.com/phiconsulting/phi-gateway.git}"

echo "=== Phi AI Gateway Deployment ==="
echo "Domain: $DOMAIN"
echo ""

# 1. Clone / update repo
if [ -d "phi-gateway" ]; then
    echo "[1/6] Updating existing repo..."
    cd phi-gateway
    git pull origin main || true
else
    echo "[1/6] Cloning repo..."
    git clone "$REPO_URL" phi-gateway
    cd phi-gateway
fi

# 2. Configure environment
echo "[2/6] Configuring environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  Created .env from .env.example"
    echo "  >>> EDIT .env NOW with your LLM API keys, then re-run this script <<<"
    exit 1
fi

# 3. Configure Caddy for the domain
echo "[3/6] Configuring Caddy for $DOMAIN..."
cat > Caddyfile << CADDYEOF
api.${DOMAIN} {
    reverse_proxy api:8000
}

${DOMAIN} {
    root * /srv/landing
    file_server
}
CADDYEOF
echo "  Caddyfile updated for $DOMAIN"

# 4. Build and start services
echo "[4/6] Building and starting services..."
docker compose down --remove-orphans 2>/dev/null || true
docker compose build --no-cache api
docker compose up -d

# 5. Wait for healthy
echo "[5/6] Waiting for API to become healthy..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo "  API is healthy!"
        break
    fi
    sleep 2
done

# 6. Done
echo "[6/6] Deployment complete!"
echo ""
echo "Services:"
docker compose ps
echo ""
echo "Next steps:"
echo "  1. Ensure DNS is configured:"
echo "     A record for $DOMAIN → $(curl -s ifconfig.me)"
echo "     A record for api.$DOMAIN → $(curl -s ifconfig.me)"
echo "  2. Caddy will auto-provision SSL within 30 seconds of DNS propagation"
echo "  3. Create your first API key:"
echo "     curl -X POST https://api.${DOMAIN}/v1/keys -H 'Content-Type: application/json' -d '{\"name\":\"admin\",\"tier\":\"pro\"}'"
echo "  4. Visit: https://${DOMAIN} (landing page)"
echo "           https://${DOMAIN}/dashboard (admin UI)"
echo "           https://api.${DOMAIN}/docs (Swagger)"
