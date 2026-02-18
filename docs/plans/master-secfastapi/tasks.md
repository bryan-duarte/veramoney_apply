# Implementation Tasks

## Task Breakdown

### Configuration Layer

- [x] Create `src/config/__init__.py` with Settings class using pydantic-settings
- [x] Define required fields: `api_key: str`, `cors_origins: list[str]`
- [x] Define optional fields: `rate_limit_per_minute: int = 60`, `environment: str = "development"`
- [x] Add validator to parse comma-separated CORS origins from env
- [x] Update `.env.example` with all required variables

### Dependencies Update

- [x] Add `slowapi>=0.1.9` to pyproject.toml (rate limiting)
- [x] Add `secure>=0.3` to pyproject.toml (security headers)
- [x] Add `pydantic-settings>=2.0` to pyproject.toml (env config) - Already present
- [x] Add `httpx>=0.25` to pyproject.toml (async HTTP client for future tools)
- [x] Run `uv sync` to install dependencies

### API Main Module (`src/api/main.py`)

- [x] Import Settings from `src.config`
- [x] Initialize slowapi Limiter with API key as key function
- [x] Add `app.state.limiter = limiter`
- [x] Add SlowAPIMiddleware (async-compatible)
- [x] Replace wildcard CORS with allowlist from settings
- [x] Restrict CORS methods to `["GET", "POST"]`
- [x] Restrict CORS headers to `["Content-Type", "X-API-Key"]`
- [x] Add async security headers middleware (X-Content-Type-Options, HSTS in prod)
- [x] Disable /docs and /redoc endpoints (set to None)
- [x] Add global async exception handler for sanitized errors
- [x] Add logging import and logger setup
- [x] Register exception handler for RateLimitExceeded

### API Dependencies Module (`src/api/dependencies.py`)

- [x] Remove placeholder Settings class
- [x] Import Settings from `src.config`
- [x] Update `get_settings()` to return `Settings()` from config
- [x] Create sync `get_api_key()` dependency function
- [x] Validate X-API-Key header against settings.api_key
- [x] Raise HTTPException(401) on invalid/missing key
- [x] Create `APIKeyDep = Annotated[str, Depends(get_api_key)]` type alias

### Chat Endpoint (`src/api/endpoints/chat.py`)

- [x] Add `request: Request` parameter (required by slowapi)
- [x] Add `@limiter.limit("60/minute")` decorator - Using global default limit
- [x] Add `api_key: APIKeyDep` parameter for authentication
- [x] Add `min_length=1` to message field in ChatRequest
- [x] Add `max_length=32000` to message field in ChatRequest
- [x] Add UUID format validator to session_id field
- [x] Update error handling to use sanitized messages
- [x] Add logging for security events (auth failures, validation errors) - Handled by global exception handler

### Git Ignore

- [x] Add `.env` to .gitignore - Already present
- [x] Add `*.pem`, `*.key` patterns to .gitignore

### Verification

- [x] Request without X-API-Key returns 401
- [x] Request with wrong X-API-Key returns 401
- [x] Request with correct X-API-Key succeeds
- [x] Empty message returns 422 validation error
- [x] Message > 32000 chars returns 422 validation error
- [x] Invalid session_id format returns 422 validation error
- [x] /docs returns 404 (disabled)
- [x] /redoc returns 404 (disabled)
- [x] X-Content-Type-Options: nosniff header present
- [x] /health endpoint works without API key

## Dependencies Between Tasks

```
Configuration Layer ─────┐
                         ├──→ Dependencies Module ──→ Chat Endpoint
Dependencies Update ─────┘
         │
         └──→ API Main Module (depends on config)
```

## Async Requirements Checklist

All implementations must follow async best practices:

- [x] All endpoint handlers use `async def`
- [x] All middleware uses `@app.middleware("http")` with `async def`
- [x] All `call_next(request)` calls are `await`ed
- [x] Exception handlers are `async def`
- [x] API key dependency is `def` (sync - no I/O needed)
- [x] Settings loading is sync (env parsing only)
- [x] No blocking calls in async context

## Estimated Effort

| Area | Tasks | Complexity |
|------|-------|------------|
| Configuration Layer | 5 | Low |
| Dependencies Update | 5 | Low |
| API Main Module | 12 | Medium |
| Dependencies Module | 7 | Medium |
| Chat Endpoint | 9 | Medium |
| Git Ignore | 2 | Low |
| Verification | 11 | Medium |

**Total: 51 tasks completed**

## Changes from Original Plan

### Removed
- ~~Request timeout middleware~~ - User decided not to implement
- ~~Request size limit middleware~~ - Using Pydantic validation only

### Added
- httpx>=0.25 dependency for async HTTP client
- Explicit async requirements checklist
- Rate limit key function uses API key (not IP)
- Health endpoint explicitly public (no auth, no rate limit)

### Modified
- API key dependency is sync (not async) - simple comparison
- CORS headers restricted to Content-Type and X-API-Key
- Used computed_field for cors_origins to handle comma-separated parsing (pydantic-settings 2.x compatibility)

## Implementation Notes

### Deviations from Plan

1. **CORS Origins Parsing**: Instead of using `@field_validator`, used `@computed_field` with a string backing field (`cors_origins_str`) because pydantic-settings 2.x attempts JSON parsing for `list[str]` types before validators run. This approach is cleaner and avoids JSON parsing issues.

2. **Rate Limiting**: Used global default limits in the Limiter constructor instead of per-endpoint decorators. This is simpler and achieves the same result.

3. **No Nested Functions**: Per the codebase_changes skill, extracted middleware, exception handlers, and health check to module-level functions instead of defining them inside `create_app()`.

4. **openapi_url=None**: Also disabled the OpenAPI JSON endpoint (not just docs and redoc) for complete documentation closure.
