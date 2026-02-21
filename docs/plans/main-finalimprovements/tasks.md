# Implementation Tasks

## Task Breakdown

### Phase 1: CRITICAL Fixes (Stability)

#### Stock Client - Division by Zero (C3)
- [ ] Add defensive check for `previous_close == 0` in `src/tools/stock/client.py`
- [ ] Return `0.0` for `change_percent` when division not possible
- [ ] Update `StockOutput` schema to use `float` for `change_percent`

#### Supervisor - None Dereference (C4)
- [ ] Add early return for `None` state in `src/agent/core/supervisor.py`
- [ ] Add check: `if existing_state is None or existing_state.checkpoint is None`
- [ ] Return `True` (treat as opening message) when state is None

---

### Phase 2: HIGH Priority (Security & Performance)

#### API Key Timing Attack (H1)
- [ ] Import `secrets` module in `src/api/core/dependencies.py`
- [ ] Replace `!=` comparison with `secrets.compare_digest()`
- [ ] Handle `None` case: `secrets.compare_digest(x_api_key or "", settings.api_key)`

#### SSRF Protection (H2)
- [ ] Create `validate_url()` function in `src/rag/loader.py`
- [ ] Define `ALLOWED_DOMAINS` frozenset from document configs
- [ ] Validate URL scheme is `https` and domain is allowlisted
- [ ] Raise `ValueError` with descriptive message for invalid URLs

#### Race Condition Fix (H3)
- [ ] Add `_init_lock: asyncio.Lock` to `SupervisorFactory.__init__`
- [ ] Wrap `_get_memory_store()` with double-checked locking
- [ ] Ensure atomic initialization of memory store

#### Sync Blocking Fix (H4)
- [ ] Import `asyncio` in `src/observability/prompts.py`
- [ ] Wrap sync Langfuse client calls in `asyncio.to_thread()`
- [ ] Affected methods: `sync_supervisor_prompt()`, `sync_worker_prompts()`, `_fetch_existing_system_content()`

#### HTTP Connection Pooling - Weather (H5)
- [ ] Add `_client: httpx.AsyncClient | None = None` class variable
- [ ] Add `_lock: asyncio.Lock` for thread-safe initialization
- [ ] Implement `_get_client()` with lazy initialization and connection limits
- [ ] Implement `aclose()` method for cleanup
- [ ] Update `_make_request()` to use `_get_client()`
- [ ] Change base URL from HTTP to HTTPS (L6)

#### HTTP Connection Pooling - Stock (H6)
- [ ] Add `_client: httpx.AsyncClient | None = None` class variable
- [ ] Add `_lock: asyncio.Lock` for thread-safe initialization
- [ ] Implement `_get_client()` with lazy initialization and connection limits
- [ ] Implement `aclose()` method for cleanup
- [ ] Update `_make_request()` to use `_get_client()`

#### ChatHandlerBase SRP Fix (H7)
- [ ] Create `src/api/handlers/mixins.py`
- [ ] Extract `ToolIntentMixin` with `infer_expected_tools()` static method
- [ ] Extract `SessionStateMixin` with `is_opening_message()` method
- [ ] Extract `StockQueryMixin` with `collect_stock_queries()` method
- [ ] Update `ChatHandlerBase` to inherit from mixins
- [ ] Update `ChatStreamHandler` and `ChatCompleteHandler` if needed

---

### Phase 3: MEDIUM Priority (Architecture & Code Quality)

#### Circular Dependency Fix (M1)
- [ ] Create `src/prompts/__init__.py`
- [ ] Create `src/prompts/system.py` with system prompt constants
- [ ] Create `src/prompts/workers.py` with worker prompt constants
- [ ] Update imports in `src/observability/prompts.py`
- [ ] Update imports in `src/agent/workers/*.py`
- [ ] Update imports in `src/agent/core/prompts.py` (remove if empty)

#### Constants Move (M2)
- [ ] Create `src/agent/constants.py`
- [ ] Move `ASK_WEATHER_AGENT`, `ASK_STOCK_AGENT`, `ASK_KNOWLEDGE_AGENT` from tools
- [ ] Move `ALL_WORKER_TOOLS` list
- [ ] Update imports in `src/agent/core/supervisor.py`
- [ ] Update imports in `src/agent/middleware/tool_error_handler.py`

#### Schema Consolidation (M4)
- [ ] Create `ChatRequest` base class in `src/api/schemas.py`
- [ ] Move `message` and `session_id` fields to base class
- [ ] Move `validate_session_id_format` validator to base class
- [ ] Update `ChatCompleteRequest` to inherit from `ChatRequest`
- [ ] Update `ChatStreamRequest` to inherit from `ChatRequest`

#### Rate Limit Key Sanitization (M8)
- [ ] Add validation in `src/api/core/rate_limiter.py`
- [ ] Check API key length (max 128 chars)
- [ ] Check API key contains only alphanumeric and hyphens/underscores
- [ ] Use sanitized/validated key in rate limit key

#### Log Injection Fix (M9)
- [ ] Create `src/utils/logging.py` module
- [ ] Implement `sanitize_for_log(value: str, max_length: int = 100) -> str`
- [ ] Escape newlines, tabs, and control characters
- [ ] Truncate long values
- [ ] Update `src/api/handlers/chat_stream.py` to use sanitizer
- [ ] Update `src/api/handlers/chat_complete.py` to use sanitizer

---

### Phase 4: LOW Priority (Polish)

#### RAG Pipeline Status Enum (L1)
- [ ] Create `PipelineStatus` StrEnum in `src/rag/schemas.py`
- [ ] Add values: INITIALIZING, LOADING, READY, ERROR, PARTIAL
- [ ] Update `src/rag/pipeline.py` to use enum instead of strings

#### Tool Return Type Fix (L2)
- [ ] Update `create_knowledge_tool()` return type annotation
- [ ] Change from `-> tool` to `-> BaseTool`
- [ ] Add `from langchain_core.tools import BaseTool` import

#### Weather Error Schema (L5)
- [ ] Create `WeatherError` Pydantic model in `src/tools/weather/schemas.py`
- [ ] Update `get_weather()` tool to use `WeatherError.model_dump_json()`
- [ ] Replace all f-string error JSON with schema-based serialization

#### HTTPS for WeatherAPI (L6)
- [ ] Change `BASE_URL` in `src/tools/weather/client.py`
- [ ] From: `http://api.weatherapi.com/v1/current.json`
- [ ] To: `https://api.weatherapi.com/v1/current.json`

---

### Phase 5: Integration & Cleanup

#### Lifespan Cleanup Registration
- [ ] Import clients in `src/api/app.py`
- [ ] Register `weather_client.aclose()` in shutdown
- [ ] Register `stock_client.aclose()` in shutdown
- [ ] Ensure proper exception handling during cleanup

#### Final Verification
- [ ] Run ruff linting on all modified files
- [ ] Verify no new circular dependencies introduced
- [ ] Verify all async functions remain async
- [ ] Verify type annotations are correct

---

## Summary

| Phase | Tasks | Focus |
|-------|-------|-------|
| Phase 1 | 5 | CRITICAL stability fixes |
| Phase 2 | 23 | HIGH security & performance |
| Phase 3 | 15 | MEDIUM architecture fixes |
| Phase 4 | 8 | LOW polish items |
| Phase 5 | 6 | Integration & verification |
| **Total** | **57** | |

## Dependencies Between Phases

```
Phase 1 (CRITICAL)
    ↓
Phase 2 (HIGH)
    ├── H5/H6 connection pooling → Phase 5 cleanup
    └── H7 mixins → no blocking deps
    ↓
Phase 3 (MEDIUM)
    ├── M1 prompts → M2 constants (can run in parallel)
    └── M4 schemas → no blocking deps
    ↓
Phase 4 (LOW)
    ↓
Phase 5 (Integration)
```
