# Technical Design

## Architecture Decisions

### 1. HTTP Client Connection Pooling

**Decision**: Singleton pattern within each client class with lazy initialization

**Rationale**: Avoids the complexity of dependency injection while providing connection pooling benefits. Each client instance manages its own `httpx.AsyncClient` lifecycle.

**Pattern**:
```python
class APIClient:
    _client: httpx.AsyncClient | None = None
    _lock: asyncio.Lock = asyncio.Lock()

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is not None:
            return self._client

        async with self._lock:
            if self._client is not None:
                return self._client

            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=httpx.Timeout(connect=5.0, read=30.0),
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
                http2=True,
            )
        return self._client

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
```

### 2. Race Condition Prevention

**Decision**: Instance-level `asyncio.Lock` for lazy initialization

**Rationale**: Simple double-checked locking pattern prevents concurrent initialization without over-engineering with per-resource locks.

**Pattern**:
```python
class SupervisorFactory:
    def __init__(self, ...):
        self._memory_store: MemoryStore | None = None
        self._init_lock = asyncio.Lock()

    async def _get_memory_store(self) -> MemoryStore:
        if self._memory_store is not None:
            return self._memory_store

        async with self._init_lock:
            if self._memory_store is not None:
                return self._memory_store

            self._memory_store = MemoryStore(settings=self._settings)
            await self._memory_store.initialize()
        return self._memory_store
```

### 3. SSRF Protection

**Decision**: URL allowlist based on configured document sources

**Rationale**: Only fetch URLs that are explicitly configured in `document_configs.py`. Simple and effective for this use case.

**Pattern**:
```python
ALLOWED_DOMAINS: frozenset[str] = frozenset({
    "pub-739843c5b2e64a7881e1fa442a3d9075.r2.dev",
})

def validate_url(url: str) -> bool:
    parsed = urlparse(url)
    is_https = parsed.scheme == "https"
    is_allowed_domain = parsed.netloc in ALLOWED_DOMAINS
    return is_https and is_allowed_domain
```

### 4. Mixin Composition for ChatHandlerBase

**Decision**: Split responsibilities into mixin classes

**Rationale**: Maintains single inheritance while separating concerns. Each mixin handles one responsibility.

**Structure**:
```python
class ToolIntentMixin:
    @staticmethod
    def infer_expected_tools(message: str) -> list[str]:
        ...

class SessionStateMixin:
    def __init__(self, memory_store: MemoryStore):
        self._memory_store = memory_store

    async def is_opening_message(self, session_id: str) -> bool:
        ...

class StockQueryMixin:
    def __init__(self, dataset_manager: DatasetManager):
        self._dataset_manager = dataset_manager

    def collect_stock_queries(self, ...) -> None:
        ...

class ChatHandlerBase(ToolIntentMixin, SessionStateMixin, StockQueryMixin):
    def __init__(self, ...):
        ToolIntentMixin.__init__(self)
        SessionStateMixin.__init__(self, memory_store)
        StockQueryMixin.__init__(self, dataset_manager)
```

### 5. Prompt Constants Extraction

**Decision**: New `src/prompts/` module with no dependencies

**Structure**:
```
src/prompts/
    __init__.py
    system.py      # VERA_FALLBACK_SYSTEM_PROMPT, SUPERVISOR_SYSTEM_PROMPT_FALLBACK
    workers.py     # WEATHER_WORKER_PROMPT, STOCK_WORKER_PROMPT, KNOWLEDGE_WORKER_PROMPT
```

**Rationale**: Breaks circular dependency by placing shared constants in a leaf module.

### 6. Schema Consolidation

**Decision**: Base class inheritance for request schemas

**Pattern**:
```python
class ChatRequest(BaseModel):
    message: str = Field(...)
    session_id: str = Field(...)

    @field_validator("session_id")
    @classmethod
    def validate_session_id_format(cls, value: str) -> str:
        ...

class ChatCompleteRequest(ChatRequest):
    pass

class ChatStreamRequest(ChatRequest):
    pass
```

## Patterns & Conventions

### Error Handling

- Use custom exceptions for domain errors
- Return structured JSON errors from tools
- Log exceptions with `logger.exception()` for stack traces

### Logging

- Structured key-value format: `"action key=%s value=%s"`
- Named boolean conditions: `is_valid = ...` before conditionals
- Sanitize user input before logging

### Async

- All I/O functions are `async def`
- Use `httpx.AsyncClient` with connection pooling
- Use `asyncio.to_thread()` for unavoidable sync calls
- Lazy initialization with locks for shared resources

### Type Annotations

- Use `X | None` syntax (Python 3.11+)
- Pydantic models for all external data
- `BaseTool` for tool return types

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| httpx | >=0.25.0 | Async HTTP client with connection pooling |
| pydantic | >=2.12.5 | Data validation and schemas |
| asyncio | stdlib | Concurrency and locks |
| secrets | stdlib | Constant-time comparison |

## Integration Points

### FastAPI Lifespan

HTTP clients must be registered for cleanup:

```python
# src/api/app.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    ...

    yield

    # Shutdown
    await weather_client.aclose()
    await stock_client.aclose()
    await memory_store.close()
```

### Dependency Injection

New clients with pooling should be created once and injected:

```python
# src/api/core/dependencies.py
def get_weather_client() -> WeatherAPIClient:
    return request.app.state.weather_client
```

### Middleware Stack

No changes to middleware registration - keep hardcoded stack.

## Data Structures

### New Types

```python
# src/rag/schemas.py
class PipelineStatus(StrEnum):
    INITIALIZING = "initializing"
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"
    PARTIAL = "partial"

# src/tools/weather/schemas.py
class WeatherError(BaseModel):
    error: str
    code: str | None = None

# src/api/schemas.py
class ChatRequest(BaseModel):
    message: str
    session_id: str
```

### Modified Types

```python
# src/tools/stock/schemas.py
class StockOutput(BaseModel):
    ticker: str
    price: float
    currency: str
    timestamp: str
    change: str
    change_percent: float  # Changed from str, returns 0.0 on div/0
```
