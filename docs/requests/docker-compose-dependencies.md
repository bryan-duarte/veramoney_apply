# Docker Compose Service Dependencies Analysis

> *"If your app crashes on startup because a dependency wasn't ready, did you really have dependencies?"*
> — **El Barto**

## Executive Summary

The FastAPI application **can currently run without LangFuse services** because LangFuse is not integrated into the codebase—it's only configured in settings but never imported or used. However, the current Docker Compose dependency configuration has structural issues that should be addressed before LangFuse integration occurs.

## Current State Analysis

### Dependency Graph

```
Level 1 (No dependencies - start in parallel):
├── postgres          [health check: pg_isready]
├── clickhouse        [health check: wget ping]
├── redis             [health check: redis-cli ping]
└── minio             [health check: curl /minio/health/live]

Level 2 (Depend on Level 1):
├── langfuse-web      [NO HEALTH CHECK] → depends on: postgres, minio, redis, clickhouse
├── langfuse-worker   [NO HEALTH CHECK] → depends on: postgres, minio, redis, clickhouse
├── postgres-memory   [health check: pg_isready]
└── chromadb          [health check: tcp port check]

Level 3 (Application):
└── app → depends on:
    ├── chromadb        condition: service_healthy    [GOOD]
    ├── langfuse-web    condition: service_started    [PROBLEMATIC]
    └── postgres-memory condition: service_healthy    [GOOD]
```

### Current App Dependencies Configuration

```yaml
depends_on:
  chromadb:
    condition: service_healthy      # Waits for health check to pass
  langfuse-web:
    condition: service_started       # Only waits for container start
  postgres-memory:
    condition: service_healthy      # Waits for health check to pass
```

### Problem Identification

| Issue | Current State | Risk Level |
|-------|---------------|------------|
| `langfuse-web` has no health check | Container can start but service not ready | **High** |
| App uses `service_started` for langfuse-web | Doesn't verify LangFuse is accepting connections | **High** |
| LangFuse worker has no health check | Cannot verify background processing is ready | **Medium** |
| App lifespan is empty | No startup validation of dependencies | **Medium** |
| Health endpoint is static | No actual connectivity verification | **Low** |

## LangFuse Integration Status

### Current Implementation: NONE

| Aspect | Status | Evidence |
|--------|--------|----------|
| SDK Import | Not used | No `from langfuse import` found |
| Client Initialization | Not implemented | Observability directory is empty |
| Callback Handler | Not configured | No LangChain callback integration |
| Environment Variables | Configured but unused | Settings class has optional fields |
| Hard Dependency | In pyproject.toml only | `"langfuse>=3.14.3"` |

### Conclusion: API Works Without LangFuse

The application is **fully functional** without LangFuse because:
1. LangFuse SDK is never imported
2. Settings make credentials optional (`str | None`)
3. No code path attempts to connect to LangFuse
4. Observability layer is planned but not implemented

## Recommended Changes

### Option A: If LangFuse Integration is Planned

#### 1. Add Health Checks to LangFuse Services

```yaml
langfuse-web:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:3000/api/health"]
    interval: 10s
    timeout: 5s
    retries: 5
    start_period: 30s

langfuse-worker:
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -h postgres -U postgres"]
    interval: 10s
    timeout: 5s
    retries: 5
    start_period: 10s
```

#### 2. Update App Dependencies

```yaml
app:
  depends_on:
    chromadb:
      condition: service_healthy
    langfuse-web:
      condition: service_healthy    # Changed from service_started
    langfuse-worker:
      condition: service_healthy    # Added new dependency
    postgres-memory:
      condition: service_healthy
```

#### 3. Add Startup Validation in App

```python
# src/api/app.py
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Validate LangFuse connectivity
    if settings.langfuse_public_key and settings.langfuse_secret_key:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{settings.langfuse_host}/api/health")
                response.raise_for_status()
                logger.info("LangFuse connection verified")
            except Exception as e:
                logger.warning(f"LangFuse not available: {e}")
    yield
```

### Option B: If LangFuse is Optional/Future Work

#### 1. Keep Current Dependencies but Add Health Checks

Add health checks to LangFuse services anyway (for monitoring), but keep `service_started` condition:

```yaml
langfuse-web:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:3000/api/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 30s
```

#### 2. Implement Graceful Degradation

When LangFuse is integrated, wrap all calls in try-except with fallback:

```python
# src/observability/langfuse_client.py
class LangFuseClient:
    def __init__(self, settings: Settings):
        self._enabled = all([
            settings.langfuse_public_key,
            settings.langfuse_secret_key,
        ])
        self._client = None
        if self._enabled:
            try:
                from langfuse import Langfuse
                self._client = Langfuse(
                    public_key=settings.langfuse_public_key,
                    secret_key=settings.langfuse_secret_key,
                    host=settings.langfuse_host,
                )
            except ImportError:
                self._enabled = False

    def is_enabled(self) -> bool:
        return self._client is not None
```

### Option C: Remove LangFuse Dependency (If Not Needed)

If LangFuse won't be used, simplify the stack:

```yaml
app:
  depends_on:
    chromadb:
      condition: service_healthy
    postgres-memory:
      condition: service_healthy
    # Remove langfuse-web dependency entirely
```

## Service Readiness Timeline

### Current Behavior (Problematic)

```
Time    0s:  postgres, clickhouse, redis, minio, postgres-memory, chromadb start
Time   10s:  postgres healthy
Time   15s:  chromadb healthy
Time   15s:  langfuse-web starts (but may not be ready)
Time   15s:  app starts (langfuse-web condition: service_started)
Time   16s:  app tries to use LangFuse → POTENTIAL FAILURE
Time   45s:  langfuse-web finally healthy (30s startup)
```

### After Fixes (Correct Behavior)

```
Time    0s:  postgres, clickhouse, redis, minio, postgres-memory, chromadb start
Time   10s:  postgres healthy
Time   15s:  chromadb healthy
Time   15s:  langfuse-web starts
Time   45s:  langfuse-web healthy (health check passes)
Time   45s:  app starts (all dependencies verified healthy)
```

## Implementation Priority

| Priority | Change | Effort | Impact |
|----------|--------|--------|--------|
| 1 | Add health check to langfuse-web | Low | High |
| 2 | Change langfuse-web condition to `service_healthy` | Low | High |
| 3 | Add health check to langfuse-worker | Low | Medium |
| 4 | Implement graceful degradation in code | Medium | Medium |
| 5 | Add startup validation in lifespan | Medium | Medium |

## Direct Answer to Your Question

> "I don't know if the API can be used without this other service being running."

**Yes, the API can be used without LangFuse running.** LangFuse is configured but not integrated—the application never imports or uses the LangFuse SDK. The current dependency is essentially a placeholder for future observability integration.

However, if you plan to integrate LangFuse in the future, you should:
1. Add health checks to LangFuse services now
2. Change the dependency condition from `service_started` to `service_healthy`
3. Implement graceful degradation when LangFuse is unavailable

---
*Analysis by: El Barto*
*Date: 2026-02-19*
