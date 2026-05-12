#!/bin/bash
# Phi AI Gateway — Auto-Update Script
# Run via cron or systemd timer to pull latest from git and redeploy
# Usage: ./auto-update.sh [branch] [repo_url]

set -e

BRANCH="${1:-staging}"
REPO_URL="${2:-https://github.com/raindragon14/phi-gateway.git}"
APP_DIR="/opt/phi-gateway"
LOG_FILE="/var/log/phi-gateway-update.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== Auto-update check ==="

# Clone if first run
if [ ! -d "$APP_DIR" ]; then
    log "First run — cloning repo..."
    git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
else
    cd "$APP_DIR"
    
    # Fetch and check for changes
    git fetch origin "$BRANCH"
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse "origin/$BRANCH")
    
    if [ "$LOCAL" = "$REMOTE" ]; then
        log "No changes detected. Skipping redeploy."
        exit 0
    fi
    
    log "Changes detected! Pulling..."
    git pull origin "$BRANCH"
fi

# Ensure .env exists
if [ ! -f .env ]; then
    log "WARNING: .env not found — copying from .env.example"
    cp .env.example .env
    log ">>> You must edit .env with real API keys! <<<"
    exit 1
fi

# Update Caddyfile with domain
if [ -n "${DOMAIN}" ]; then
    cat > Caddyfile << CADDYEOF
api.${DOMAIN} {
    reverse_proxy api:8000
}

staging.${DOMAIN} {
    reverse_proxy api:8000
}

${DOMAIN} {
    root * /srv/landing
    file_server
}
CADDYEOF
    log "Caddyfile updated for $DOMAIN"
fi

# Rebuild and restart
log "Building Docker image..."
docker compose build --no-cache api

log "Restarting services..."
docker compose down --remove-orphans
docker compose up -d

# Health check
log "Waiting for API health check..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        log "API healthy!"
        break
    fi
    sleep 2
done

log "Deploy complete. Services running:"
docker compose ps
