# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] — 2026-05-18

### Added

- Connection pooling configuration for SQLAlchemy (`pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`)
- Structured JSON logging via `phi_gateway.log_config` — outputs JSON lines with `timestamp`, `level`, `logger`, `message`, and extra fields
- Uvicorn access logger overridden to JSON format with request context (`request_id`, `method`, `path`, `status_code`, `duration_ms`)
- `X-Request-ID` middleware — correlates logs across requests, accepts incoming header or auto-generates UUID
- `OPS.md` — operations runbook with restart, logs, backup, health check, scale, upgrade procedures
- `scripts/backup-db.sh` — automated SQLite backup with 30-day retention and syslog logging
- `CHANGELOG.md` — this file
- Security headers middleware (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`)
- Request body size limit middleware (configurable via `MAX_REQUEST_BODY_SIZE`)
- Health check endpoint enhanced with database connectivity probe and uptime metric
- CORS origin config — `ALLOWED_ORIGINS` environment variable with comma-separated support

### Changed

- Database engine initialization now uses explicit pool parameters for production readiness
- Application logging switched from plain-text to structured JSON format
- Uvicorn access logs emit structured JSON for log aggregator compatibility

### Fixed

- Database connection reuse improved with `pool_pre_ping=True` to detect stale connections

## [0.1.0] — 2026-04-22

### Added

- Initial PyPI release of `phi-gateway`
- FastAPI-based LLM proxy with OpenAI, Anthropic, Groq, and OpenRouter support
- MCP (Model Context Protocol) tool registry — register and invoke tools via API
- RAG knowledge base — upload documents, semantic search with embeddings
- Agent memory — persistent conversation memory per session
- API key authentication with tier-based rate limiting
- Usage tracking and cost management per API key
- Built-in SQLite database (single-node deployment)
- Docker Compose setup for easy self-hosting
- Scalar API documentation UI at `/docs`
- CI/CD pipeline via GitHub Actions (ruff, pytest, Docker build)
- PyPI publish workflow triggered on version tags
