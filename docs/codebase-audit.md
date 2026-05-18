# Phi-Gateway Codebase Audit

**Date:** 2026-05-18
**Scope:** `src/phi_gateway/` (all Python), `tests/` (all test files)
**Method:** Manual line-by-line review of all 50 Python source files

---

## Summary

| Category | Count | Severity |
|---|---|---|
| Dead code (unused definitions) | 3 | Medium |
| Shallow modules | 2 | Low |
| Redundant tests | 3 | Medium |
| Pricing data duplication | 1 | High |
| Dead logic (unreachable code) | 1 | Medium |
| Missing error handling | 3 | Medium |
| Performance issue | 1 | Medium |
| Inconsistent patterns | 3 | Low |
| Schema in wrong location | 1 | Low |

---

## 1. Dead Code — Unused Definitions

### 1.1 `JsonRpcResponse` schema never used

**File:** `src/phi_gateway/schemas/mcp.py:13-17`

The `JsonRpcResponse` Pydantic model is defined but never imported or used
anywhere in the codebase. The MCP endpoint in `api/mcp.py` returns raw dicts
instead of using this schema.

```python
# This class is never imported anywhere
class JsonRpcResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: Any = None
    error: Optional[dict] = None
    id: str | int | None = None
```

**Fix:** Either use it as the response_model in the MCP endpoint, or remove it.

### 1.2 `get_rate_limit_headers()` never called in production code

**File:** `src/phi_gateway/core/rate_limiter.py:64-77`

This function is defined and tested but never called from any route handler
or middleware. Rate limit headers (`X-RateLimit-Limit-Min`, etc.) are never
sent to clients. The tests prove it works, but no production code wires it in.

**Fix:** Add rate limit headers to responses in `dependencies.py` or a middleware.

### 1.3 `EmbeddingRequest` schema defined in wrong place

**File:** `src/phi_gateway/api/embeddings.py:11-14`

Every other request/response schema lives in `schemas/` (chat, keys, knowledge,
memory, tools, usage, mcp). `EmbeddingRequest` is the only one defined inline
in an API route file.

```python
class EmbeddingRequest(BaseModel):
    model: str
    input: str | list[str]
```

**Fix:** Move to `src/phi_gateway/schemas/embeddings.py` for consistency.

---

## 2. Dead Logic — Unreachable Per-Model Context Limits

### 2.1 `CONTEXT_LIMITS` per-model entries are never used

**File:** `src/phi_gateway/services/memory_service.py:18-24, 175`

The `CONTEXT_LIMITS` dict defines per-model limits (gpt-5-nano: 400K,
claude-haiku-4.5: 200K, etc.), but `_trim_if_needed` always reads the
`"default"` key:

```python
limit = CONTEXT_LIMITS.get("default", 128_000)  # line 175
```

The function signature doesn't accept a model parameter, so there's no way
to look up a specific model. The per-model entries are dead data.

**Fix:** Either pass the model name into `_trim_if_needed` and do a real
lookup, or simplify `CONTEXT_LIMITS` to a single constant.

---

## 3. Pricing Data Duplication (High Severity)

### 3.1 Model pricing defined in two separate places

**Files:**
- `src/phi_gateway/core/cost_tracker.py:6-26` — `COST_PER_1M_TOKENS` dict
- `src/phi_gateway/core/llm_proxy.py:57-79` — `KNOWN_MODELS` list with `pricing` strings

Both maintain the same pricing information in different formats:

```python
# cost_tracker.py
"gpt-5-nano": (0.05, 0.40),      # tuple of (input, output) per 1M tokens

# llm_proxy.py
{"id": "gpt-5-nano", "pricing": "$0.05/$0.40", ...}  # human-readable string
```

These must be kept in sync manually. If one is updated and the other isn't,
cost calculations will disagree with the models listing.

**Fix:** Define pricing once (likely in `cost_tracker.py` as the source of
truth) and derive the display string programmatically, or import from a
shared config.

---

## 4. Shallow Modules

### 4.1 `api/models.py` — Pure pass-through (11 lines)

**File:** `src/phi_gateway/api/models.py`

The entire module is:
```python
router = APIRouter(prefix="/v1", tags=["Models"])

@router.get("/models")
async def get_models():
    return list_models()
```

This is a single endpoint that calls `list_models()` and returns the result.
Zero business logic, zero transformation.

**Fix:** Consider merging into `api/chat.py` (which also uses prefix="/v1"
and handles LLM-related endpoints) or into `api/router.py` directly.

### 4.2 `models/base.py` — Single empty class (5 lines)

**File:** `src/phi_gateway/models/base.py`

```python
class Base(DeclarativeBase):
    pass
```

This is standard SQLAlchemy pattern and is acceptable — every model imports
from here. Not a real problem, just noting it.

---

## 5. Redundant Tests

### 5.1 `test_security_headers_present` is a subset of `test_security_headers_on_root`

**File:** `tests/integration/test_security_headers.py:8-13, 25-31`

Both test `GET /` and check the same security headers. `test_security_headers_present`
checks `X-Content-Type-Options == "nosniff"` and `X-Frame-Options == "DENY"` and
`Referrer-Policy in headers`. `test_security_headers_on_root` checks the exact same
things plus verifies the exact value of `Referrer-Policy`.

`test_security_headers_present` adds zero coverage beyond what
`test_security_headers_on_root` already provides.

**Fix:** Remove `test_security_headers_present` — it's fully subsumed.

### 5.2 `test_health_returns_200` is redundant

**File:** `tests/integration/test_health.py:10-13`

`test_health_status_ok` (line 28-33) already checks that `GET /health` returns 200
AND verifies the body fields. `test_health_returns_200` only checks status code 200.

**Fix:** Remove `test_health_returns_200` — it's subsumed by `test_health_status_ok`.

### 5.3 Dashboard tests are all xfail — effectively dead tests

**File:** `tests/integration/test_dashboard.py`

All 6 tests are marked `@pytest.mark.xfail` with the same reason. They provide
zero regression coverage. They document that the dashboard exists but never
verify anything passes.

**Note:** This is acceptable if the Jinja2 issue is genuinely temporary, but
if it's been xfail for a long time, consider removing or fixing them.

---

## 6. Missing Error Handling

### 6.1 MCP `tools/call` doesn't handle tool auth

**File:** `src/phi_gateway/api/mcp.py:65-71`

The MCP `tools/call` handler fires an HTTP request to `tool.endpoint` but
completely ignores `tool.auth_type`. Compare with `tool_service.py` which
at least validates params. The MCP handler sends no auth headers to the
external tool, regardless of `auth_type`.

### 6.2 MCP `tools/call` uses generic error handling

**File:** `src/phi_gateway/api/mcp.py:149-155`

The outer `except Exception` catches everything, including `httpx.TimeoutException`
and `httpx.ConnectError`. Compare with `tool_service.py` which properly maps:
- `httpx.TimeoutException` → 504
- `httpx.HTTPStatusError` → 502
- `httpx.RequestError` → 502

The MCP endpoint returns error code `-32603` for all failures, losing the
specific error type.

### 6.3 Health check swallows DB errors silently

**File:** `src/phi_gateway/main.py:141-144`

```python
try:
    await db.execute(text("SELECT 1"))
except Exception:
    db_status = "degraded"
```

No logging of the actual exception. If the DB is down, you'll see "degraded"
in the response but nothing in the logs to diagnose why.

---

## 7. Performance Issue

### 7.1 Rate limiter uses O(n) list.pop(0)

**File:** `src/phi_gateway/core/rate_limiter.py:20-24`

```python
def _prune(bucket: list[float], cutoff: float) -> list[float]:
    while bucket and bucket[0] < cutoff:
        bucket.pop(0)  # O(n) for each pop
    return bucket
```

`list.pop(0)` is O(n) because it shifts all remaining elements. For a key
with high request volume, this runs on every request. Using
`collections.deque` with `popleft()` would make this O(1).

**Fix:** Change `_minute_buckets` and `_day_buckets` to use `deque` and
replace `pop(0)` with `popleft()`.

---

## 8. Inconsistent Patterns

### 8.1 Type hint style: `Optional[T]` vs `T | None`

The codebase mixes PEP 604 union syntax (`str | None`) with the older
`Optional[str]` from typing:

| File | Style |
|---|---|
| `api/memory.py`, `api/mcp.py`, `services/llm_service.py` | `T \| None` |
| `api/usage.py`, `schemas/keys.py`, `schemas/chat.py`, `schemas/memory.py`, `schemas/tools.py`, `schemas/mcp.py` | `Optional[T]` |

Since the project targets Python 3.10+ (uses `str | None` in many places),
the `Optional` imports are unnecessary.

### 8.2 Inconsistent route prefix patterns

| Router | Prefix |
|---|---|
| `chat.py`, `models.py`, `embeddings.py`, `usage.py` | `/v1` |
| `keys.py` | `/v1/keys` |
| `knowledge.py` | `/v1/kb` |
| `memory.py` | `/v1/memory` |
| `tools.py` | `/v1/tools` |
| `mcp.py` | (none) |
| `dashboard.py` | (none) |

The `/v1` prefix routers put versioning in the prefix, while others put the
full resource path. This is a style choice, not a bug, but it means the
version prefix is applied inconsistently.

### 8.3 `_get_client()` creates a new client on every call

**File:** `src/phi_gateway/core/llm_proxy.py:30-52`

Every call to `route_chat()` or `route_chat_stream()` creates a new
`AsyncOpenAI`/`AsyncAnthropic`/`AsyncGroq` client instance. These clients
maintain their own connection pools. Creating them per-request wastes
resources and prevents connection reuse.

**Fix:** Cache clients at module level (they're stateless except for config).

---

## 9. Files That Are Clean

These modules have no significant issues:

- `config.py` — Clean, minimal
- `database.py` — Standard pattern (pool_size ignored by SQLite, but harmless)
- `log_config.py` — Well-structured
- `dependencies.py` — Solid auth + rate limiting
- `core/security.py` — Clean key generation/verification
- `core/cost_tracker.py` — Clean (except duplication issue noted above)
- `core/embedding.py` — Clean, appropriate error handling
- `services/kb_service.py` — Good ownership checks, proper fallback
- `services/tool_service.py` — Good error handling, proper HTTP status mapping
- `services/llm_service.py` — Good logging, proper error propagation
- `models/*` — All clean, standard SQLAlchemy
- `tests/unit/test_rate_limiter.py` — Thorough
- `tests/unit/test_llm_proxy_fallback.py` — Excellent fallback testing
- `tests/integration/test_kb.py` — Good end-to-end coverage

---

## Priority Fixes

1. **High:** Consolidate pricing data (`cost_tracker.py` + `llm_proxy.py`)
2. **Medium:** Remove unused `JsonRpcResponse` schema
3. **Medium:** Wire `get_rate_limit_headers()` into responses or remove it
4. **Medium:** Fix `CONTEXT_LIMITS` dead per-model entries
5. **Medium:** Remove redundant tests (security_headers, health)
6. **Medium:** Fix rate limiter O(n) pop(0) → deque
7. **Low:** Move `EmbeddingRequest` to `schemas/`
8. **Low:** Standardize type hints to `T | None`
9. **Low:** Cache LLM clients instead of creating per-request
