# PhiGateway — Technical Implementation Plan

> Code audit findings and remediation plan. Each task is sized to be
> a single PR that can be reviewed independently.

## Overview

The codebase audit identified 9 issues across 3 severity levels.
This plan organizes them into 4 phases ordered by impact and risk.

```
Phase 1: Error handling consolidation     (HIGH impact, LOW risk)
Phase 2: MCP endpoint decomposition       (HIGH impact, MEDIUM risk)
Phase 3: LLM proxy cleanup                (MEDIUM impact, MEDIUM risk)
Phase 4: Operational hardening             (MEDIUM impact, LOW risk)
```

---

## Phase 1: Error Handling Consolidation

**Goal:** Eliminate 70 lines of copy-pasted exception handlers in `main.py`.

### Problem

`main.py:create_app()` contains 7 exception handlers that all do the
same thing with different status codes:

```python
# This exact pattern repeats 7 times:
request_id = getattr(request.state, "request_id", None)
return JSONResponse(
    status_code=N,
    content=ErrorDetail(detail=str(exc), id=request_id).model_dump(exclude_none=True),
)
```

Only `RateLimitExceededError` adds a `Retry-After` header. The other
6 are identical except for the status code number.

### Solution

**1.1 — Add `status_code` to `GatewayError` base class**

File: `src/phi_gateway/core/exceptions.py`

```python
class GatewayError(Exception):
    """Base exception for all domain errors."""

    status_code: int = 500

    @property
    def headers(self) -> dict[str, str] | None:
        """Override in subclasses to add response headers."""
        return None
```

Each subclass sets its own `status_code`:

| Exception | status_code | headers |
|-----------|-------------|---------|
| `NotFoundError` | 404 | - |
| `ConflictError` | 409 | - |
| `ValidationError` | 400 | - |
| `ExternalToolError` | 502 | - |
| `ExternalToolTimeoutError` | 504 | - |
| `RateLimitExceededError` | 429 | `{"Retry-After": ...}` |

`RateLimitExceededError` overrides `headers` property to return
`{"Retry-After": str(self.retry_after)}`.

**1.2 — Replace 7 handlers with 1 generic handler**

File: `src/phi_gateway/main.py`

```python
@app.exception_handler(GatewayError)
async def gateway_error_handler(request: Request, exc: GatewayError):
    """Map any GatewayError to its HTTP status code."""
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorDetail(detail=str(exc), id=request_id).model_dump(exclude_none=True),
        headers=exc.headers,
    )
```

Lines removed: ~65. Lines added: ~10.

**1.3 — Remove `FastAPIHTTPException` handler**

The `http_exception_handler` for `FastAPIHTTPException` is still
needed for framework-level errors (422 validation, etc.). Keep it.

### Verification

- All 111 tests must pass (no behavior change).
- Manually verify each exception type returns the correct status code.
- `ruff check` clean.

### PR size estimate

~80 lines removed, ~20 added. Single file change to exceptions.py +
main.py. Low risk: pure refactor, no behavior change.

---

## Phase 2: MCP Endpoint Decomposition

**Goal:** Break the 146-line `mcp_endpoint()` god function into 4
focused handlers.

### Problem

`api/mcp.py:mcp_endpoint()` handles 4 different JSON-RPC methods in
a single `if/elif/elif/elif/else` chain. Each branch is a completely
different feature. The function has 9 branches and 146 lines.

### Solution

**2.1 — Create dispatch table**

File: `src/phi_gateway/api/mcp.py`

```python
_METHOD_HANDLERS: dict[str, Callable] = {
    "tools/list": _handle_tools_list,
    "tools/call": _handle_tools_call,
    "resources/list": _handle_resources_list,
    "resources/read": _handle_resources_read,
}


@router.post("/mcp")
async def mcp_endpoint(
    body: JsonRpcRequest,
    api_key: ApiKey = Depends(get_api_key),
    db: AsyncSession = Depends(get_db),
):
    handler = _METHOD_HANDLERS.get(body.method)
    if handler is None:
        return _jsonrpc_error(body.id, -32601, f"Method '{body.method}' not supported")
    try:
        return await handler(body, db)
    except Exception as e:
        logger.exception("MCP error")
        return _jsonrpc_error(body.id, -32603, str(e))
```

**2.2 — Extract 4 handler functions**

Each becomes ~20-30 lines with a clear docstring:

- `_handle_tools_list(body, db)` — list tools from DB
- `_handle_tools_call(body, db)` — validate + proxy HTTP call
- `_handle_resources_list(body, db)` — list knowledge bases
- `_handle_resources_read(body, db)` — fetch documents for a KB

**2.3 — Add helper for JSON-RPC error responses**

```python
def _jsonrpc_error(request_id: str, code: int, message: str) -> dict:
    """Build a JSON-RPC 2.0 error response."""
    return {"jsonrpc": "2.0", "error": {"code": code, "message": message}, "id": request_id}
```

**2.4 — Fix `tools/call` query inefficiency**

Currently `tools/call` calls `list_tools(db)` and filters in Python.
Replace with a direct DB query:

```python
result = await db.execute(
    select(ToolDefinition).where(ToolDefinition.name == tool_name)
)
tool = result.scalar_one_or_none()
```

### Verification

- Existing MCP tests must pass.
- Add unit tests for each handler function in isolation.
- Test unknown method returns `-32601`.

### PR size estimate

~150 lines changed. Medium risk: restructuring control flow, but
each handler is isolated.

---

## Phase 3: LLM Proxy Cleanup

**Goal:** Reduce `route_chat()` from 119 lines/12 branches to ~40
lines. Cache provider clients.

### Problem

`core/llm_proxy.py:route_chat()` combines:
- Model parsing
- Client creation
- Request building (with per-provider branching)
- Tool translation
- Fallback loop
- Response translation

Also: `_get_client()` creates a new SDK client per request, wasting
connection pools.

### Solution

**3.1 — Cache provider clients at module level**

```python
_client_cache: dict[str, AsyncOpenAI | AsyncAnthropic | AsyncGroq] = {}

def _get_client(provider: str):
    if provider not in _client_cache:
        # ... create client
        _client_cache[provider] = client
    return _client_cache[provider]
```

Thread-safe because the clients are async and the dict is populated
once at first use (GIL protects the write).

**3.2 — Extract request builder**

```python
def _build_request_kwargs(
    provider: str,
    model_name: str,
    messages: list[dict],
    temperature: float,
    max_tokens: int | None,
    tools: list[dict] | None,
) -> dict:
    """Build provider-specific kwargs for chat.completions.create()."""
```

This absorbs the per-provider branching from `route_chat()`.
Returns a dict ready to unpack into `client.chat.completions.create(**kwargs)`.

**3.3 — Remove dead `stream` parameter from `route_chat()`**

The `stream` parameter is accepted but never used (streaming uses
`route_chat_stream()`). Remove it from the signature.

**3.4 — Simplify `route_chat()` to just the fallback loop**

After extracting the builder, `route_chat()` becomes:

```python
async def route_chat(model, messages, temperature=0.7, max_tokens=None, tools=None):
    models_to_try = [model] + _get_fallbacks(model)
    last_error = None
    for candidate in models_to_try:
        try:
            provider, model_name = _parse_model(candidate)
            client = _get_client(provider)
            kwargs = _build_request_kwargs(provider, model_name, messages, temperature, max_tokens, tools)
            response = await client.chat.completions.create(**kwargs)
            return _translate_response(response, candidate, provider)
        except (...) as exc:
            last_error = exc
            logger.warning(...)
    raise last_error
```

~25 lines. Down from 119.

### Verification

- All chat-related tests must pass.
- Verify fallback behavior still works (mock provider failures).
- Verify streaming is unaffected.

### PR size estimate

~200 lines changed. Medium risk: touching the core routing logic.

---

## Phase 4: Operational Hardening

**Goal:** Fix small issues that affect production reliability.

**4.1 — Sanitize error messages**

`_get_client()` currently says `Set OPENAI_API_KEY in your .env file`
to API consumers. This leaks internal env var names.

Fix: Log the detailed message server-side, return a generic message
to the client:

```python
logger.error("Provider '%s' not configured: missing %s", provider, env_key)
raise RuntimeError(f"Provider '{provider}' is not available")
```

**4.2 — Add `tools/call` parameter validation**

MCP `tools/call` currently passes `arguments` directly to the tool
endpoint without validating against the tool's JSON Schema.

Fix: Add basic validation using `jsonschema` library (already a
transitive dependency via FastAPI/pydantic):

```python
from jsonschema import validate, ValidationError
validate(instance=arguments, schema=tool.json_schema)
```

**4.3 — Remove `tools/call` all-tools fetch**

Replace `list_tools(db)` + Python filter with direct DB query
(addressed in Phase 2.4).

### Verification

- Existing tests pass.
- Add test for error message sanitization.
- Add test for invalid tool parameter rejection.

### PR size estimate

~50 lines changed. Low risk.

---

## Phase Summary

| Phase | Files Changed | Lines +/- | Risk | Dependencies |
|-------|--------------|-----------|------|-------------|
| 1. Error handling | 2 (exceptions.py, main.py) | -65/+20 | Low | None |
| 2. MCP decomposition | 1 (mcp.py) | +80/-60 | Medium | None |
| 3. LLM proxy cleanup | 1 (llm_proxy.py) | +100/-80 | Medium | None |
| 4. Operational hardening | 2-3 files | +30/-20 | Low | Phase 2 |

Phases 1-3 are independent and can be done in parallel.
Phase 4 depends on Phase 2 for the MCP query fix.

---

## Not In Scope

These were considered but deferred:

- **Consolidating shallow modules** (`api/router.py`, `api/models.py`,
  `api/usage.py`): These are fine as-is. Thin modules are not a
  problem when they're stable and rarely touched.

- **Moving middleware out of `create_app()`**: The closures work
  correctly. The function is long but not complex. Refactoring
  middleware into separate modules adds indirection without clear
  benefit.

- **Switching to PostgreSQL**: Tracked separately in issue #5.
  Not a code quality issue.

- **Adding OpenTelemetry**: Tracked in issue #7. Separate concern.
