# Technical Design

## Architecture Decisions

### ADR-001: API Key Authentication (Single-Tenant)

**Context**: The API is a closed feature serving a single frontend client.

**Decision**: Implement simple API key authentication via `X-API-Key` header.

**Rationale**:
- Single tenant = single API key
- No need for user management, sessions, or OAuth flows
- Simple to implement and validate
- Easy to rotate if compromised

**Consequences**:
- API key must be kept secret
- Key rotation requires frontend coordination
- Not suitable for multi-user scenarios (would require redesign)

---

### ADR-002: Per-API-Key Rate Limiting

**Context**: Need to protect against abuse and control LLM API costs.

**Decision**: Implement rate limiting tracked per API key using slowapi.

**Rationale**:
- Slowapi is built on limits, well-maintained
- Per-key tracking allows future multi-client support
- 60/min is conservative enough to prevent abuse
- Uses Redis-like in-memory storage (sufficient for single instance)

**Consequences**:
- In-memory storage doesn't persist across restarts
- For multi-instance deployment, would need Redis backend
- Legitimate bursts may be throttled

---

### ADR-003: Environment-Based Configuration

**Context**: Security settings vary between development and production.

**Decision**: Use pydantic-settings for configuration, load from `.env` file.

**Configuration Structure**:
```
API_KEY           - Required: The API key for authentication
CORS_ORIGINS      - Required: Comma-separated list of allowed origins
RATE_LIMIT_PER_MINUTE - Default: 60
ENVIRONMENT       - Default: development
```

**Rationale**:
- Type-safe configuration with validation
- Automatic environment variable loading
- Clear separation of concerns

---

### ADR-004: Full Async Architecture

**Context**: FastAPI is async-first; all operations should run on the asyncio event loop.

**Decision**: ALL I/O operations, middleware, and dependencies must be async.

**Rationale**:
- FastAPI runs on Starlette's async ASGI server
- Blocking operations block the entire event loop
- Async enables concurrent request handling
- LLM calls and tool execution will be async

**Consequences**:
- No blocking calls allowed (time.sleep, requests, sync DB drivers)
- All external calls must use async libraries (httpx, asyncpg)
- Middleware must use `async def` with `await call_next(request)`

**Implementation Requirements**:
1. All endpoints: `async def`
2. All dependencies: `async def` with proper yields
3. All middleware: `@app.middleware("http") async def`
4. Rate limiting: SlowAPIMiddleware (async-compatible)
5. Timeouts: Use `asyncio.wait_for()` - NOT signal-based timeouts
6. External calls: Use `httpx` (async) - NOT `requests` (sync)

---

## Patterns & Conventions

### Async Middleware Pattern

ALL middleware must be async:

```python
@app.middleware("http")
async def middleware_name(request: Request, call_next):
    # Pre-processing (async if I/O needed)
    response = await call_next(request)  # MUST await
    # Post-processing (async if I/O needed)
    return response
```

### Async Dependency Pattern

All dependencies with I/O must be async generators:

```python
async def get_api_key(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    settings: Settings = Depends(get_settings)
) -> str:
    # Async if key lookup involves I/O (e.g., database)
    # Sync is OK for simple comparison (in-memory)
    ...
```

### Async Timeout Pattern

Use `asyncio.wait_for` for timeouts - this is event-loop friendly:

```python
import asyncio

try:
    result = await asyncio.wait_for(
        some_async_operation(),
        timeout=60.0
    )
except asyncio.TimeoutError:
    raise HTTPException(504, "Request timeout")
```

**NEVER** use signal-based timeouts (they don't work with asyncio).

### Rate Limiting Pattern

SlowAPI works with async via middleware:

```python
from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware

limiter = Limiter(key_func=get_api_key_or_ip)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)  # Async-compatible

@router.post("/chat")
@limiter.limit("60/minute")
async def chat(request: Request, ...):  # Request param required
    ...
```

### Error Handling Pattern

```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log full details (sync logging is OK)
    logger.exception("Unhandled error")

    # Return safe message
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

### Settings Pattern

Settings loading can be sync (no I/O, just env parsing):

```python
@lru_cache
def get_settings() -> Settings:
    return Settings()  # Sync is OK - just parses env vars

SettingsDep = Annotated[Settings, Depends(get_settings)]
```

---

## Dependencies

### New Dependencies to Add

| Package | Version | Purpose | Async Support |
|---------|---------|---------|---------------|
| `slowapi` | >=0.1.9 | Rate limiting | Yes (via middleware) |
| `secure` | >=0.3 | Security headers | N/A (sync headers) |
| `pydantic-settings` | >=2.0 | Environment configuration | N/A |
| `httpx` | >=0.25 | Async HTTP client | **Yes (required for tools)** |

### Existing Dependencies (No Changes)

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | >=0.129.0 | Web framework (async) |
| `pydantic` | >=2.12.5 | Data validation |
| `langchain` | >=1.2.10 | LLM orchestration (async) |
| `langchain-openai` | >=1.1.10 | OpenAI integration (async) |

---

## Integration Points

### API → Configuration

- `src/api/dependencies.py` imports `Settings` from `src/config/`
- Settings provides API key, CORS origins, rate limits
- Settings loading is sync (env parsing only)

### API → Rate Limiting

- `src/api/main.py` initializes `Limiter` from slowapi
- `src/api/main.py` adds `SlowAPIMiddleware` (async)
- Endpoints use `@limiter.limit()` decorator
- Key function can be sync (no I/O)

### API → Security Headers

- `src/api/main.py` adds security headers middleware
- Headers are sync (no I/O needed)
- Uses `secure` package for header generation

### API → Future Tools (Async Required)

- Tools (weather, stock) must use async HTTP client (`httpx`)
- Tool calls will use `asyncio.gather()` for concurrent execution
- Pattern: `weather, stock = await asyncio.gather(get_weather(), get_stock())`

### Frontend → API

- Frontend sends `X-API-Key: <key>` header with every request
- Frontend origin must be in `CORS_ORIGINS` allowlist
- Frontend receives 401 on invalid/missing key
- Frontend receives 429 on rate limit exceeded

---

## Data Structures

### Settings Model

```
Settings:
  api_key: str (from API_KEY env)
  cors_origins: list[str] (from CORS_ORIGINS env, comma-separated)
  rate_limit_per_minute: int = 60
  environment: str = "development"
  debug: bool = False
  request_timeout_seconds: int = 60
  max_request_size_bytes: int = 1048576  # 1MB
```

### API Key Validation Response

```
Success: returns api_key string
Failure: raises HTTPException(401, "Invalid or missing API key")
```

### Rate Limit Headers (Automatic from SlowAPI)

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1708123456
Retry-After: 30  # On 429 response
```

### Security Headers (Minimal)

```
X-Content-Type-Options: nosniff
Strict-Transport-Security: max-age=31536000; includeSubDomains (production only)
```

---

## Security Controls Summary

| Control | Implementation | Location | Async |
|---------|---------------|----------|-------|
| Authentication | API Key via X-API-Key header | `dependencies.py` | Sync OK |
| Authorization | N/A (single-tenant) | - | - |
| Rate Limiting | SlowAPIMiddleware, 60/min | `main.py` | Yes |
| CORS | Allowlist from env | `main.py` | N/A |
| Input Validation | Pydantic with constraints | `chat.py` | N/A |
| Request Timeout | asyncio.wait_for, 60s | middleware | **Yes** |
| Request Size | Content-Length check | middleware | **Yes** |
| Security Headers | secure package | middleware | **Yes** |
| Error Sanitization | Generic messages | exception handler | **Yes** |
| Docs Protection | Disabled entirely | `main.py` | N/A |

---

## Async Request Flow

```
1. Request arrives (ASGI)
2. async CORS middleware checks origin
3. async Rate limiter middleware checks limit
4. async Security headers middleware adds headers
5. async Request size middleware checks Content-Length
6. async API key validated via Depends() (sync OK for comparison)
7. Pydantic validates input (sync OK)
8. async Endpoint handler executes
   └── If tools needed: asyncio.gather() for concurrent calls
9. Response returned with rate limit headers
10. async Error? → Generic message to client, details logged
```

---

## Async Best Practices Checklist

- [ ] All endpoint handlers use `async def`
- [ ] All middleware uses `@app.middleware("http")` with `async def`
- [ ] All `call_next(request)` calls are `await`ed
- [ ] Timeouts use `asyncio.wait_for()` NOT signals
- [ ] External HTTP calls use `httpx` (async) NOT `requests` (sync)
- [ ] Database operations would use async drivers (future)
- [ ] No blocking calls in async context (no `time.sleep`, `requests.get`)
- [ ] SlowAPIMiddleware is used (async-compatible)
- [ ] Exception handlers are `async def`

---

## Environment Variables Required

```
# Required
API_KEY=your-secret-api-key-here
CORS_ORIGINS=https://app.example.com,http://localhost:3000

# Optional (defaults shown)
RATE_LIMIT_PER_MINUTE=60
ENVIRONMENT=development
REQUEST_TIMEOUT_SECONDS=60
MAX_REQUEST_SIZE_BYTES=1048576
```
