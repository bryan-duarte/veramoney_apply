# User Preferences & Decisions

## Configuration Preferences

- **Context Level**: Profundo (comprehensive exploration with 12 parallel tasks)
- **Participation Level**: Control pleno (user validates ALL design decisions)
- **Detail Level**: Neutral (example snippets, implementer decides final code)
- **Extras**: None (no tests or documentation tasks)

## Q&A and Rationale

### Priority & Scope

**Q:** Which issues should be prioritized?
**A:** All Issues
**Decision:** Comprehensive fix covering CRITICAL, HIGH, MEDIUM, and LOW severity issues
**Rejected:** Security-first (delays stability), Stability-first (delays security), High-only (leaves technical debt)

### HTTP Client Architecture

**Q:** How should HTTP client connection pooling (H5/H6) be implemented?
**A:** Singleton in Client with lazy initialization
**Decision:** Each client manages its own `httpx.AsyncClient` with lazy init via `_get_client()` method. User provided specific pattern with `httpx.Limits(max_connections=100, max_keepalive_connections=20)` and HTTP/2 support.
**Rejected:** Dependency injection (more complex), Global pool (shared state issues)

### Concurrency

**Q:** What granularity of locking for race condition fix (H3)?
**A:** Instance-Level Lock
**Decision:** Single `asyncio.Lock` per SupervisorFactory instance protects all lazy-initialized resources
**Rejected:** Per-resource locks (over-engineering), Hybrid (unnecessary complexity)

### Security

**Q:** SSRF protection strategy (H2)?
**A:** Allowlist Only
**Decision:** Only URLs matching configured document sources in `document_configs.py` are allowed
**Rejected:** Allowlist + IP blocking (overkill for this use case), Defense in depth (excessive)

**Q:** Rate limit key sanitization (M8)?
**A:** Validate + Sanitize
**Decision:** Validate API key format (length, characters) before using as rate limit key
**Rejected:** Hash API key (breaks debugging), Keep as-is (security risk)

**Q:** Log injection protection (M9)?
**A:** Add Sanitization Helper
**Decision:** Create `sanitize_for_log()` helper to escape newlines and special characters
**Rejected:** Keep as-is (vulnerable), Structured logging (larger refactor)

### Architecture

**Q:** SRP violation fix (H7)?
**A:** Mixin Composition
**Decision:** Split ChatHandlerBase into mixin classes (ToolIntentMixin, SessionStateMixin, StockQueryMixin) that are composed together
**Rejected:** Extract services (more files), Minimal change (doesn't address issue)

**Q:** Settings ISP violation (H8)?
**A:** Keep As-Is
**Decision:** Single Settings class is acceptable - not causing real problems
**Rejected:** Multiple settings classes (breaking change), Nested configuration (complexity)

**Q:** Middleware LSP violation (H9)?
**A:** Keep As-Is
**Decision:** Current exception handling is intentional for error resilience
**Rejected:** Specific exception only (could miss edge cases)

**Q:** DRY violation fix (M3)?
**A:** Keep As-Is
**Decision:** Each worker has specific variations that make generic builder complex
**Rejected:** Generic factory (over-abstraction), Separate builder module (unnecessary)

**Q:** Middleware OCP violation (M7)?
**A:** Keep Hardcoded
**Decision:** Hardcoded stack in `_build_middleware_stack()` is simple and works
**Rejected:** Settings-based (over-engineering), Registry pattern (unnecessary complexity)

### Code Quality

**Q:** Duplicate schemas fix (M4)?
**A:** Base Class Inheritance
**Decision:** Create `ChatRequest` base class that `ChatCompleteRequest` and `ChatStreamRequest` extend
**Rejected:** Single unified class (may diverge), Keep as-is (duplication)

**Q:** Circular dependency fix (M1)?
**A:** Extract Prompts Module
**Decision:** Move all prompt constants to `src/prompts/` module with no dependencies on app code
**Rejected:** Lazy import (runtime overhead), Keep as-is (architectural smell)

**Q:** Constants placement (M2)?
**A:** Move to Agent Layer
**Decision:** Move `ASK_*_AGENT` constants from `src/tools/constants.py` to `src/agent/constants.py`
**Rejected:** Keep with documentation (still misplaced), Keep as-is (architectural smell)

**Q:** Status enum (L1)?
**A:** Add Enum
**Decision:** Create `PipelineStatus` enum (INITIALIZING, LOADING, READY, ERROR, PARTIAL)
**Rejected:** Keep as-is (magic strings)

**Q:** Tool return type (L2)?
**A:** Fix Type Annotation
**Decision:** Change return type from `tool` to `BaseTool` or `Annotated[..., BaseTool]`
**Rejected:** Keep as-is (incorrect typing)

**Q:** Error JSON handling (L5)?
**A:** Use Pydantic Error Schema
**Decision:** Create `WeatherError` schema and use `model_dump_json()` for consistency
**Rejected:** Keep as-is (inconsistent), json.dumps() (manual serialization)

**Q:** HTTPS for WeatherAPI (L6)?
**A:** Change to HTTPS
**Decision:** Change base URL to `https://api.weatherapi.com/v1/current.json`
**Rejected:** Keep HTTP (insecure), Investigate first (HTTPS is standard)

**Q:** Keyword tuples vs sets (L3)?
**A:** Keep As-Is
**Decision:** Tuples are fine - Python caches small tuples efficiently
**Rejected:** Use frozenset (micro-optimization)

### API Limitations

**Q:** WeatherAPI key in URL (M5)?
**A:** Keep in URL (API Limitation)
**Decision:** WeatherAPI requires key in query parameter - cannot change
**Rejected:** Move to header (not supported by API)

### Edge Cases

**Q:** Division by zero result (C3)?
**A:** Return 0.0
**Decision:** Return `0.0` for `change_percent` when `previous_close` is 0
**Rejected:** Return None (breaking change), Return 'N/A' (type inconsistency)

**Q:** None checkpoint behavior (C4)?
**A:** Return True
**Decision:** Return `True` (is opening message) when state is None - treat as new session
**Rejected:** Raise exception (over-engineering), Log warning + return True (noisy)

**Q:** Sync blocking fix (H4)?
**A:** Use asyncio.to_thread()
**Decision:** Wrap sync Langfuse client calls in `asyncio.to_thread()` to prevent event loop blocking
**Rejected:** Keep as-is (blocks event loop), Async SDK (may not be available)

**Q:** HTTP client cleanup?
**A:** Lifespan Cleanup
**Decision:** Register client cleanup in FastAPI lifespan shutdown handler
**Rejected:** Resource manager (over-engineering), No cleanup (resource leak)
