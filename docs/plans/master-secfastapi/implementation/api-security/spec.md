# API Security Implementation

## Overview

This module implements the core security layer for the FastAPI application, including API key authentication, rate limiting, CORS hardening, and security headers. All operations follow async best practices.

## Files to Modify/Create

| File | Action | Purpose |
|------|--------|---------|
| `pyproject.toml` | Modify | Add security dependencies |
| `src/config/__init__.py` | Create | Settings class with security config |
| `src/api/main.py` | Modify | Add middleware, disable docs, exception handler |
| `src/api/dependencies.py` | Modify | Add API key validation |
| `src/api/endpoints/chat.py` | Modify | Add auth, rate limiting, validation |
| `.env.example` | Modify | Document security variables |
| `.gitignore` | Modify | Exclude .env |

## Implementation Guidelines

### 1. Configuration Layer (`src/config/__init__.py`)

Create a pydantic-settings based configuration class:

**Guidelines:**
- Inherit from `BaseSettings` (from pydantic_settings)
- Import: `from pydantic_settings import BaseSettings`
- Import: `from pydantic import field_validator`
- Define `api_key: str` as required field
- Define `cors_origins: list[str]` with validator to parse comma-separated env
- Define `rate_limit_per_minute: int = 60`
- Define `environment: str = "development"`
- Use `model_config = SettingsConfigDict(env_file=".env")` for config

**Async Note:** Settings loading is SYNC (just parses environment variables, no I/O)

### 2. Dependencies Update (`pyproject.toml`)

Add security dependencies:

**Packages to add:**
- `slowapi>=0.1.9` - Rate limiting (async-compatible via middleware)
- `secure>=0.3` - Security headers (sync headers, no async needed)
- `pydantic-settings>=2.0` - Environment configuration
- `httpx>=0.25` - Async HTTP client (for future tools)

**Command:** `uv add slowapi secure pydantic-settings httpx`

### 3. API Main Module (`src/api/main.py`)

**Changes required:**

1. **Import security components:**
   - Import `Limiter` from slowapi
   - Import `SlowAPIMiddleware` from slowapi.middleware
   - Import `SecureHeaders` from secure (or manual headers)
   - Import `Settings` from src.config
   - Import `logging` and create logger
   - Import `RateLimitExceeded` from slowapi.errors

2. **Initialize rate limiter:**
   - Create key function that extracts API key from request
   - Create `limiter = Limiter(key_func=get_rate_limit_key)`
   - Add `app.state.limiter = limiter`
   - Add `SlowAPIMiddleware(app)` (this is ASYNC-COMPATIBLE)

3. **Fix CORS configuration:**
   - Replace `allow_origins=["*"]` with `allow_origins=settings.cors_origins`
   - Keep `allow_credentials=True`
   - Restrict methods to `["GET", "POST"]`
   - Restrict headers to `["Content-Type", "X-API-Key"]`

4. **Add async security headers middleware:**
   ```python
   @app.middleware("http")
   async def add_security_headers(request: Request, call_next):
       response = await call_next(request)  # MUST await
       response.headers["X-Content-Type-Options"] = "nosniff"
       if settings.environment == "production":
           response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
       return response
   ```

5. **Disable documentation:**
   - Set `docs_url=None` in FastAPI constructor
   - Set `redoc_url=None` in FastAPI constructor

6. **Add global async exception handler:**
   ```python
   @app.exception_handler(Exception)
   async def global_exception_handler(request: Request, exc: Exception):
       logger.exception(f"Unhandled error: {exc}")  # Full details in log
       return JSONResponse(
           status_code=500,
           content={"detail": "Internal server error"}  # Generic message
       )
   ```

7. **Add rate limit exception handler:**
   - Import `_rate_limit_exceeded_handler` from slowapi or create custom
   - Register with `@app.exception_handler(RateLimitExceeded)`

8. **Health endpoint (PUBLIC - no auth, no rate limit):**
   - Keep `/health` endpoint outside protected routes
   - No `@limiter.limit` decorator
   - No `APIKeyDep` dependency

### 4. Dependencies Module (`src/api/dependencies.py`)

**Changes required:**

1. **Remove placeholder Settings class**

2. **Import from config:**
   - Import `Settings` from `src.config`

3. **Update get_settings:**
   - Keep sync: `def get_settings() -> Settings`
   - Return `Settings()` (pydantic-settings auto-loads from env)

4. **Create API key dependency (SYNC - simple comparison):**
   ```python
   def get_api_key(
       x_api_key: str | None = Header(None, alias="X-API-Key"),
       settings: Settings = Depends(get_settings)
   ) -> str:
       if not x_api_key:
           raise HTTPException(401, "Invalid or missing API key")
       if x_api_key != settings.api_key:
           raise HTTPException(401, "Invalid or missing API key")
       return x_api_key
   ```

5. **Create type alias:**
   - `APIKeyDep = Annotated[str, Depends(get_api_key)]`

### 5. Chat Endpoint (`src/api/endpoints/chat.py`)

**Changes required:**

1. **Add authentication:**
   - Add `api_key: APIKeyDep` parameter to endpoint

2. **Add rate limiting:**
   - Import limiter from main or use app.state.limiter
   - Add `@limiter.limit("60/minute")` decorator
   - Add `request: Request` parameter (REQUIRED by slowapi)

3. **Update ChatRequest validation:**
   - Add `min_length=1` to message field
   - Add `max_length=32000` to message field
   - Add UUID validator:
     ```python
     @field_validator('session_id')
     @classmethod
     def validate_session_id(cls, v):
         if v is not None:
             import uuid
             try:
                 uuid.UUID(v)
             except ValueError:
                 raise ValueError('session_id must be a valid UUID')
         return v
     ```

4. **Update error handling:**
   - Log security events (auth failures)
   - Return generic error messages
   - Never include stack traces

5. **Endpoint signature:**
   ```python
   @router.post("")
   @limiter.limit("60/minute")
   async def chat(
       request: Request,  # Required for slowapi
       api_key: APIKeyDep,  # Authentication
       chat_request: ChatRequest  # Validated input
   ) -> ChatResponse:
   ```

### 6. Environment File (`.env.example`)

Document required variables:

```
# Required - API Authentication
API_KEY=your-secret-api-key-here

# Required - CORS allowed origins (comma-separated)
CORS_ORIGINS=https://your-frontend.com,http://localhost:3000

# Optional (defaults shown)
RATE_LIMIT_PER_MINUTE=60
ENVIRONMENT=development
```

### 7. Git Ignore (`.gitignore`)

Add entries:
```
# Environment files with secrets
.env
.env.local
.env.*.local

# Secrets
*.pem
*.key
secrets/
```

## Dependencies

**This module depends on:**
- `src/config/` - For Settings (sync loading)

**This module is depended on by:**
- `src/api/endpoints/chat.py` - For authentication

## Integration Notes

### SlowAPI Integration (ASYNC)

- SlowAPIMiddleware is async-compatible
- Decorator `@limiter.limit()` works with async endpoints
- Request parameter MUST be first parameter in endpoint
- Key function receives Starlette Request object

### Secure Headers Integration (SYNC)

- Headers are set synchronously (no I/O)
- Use in async middleware via `response.headers[...]`
- Minimal headers: X-Content-Type-Options, HSTS (prod only)

### Pydantic Settings Integration (SYNC)

- Settings auto-load from `.env` file
- Use `@lru_cache` to avoid re-parsing
- Validation happens at startup (fail fast)

### Async Architecture Notes

**What is ASYNC:**
- All middleware (`@app.middleware("http") async def`)
- All endpoint handlers (`async def chat(...)`)
- All exception handlers (`async def handler(...)`)
- SlowAPIMiddleware internals

**What is SYNC (OK in async context):**
- Settings loading (env parsing, no I/O)
- API key validation (string comparison, no I/O)
- Pydantic validation (in-memory, no I/O)
- Logging calls (thread-safe)

**What MUST be ASYNC when added:**
- HTTP client calls (use httpx, not requests)
- Database operations (use asyncpg, async sessions)
- File I/O (use aiofiles)
- External API calls (weather, stock tools)

## Testing Checklist

After implementation, verify:

- [ ] Request without X-API-Key returns 401
- [ ] Request with wrong X-API-Key returns 401
- [ ] Request with correct X-API-Key succeeds
- [ ] Rate limit returns 429 after 60 requests (check X-RateLimit-* headers)
- [ ] Request from non-allowlisted origin is blocked (CORS error)
- [ ] Empty message returns 422 validation error
- [ ] Message > 32000 chars returns 422 validation error
- [ ] Invalid session_id format returns 422 validation error
- [ ] /docs returns 404 (disabled)
- [ ] /redoc returns 404 (disabled)
- [ ] Error responses don't include stack traces
- [ ] X-Content-Type-Options: nosniff header present
- [ ] /health endpoint works without API key
- [ ] Rate limit headers present (X-RateLimit-Limit, X-RateLimit-Remaining)

## Rate Limiting Key Function

The key function determines how rate limits are tracked:

```python
def get_rate_limit_key(request: Request) -> str:
    """Get API key from request for rate limiting."""
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"apikey:{api_key}"
    # Fallback to IP for unauthenticated requests
    return f"ip:{get_remote_address(request)}"
```

This allows:
- Per-API-key rate limiting for authenticated requests
- Per-IP fallback for unauthenticated requests (before they get 401)
