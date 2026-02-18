# Implementation Tasks

## Task Breakdown

### Configuration Layer

- [ ] Create `src/config/__init__.py` with Settings class using pydantic-settings
- [ ] Define required fields: `api_key: str`, `cors_origins: list[str]`
- [ ] Define optional fields: `rate_limit_per_minute: int = 60`, `environment: str = "development"`
- [ ] Add validator to parse comma-separated CORS origins from env
- [ ] Update `.env.example` with all required variables

### Dependencies Update

- [ ] Add `slowapi>=0.1.9` to pyproject.toml (rate limiting)
- [ ] Add `secure>=0.3` to pyproject.toml (security headers)
- [ ] Add `pydantic-settings>=2.0` to pyproject.toml (env config)
- [ ] Add `httpx>=0.25` to pyproject.toml (async HTTP client for future tools)
- [ ] Run `uv sync` to install dependencies

### API Main Module (`src/api/main.py`)

- [ ] Import Settings from `src.config`
- [ ] Initialize slowapi Limiter with API key as key function
- [ ] Add `app.state.limiter = limiter`
- [ ] Add SlowAPIMiddleware (async-compatible)
- [ ] Replace wildcard CORS with allowlist from settings
- [ ] Restrict CORS methods to `["GET", "POST"]`
- [ ] Restrict CORS headers to `["Content-Type", "X-API-Key"]`
- [ ] Add async security headers middleware (X-Content-Type-Options, HSTS in prod)
- [ ] Disable /docs and /redoc endpoints (set to None)
- [ ] Add global async exception handler for sanitized errors
- [ ] Add logging import and logger setup
- [ ] Register exception handler for RateLimitExceeded

### API Dependencies Module (`src/api/dependencies.py`)

- [ ] Remove placeholder Settings class
- [ ] Import Settings from `src.config`
- [ ] Update `get_settings()` to return `Settings()` from config
- [ ] Create sync `get_api_key()` dependency function
- [ ] Validate X-API-Key header against settings.api_key
- [ ] Raise HTTPException(401) on invalid/missing key
- [ ] Create `APIKeyDep = Annotated[str, Depends(get_api_key)]` type alias

### Chat Endpoint (`src/api/endpoints/chat.py`)

- [ ] Add `request: Request` parameter (required by slowapi)
- [ ] Add `@limiter.limit("60/minute")` decorator
- [ ] Add `api_key: APIKeyDep` parameter for authentication
- [ ] Add `min_length=1` to message field in ChatRequest
- [ ] Add `max_length=32000` to message field in ChatRequest
- [ ] Add UUID format validator to session_id field
- [ ] Update error handling to use sanitized messages
- [ ] Add logging for security events (auth failures, validation errors)

### Git Ignore

- [ ] Add `.env` to .gitignore
- [ ] Add `*.pem`, `*.key` patterns to .gitignore


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

- [ ] All endpoint handlers use `async def`
- [ ] All middleware uses `@app.middleware("http")` with `async def`
- [ ] All `call_next(request)` calls are `await`ed
- [ ] Exception handlers are `async def`
- [ ] API key dependency is `def` (sync - no I/O needed)
- [ ] Settings loading is sync (env parsing only)
- [ ] No blocking calls in async context

## Estimated Effort

| Area | Tasks | Complexity |
|------|-------|------------|
| Configuration Layer | 5 | Low |
| Dependencies Update | 5 | Low |
| API Main Module | 12 | Medium |
| Dependencies Module | 7 | Medium |
| Chat Endpoint | 9 | Medium |
| Git Ignore | 2 | Low |
| Verification | 13 | Medium |

**Total: 53 tasks** (7 new tasks added for async requirements and httpx)

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
