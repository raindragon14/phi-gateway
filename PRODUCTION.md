# Production Checklist — PhiGateway

> A running instance with real users. Not just `docker compose up`.

---

## Tier 1: Security (gating items — skip these and you *will* regret it)

- [ ] **Caddy auto TLS verified.** `https://your.domain` loads with a valid Let's Encrypt cert. No self-signed, no HTTP-only.
- [ ] **Secrets out of git.** `.env` in `.gitignore` (already done). All API keys + `PYPI_API_TOKEN` are **environment variables or a secrets manager**, never in the repo.
- [ ] **Default API key tiers configured.** `ApiKey.tier` maps to rate limits (free/pro/team). Create your admin key, then define per-tier limits in code or DB seed.
- [ ] **CORS restricted.** `app.add_middleware(CORSMiddleware, allow_origins=["*"])` → change to explicit origins (`["https://your.app", "https://admin.your.domain"]`).
- [ ] **Request body size limit.** Add `max_request_size` middleware or nginx/client_max_body_size. Without it, a 1GB POST to `/v1/kb` OOMs the container.
- [ ] **Security headers.** Caddy snippet:
  ```caddy
  header {
    X-Content-Type-Options "nosniff"
    X-Frame-Options "DENY"
    Referrer-Policy "strict-origin-when-cross-origin"
    Permissions-Policy "geolocation=(), microphone=(), camera=()"
  }
  ```
- [ ] **API key rotation procedure documented.** How to revoke a compromised key, generate a replacement, and update clients — without downtime.

---

## Tier 2: Infrastructure (stability & durability)

- [ ] **PostgreSQL instead of SQLite.** SQLite is fine for single-node dev + up to ~100 concurrent users. Beyond that:
  ```yaml
  DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/phi_gateway
  ```
  Switch `aiosqlite` → `asyncpg` in `pyproject.toml` deps. Run `alembic upgrade head`.
- [ ] **Redis-backed rate limiting.** `rate_limiter.py` currently uses in-memory dicts — lost on restart, wrong with >1 worker. Swap to Redis:
  ```python
  # ratelimit/redis.py (or use slowapi + redis)
  import aioredis
  r = await aioredis.from_url("redis://...")
  count = await r.incr(f"rl:{key_id}:minute:{minute_bucket}")
  ```
- [ ] **Multiple uvicorn workers.** Single worker leaves CPU 75% idle. Bump to `--workers $(nproc)`:
  ```dockerfile
  CMD ["uvicorn", "phi_gateway.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
  ```
  **Caveat:** SQLite + multi-worker = `database is locked` errors. Only do multi-worker with PostgreSQL.
- [ ] **Graceful shutdown.** FastAPI lifespan already handles engine disposal. Verify:
  - SIGTERM → drain in-flight requests (default: 30s timeout)
  - SIGKILL → emergency (avoid in production)
- [ ] **Health check endpoint improved.** Current `/health` returns `{"status":"ok","version":"x"}`. Add DB connectivity check + provider key presence:
  ```python
  @app.get("/health")
  async def health(db: AsyncSession = Depends(get_db)):
      db_ok = await db.execute(select(1))
      return {"status": "ok" if db_ok else "degraded", "version": __version__}
  ```
  Use for Docker HEALTHCHECK + load balancer probes.

---

## Tier 3: Operations (runbooks & observability)

- [ ] **Structured logging.** Uvicorn defaults to plain-text line logs. Enable JSON for log aggregation (CloudWatch, Loki, DataDog):
  ```bash
  uvicorn ... --log-config log_config.json
  # or pipe through: pip install uvicorn-log-collector
  ```
- [ ] **OpenTelemetry tracing.** Instrument FastAPI middleware + LLM provider calls:
  - Request → provider call → response: trace end-to-end
  - Export to Jaeger, Grafana Tempo, or Honeycomb
  - Roadmap item: Q3 2026
- [ ] **Metrics endpoint** (`/metrics` in Prometheus format). Track:
  - Requests/s by endpoint + status code
  - LLM latency p50/p95/p99 (by provider)
  - Token usage rate (input/output)
  - Rate limit hits (429s by tier)
  - DB connection pool utilization
  ```bash
  pip install prometheus-fastapi-instrumentator
  ```
- [ ] **Alert rules defined.** What triggers a page vs. a ticket:
  | Signal | Severity | Action |
  |--------|----------|--------|
  | 5xx rate > 5% over 5 min | P1 | Wake up on-call |
  | Provider key exhausted / 401 | P2 | Rotate key in env, restart worker |
  | LLM p99 latency > 10s | P2 | Check provider status page |
  | Rate-limit 429s > 10% of requests | P3 | Scale up or adjust tier caps |
  | DB connection pool exhausted | P1 | Increase pool_size or scale DB |
- [ ] **Backup strategy:**
  - SQLite: `cp /app/data/phi.db /backup/phi-$(date +%F).db` (daily cron, keep 30 days)
  - PostgreSQL: `pg_dump` or WAL archiving
  - Caddy data (certs): `caddy_data` volume backup
- [ ] **Log retention policy.** Gateway logs rotate at 100MB, keep 14 days. FastAPI access logs → stdout → container logger.
- [ ] **Readiness probe.** K8s or Docker health check:
  ```yaml
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
  ```

---

## Tier 4: Resiliency (surviving failure)

- [ ] **Provider fallback chain.** If `anthropic/claude-sonnet-4.6` returns 5xx, retry with `openai/gpt-5.2`. Currently llm_proxy.py hard-fails on provider error. Add:
  ```python
  FALLBACK_CHAIN = [
      ("anthropic", "claude-sonnet-4.6"),
      ("openai", "gpt-5.2"),
      ("groq", "llama-3.3-70b"),
  ]
  ```
- [ ] **Connection pooling tuned.** SQLAlchemy defaults to 5 pool connections. For PostgreSQL:
  ```python
  engine = create_async_engine(
      settings.DATABASE_URL,
      pool_size=10,
      max_overflow=20,
      pool_pre_ping=True,
  )
  ```
- [ ] **Idempotent API key creation.** `POST /v1/keys` with idempotency key prevents dupes on retry.
- [ ] **Docker restart policy.** Already `restart: unless-stopped` in compose files. Add `--restart always` for systemd/gateway deployments.
- [ ] **Resource limits.** `mem_limit: 1g` in compose is a start. Add CPU limits:
  ```yaml
  deploy:
    resources:
      limits:
        cpus: "2.0"
        memory: 1G
  ```

---

## Tier 5: Testing & Release

- [ ] **Load test baseline.** `hey` or `locust` or `wrk` against `/v1/chat/completions`:
  ```bash
  hey -n 1000 -c 20 -H "Authorization: Bearer $KEY" \
    -m POST \
    -d '{"model":"groq/llama-3.3-70b","messages":[{"role":"user","content":"hi"}],"max_tokens":5}' \
    http://localhost:8000/v1/chat/completions
  ```
  Record: throughput (req/s), p50/p95/p99 latency, error rate.
- [ ] **Chaos tests:**
  - Kill the DB → gateway returns 503, not a crash
  - Revoke all provider keys → graceful 502 with clear message
  - `docker stop` the container → pending requests drain within timeout
- [ ] **Staging environment.** Mirror prod with fake provider keys or a mock LLM server.
- [ ] **GitHub Actions CI passes.** Current CI (ruff + pytest + Docker build) runs per push.
- [ ] **Semantic versioning.** `vMAJOR.MINOR.PATCH` on PyPI + git tags. Publish workflow triggers on `v*` tags.

---

## Tier 6: Documentation & Runbooks

- [ ] **One-page ops runbook** (OPS.md):
  ```markdown
  # Quick reference for the on-call engineer
  ## Restart: docker compose restart api
  ## Logs:   docker compose logs -f api
  ## Backup: docker compose exec api cp /app/data/phi.db /app/data/backups/
  ## Scale:  docker compose up -d --scale api=3   (requires PostgreSQL + Redis)
  ```
- [ ] **`.env.example` kept in sync** with actual config keys. Every deployable config key documented with its default and purpose.
- [ ] **CHANGELOG.md** — every version bump includes a human-readable diff. Automated via `git-cliff` or manual.

---

## Quick Wins (do this week)

Items from the checklist that cost <1 hour each:

| What | Why | Effort |
|------|-----|--------|
| CORS restrict to your domain | Security | 5 min |
| Add security headers in Caddy | Security | 5 min |
| Docker HEALTHCHECK | Orchestrator detects dead container | 5 min |
| Health check with DB probe | Load balancer accuracy | 10 min |
| Structured JSON logging | Log aggregation | 15 min |
| Backup cron (SQLite cp) | Data loss prevention | 10 min |
| Rate limit Redis (if you have Redis) | Correctness under multi-worker | 30 min |
| Load test baseline | Know your capacity before launch | 20 min |

---

**Related:** [CONTRIBUTING.md](CONTRIBUTING.md) — [DESIGN.md](DESIGN.md) — [LICENSE](LICENSE)
