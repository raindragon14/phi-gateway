# OPS.md — PhiGateway Operations Runbook

> Quick reference for the on-call engineer. Keep this page open.

## Restart

```bash
docker compose restart api
```

## View Logs

```bash
# Follow all services
docker compose logs -f

# Follow just the API
docker compose logs -f api

# Tail last 100 lines
docker compose logs --tail=100 api
```

## Backup Database

### SQLite (default)

```bash
# Manual backup
cp /path/to/phi.db /path/to/backups/phi-$(date +%F).db

# Or use the provided script
./scripts/backup-db.sh
```

### PostgreSQL (production)

```bash
pg_dump -U user -h host phi_gateway > backup-$(date +%F).sql
```

## Health Check

```bash
curl -s http://localhost:8000/health | jq .
```

Expected response:
```json
{
  "status": "ok",
  "version": "0.1.1",
  "db_status": "ok",
  "uptime": 1234.56
}
```

## Docker HEALTHCHECK (production)

The following is already configured in `docker-compose.yml`:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## Scaling

> **Note:** Scaling beyond a single instance requires PostgreSQL and Redis.

```bash
# Scale to 3 API containers (with PostgreSQL + Redis backend)
docker compose up -d --scale api=3
```

Prerequisites for horizontal scaling:
- PostgreSQL instead of SQLite (`DATABASE_URL=postgresql+asyncpg://...`)
- Redis-backed rate limiting (replace in-memory dicts in `rate_limiter.py`)
- Shared file storage for knowledge base uploads (S3/MinIO/NFS)

## Upgrade Procedure

```bash
# 1. Pull latest code
git pull

# 2. Rebuild images
docker compose build

# 3. Restart services
docker compose up -d

# 4. Verify health
curl -s http://localhost:8000/health | jq .

# 5. Check logs for errors
docker compose logs --tail=50 api
```

## Rollback

```bash
# Revert to previous tagged version
git checkout v0.1.0
docker compose build
docker compose up -d
```

## Common Issues

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `Connection refused` on startup | DB not ready | `docker compose restart db` or wait for SQLite file |
| `429 Too Many Requests` | Rate limit hit | Check `rate_limiter.py` config or scale up |
| `413 Request Entity Too Large` | Body exceeds `MAX_REQUEST_BODY_SIZE` | Increase limit in `.env` or reduce payload |
| `engine disposed` errors | Worker restart during request | Increase graceful timeout or disable restart on failure |

## Logs & Monitoring

- Application logs: JSON-structured to stdout via `log_config.py`
- Uvicorn access logs: JSON format with `request_id`, `method`, `path`, `status_code`, `duration_ms`
- Log retention: handled by container runtime (Docker), typically 14 days
- Metrics: `/health` endpoint exposes uptime and DB status

## Cron Jobs (recommended)

```cron
# Backup SQLite database daily at 2 AM, keep 30 days
0 2 * * * /path/to/phi-gateway/scripts/backup-db.sh

# Health check ping (optional)
*/5 * * * * curl -sf http://localhost:8000/health > /dev/null 2>&1 || logger -t phi-gateway "Health check failed"
```
