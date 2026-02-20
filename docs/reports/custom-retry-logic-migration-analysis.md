# Custom Retry Logic Migration Analysis

> *"Reinventing the wheel is fine, until you realize the wheel you invented is square and tenacity is round."*
> — **El Barto**

## Executive Summary

The codebase contains **2 custom retry implementations** using manual `for` loops that should be migrated to tenacity for consistency, maintainability, and reliability. Three other locations already correctly use tenacity. No `while` loop retry patterns exist in the codebase.

---

## Current State Overview

### Retry Implementations Summary

| File | Lines | Pattern | Library | Migration Needed |
|------|-------|---------|---------|------------------|
| `src/observability/manager.py` | 37-73 | `for` loop | Manual | **Yes** |
| `src/chainlit/sse_client.py` | 42-79 | `for` loop | Manual | **Yes** |
| `src/tools/weather/client.py` | 48-63 | `AsyncRetrying` | tenacity | No |
| `src/tools/stock/client.py` | 44-59 | `AsyncRetrying` | tenacity | No |
| `src/rag/loader.py` | 30-46 | `AsyncRetrying` | tenacity | No |

---

## Custom Retry Implementations (Migration Required)

### 1. Langfuse Client Initialization

**File:** `src/observability/manager.py:37-73`

**Current Implementation:**
```python
_MAX_INIT_RETRIES = 3
_INIT_RETRY_DELAY_SECONDS = 5

for attempt in range(1, _MAX_INIT_RETRIES + 1):
    try:
        is_authenticated = await self._check_auth()
        if not is_authenticated:
            return

        self._client = Langfuse(
            public_key=self._settings.langfuse_public_key,
            secret_key=self._settings.langfuse_secret_key,
            host=self._settings.langfuse_host,
        )
        self._initialized = True
        logger.info(...)
        return

    except Exception as exc:
        is_last_attempt = attempt >= _MAX_INIT_RETRIES
        if not is_last_attempt:
            logger.warning(
                "Langfuse init failed (attempt %d/%d): %s - retrying in %ds",
                attempt, _MAX_INIT_RETRIES, exc, _INIT_RETRY_DELAY_SECONDS,
            )
            await asyncio.sleep(_INIT_RETRY_DELAY_SECONDS)
        else:
            logger.warning(
                "Langfuse init failed after %d attempts: %s - observability disabled",
                _MAX_INIT_RETRIES, exc,
            )
```

**Characteristics:**
- Max attempts: 3
- Delay: Fixed 5 seconds
- Exceptions: All exceptions caught
- Graceful degradation: Logs warning and continues without observability

**Migration Complexity:** Low
- Straightforward retry with fixed delay
- Needs custom callback for graceful degradation on final failure

---

### 2. SSE Streaming Client

**File:** `src/chainlit/sse_client.py:42-79`

**Current Implementation:**
```python
delay = self._settings.retry_delay

for attempt in range(self._settings.max_retries):
    try:
        async for event in self._fetch_events(message, session_id):
            yield event
        return
    except (httpx.ConnectError, httpx.ReadError) as exc:
        last_error = exc
        logger.warning("sse_network_error attempt=%d/%d error=%s", ...)
    except httpx.TimeoutException as exc:
        last_error = exc
        logger.warning("sse_timeout attempt=%d/%d", ...)
    except _RetryableHTTPError as exc:
        last_error = exc
        logger.warning("sse_server_error attempt=%d/%d status=%d", ...)

    is_last_attempt = attempt >= self._settings.max_retries - 1
    if is_last_attempt:
        break

    await asyncio.sleep(delay)
    delay *= BACKOFF_MULTIPLIER
```

**Characteristics:**
- Max attempts: Configurable via `CHAINLIT_MAX_RETRIES` (default: 3)
- Delay: Exponential backoff starting at 1.0s with multiplier 2
- Exceptions: `httpx.ConnectError`, `httpx.ReadError`, `httpx.TimeoutException`, `_RetryableHTTPError`
- Non-retryable: 401, 403, 429 status codes
- Custom exception class: `_RetryableHTTPError` (line 151-154)

**Migration Complexity:** Medium
- Exponential backoff with custom multiplier
- Selective exception handling (only network/server errors)
- Async generator function (requires careful handling)
- Custom HTTP error classification logic

---

## Existing Tenacity Implementations (Reference Patterns)

These implementations serve as templates for migration:

### Pattern A: Basic Exponential Backoff

**Used by:** `src/tools/weather/client.py`, `src/tools/stock/client.py`

```python
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

async for attempt in AsyncRetrying(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=INITIAL_RETRY_DELAY_SECONDS),
    retry=lambda exc: isinstance(exc, httpx.TimeoutException),
    reraise=True,
):
    with attempt:
        # operation here
```

### Pattern B: Retry All Exceptions

**Used by:** `src/rag/loader.py`

```python
async for attempt in AsyncRetrying(
    stop=stop_after_attempt(MAX_DOWNLOAD_RETRIES),
    wait=wait_exponential(multiplier=INITIAL_RETRY_DELAY_SECONDS),
    reraise=True,
):
    with attempt:
        # operation here
```

---

## Migration Recommendations

### Priority 1: `src/observability/manager.py`

**Rationale:** Simpler implementation, fixed delay pattern already supported by tenacity.

**Recommended Migration:**
```python
from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed, retry_if_exception_type

async for attempt in AsyncRetrying(
    stop=stop_after_attempt(_MAX_INIT_RETRIES),
    wait=wait_fixed(_INIT_RETRY_DELAY_SECONDS),
    reraise=False,
):
    with attempt:
        is_authenticated = await self._check_auth()
        if not is_authenticated:
            return
        self._client = Langfuse(...)
        self._initialized = True
        return
```

**Consideration:** Current implementation logs differently on final failure. Use `before_sleep_log` or wrap the retry loop to maintain current logging behavior.

---

### Priority 2: `src/chainlit/sse_client.py`

**Rationale:** More complex due to async generator and selective exception handling.

**Recommended Migration:**
```python
from tenacity import (
    AsyncRetrying,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

retryable_exceptions = (
    httpx.ConnectError,
    httpx.ReadError,
    httpx.TimeoutException,
    _RetryableHTTPError,
)

async for attempt in AsyncRetrying(
    stop=stop_after_attempt(self._settings.max_retries),
    wait=wait_exponential(
        multiplier=self._settings.retry_delay,
        exp_base=BACKOFF_MULTIPLIER,
    ),
    retry=retry_if_exception_type(retryable_exceptions),
    reraise=True,
):
    with attempt:
        async for event in self._fetch_events(message, session_id):
            yield event
        return
```

**Consideration:** The custom `_RetryableHTTPError` exception classification happens inside `_fetch_events`, which is correct. The retry logic only needs to catch the classified exception.

---

## Technical Debt Summary

| Metric | Value |
|--------|-------|
| Custom retry implementations | 2 |
| Files needing migration | 2 |
| Lines of custom retry code | ~70 |
| Existing tenacity implementations | 3 |
| Consistency gap | 40% (2/5 files) |

---

## Benefits of Migration

1. **Consistency**: All retry logic uses the same library and patterns
2. **Maintainability**: Less custom code to maintain
3. **Reliability**: Tenacity handles edge cases (jitter, proper exception chaining)
4. **Observability**: Built-in logging and metrics hooks via `before_sleep_log`
5. **Testability**: Easier to mock/configure retry behavior in tests

---

## Migration Risks

| Risk | Mitigation |
|------|------------|
| Behavior change in edge cases | Write integration tests before migration |
| Async generator complexity | Test streaming behavior thoroughly |
| Logging format changes | Use tenacity callbacks to maintain log format |
| Graceful degradation logic | Wrap retry loop to handle final failure |

---

## Files Modified Summary

### Files Requiring Changes

| File | Change Type | Complexity |
|------|-------------|------------|
| `src/observability/manager.py` | Replace retry loop | Low |
| `src/chainlit/sse_client.py` | Replace retry loop | Medium |

### Files to Remove After Migration

| Constant | Location | Status |
|----------|----------|--------|
| `_MAX_INIT_RETRIES` | `src/observability/manager.py:13` | Keep (passed to tenacity) |
| `_INIT_RETRY_DELAY_SECONDS` | `src/observability/manager.py:14` | Keep (passed to tenacity) |
| `BACKOFF_MULTIPLIER` | `src/chainlit/constants.py:6` | Keep (passed to tenacity) |

---

## Appendix: No While-Loop Patterns Found

The search confirmed zero instances of `while` loop-based retry logic. All retry implementations use either:
- `for` loops with `range()` and manual delay handling
- `tenacity.AsyncRetrying` async iterator

This is good—the codebase avoids the most error-prone retry pattern (infinite while loops with manual break conditions).

---
*Report generated by: El Barto*
*Date: 2026-02-20*
