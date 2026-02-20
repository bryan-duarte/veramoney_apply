# Technical Design

## Architecture Decisions

### 1. Manual Dependency Injection Pattern

All service classes use constructor injection with optional defaults:

```
Service Constructor Pattern:
├── Required dependencies: positional arguments
├── Optional dependencies: keyword arguments with None default
└── Default instantiation: self._dep = dep or DefaultDep()
```

**Example:**
```python
class RAGPipeline:
    def __init__(
        self,
        settings: Settings,
        vector_store_manager: ChromaVectorStoreManager | None = None,
        document_loader: DocumentLoader | None = None,
    ):
        self._settings = settings
        self._vector_store_manager = vector_store_manager
        self._document_loader = document_loader
```

### 2. Service Container Pattern

A central `ServiceContainer` holds all service instances:

```
ServiceContainer
├── settings: Settings (via @property)
├── langfuse_manager: LangfuseManager (via @property)
├── memory_store: MemoryStore (lazy via get_memory_store())
├── rag_pipeline: RAGPipeline (via get_rag_pipeline())
├── dataset_manager: DatasetManager (via get_dataset_manager())
└── prompt_manager: PromptManager (via get_prompt_manager())
```

### 3. Layer Architecture (Preserved)

```
API Layer (FastAPI)
├── ChatHandlerBase (NEW)
├── ChatCompleteHandler (NEW)
├── ChatStreamHandler (NEW)
└── HealthHandler (NEW)

Agent Layer (LangChain)
├── AgentFactory (NEW - wraps create_conversational_agent)
├── MemoryStore (EXISTS)
└── Middleware (KEEP - decorator functions)

Tools Layer
├── WeatherAPIClient (EXISTS)
├── FinnhubClient (EXISTS)
└── @tool functions (KEEP)

RAG Layer
├── RAGPipeline (NEW)
├── DocumentLoader (NEW)
├── ChromaVectorStoreManager (EXISTS)
└── KnowledgeRetriever (EXISTS)

Observability Layer
├── LangfuseManager (NEW)
├── PromptManager (NEW)
└── DatasetManager (NEW)

DI Layer (NEW)
└── ServiceContainer
```

## Patterns & Conventions

### Constructor Injection

```python
class ServiceName:
    def __init__(
        self,
        required_dep: RequiredType,
        optional_dep: OptionalType | None = None,
    ):
        self._required_dep = required_dep
        self._optional_dep = optional_dep or DefaultOptional()
```

### Factory Methods (@classmethod)

```python
class ServiceName:
    @classmethod
    def from_settings(cls, settings: Settings) -> "ServiceName":
        return cls(settings=settings)

    @classmethod
    def with_dependencies(
        cls,
        settings: Settings,
        dependency: Dependency,
    ) -> "ServiceName":
        return cls(settings=settings, dependency=dependency)
```

### Properties for State Access

```python
class ServiceName:
    @property
    def is_ready(self) -> bool:
        return self._resource is not None

    @property
    def is_enabled(self) -> bool:
        return self._initialized and self._client is not None

    @property
    def has_errors(self) -> bool:
        return len(self._errors) > 0
```

### Static Methods for Pure Functions

```python
class ServiceName:
    @staticmethod
    def infer_expected_tools(message: str) -> list[str]:
        message_lower = message.lower()
        # ... pure function of message

    @staticmethod
    def build_config(session_id: str, handler: Any) -> dict:
        # ... pure function of inputs
```

### Async Initialization

Classes with async setup use a separate `initialize()` method:

```python
class ServiceName:
    def __init__(self, config: Config):
        self._config = config
        self._resource: Resource | None = None

    async def initialize(self) -> None:
        self._resource = await create_resource(self._config)
```

### Helper Methods for Complex Logic

```python
class ServiceName:
    async def main_operation(self) -> Result:
        self._validate_input()
        intermediate = await self._fetch_data()
        return self._transform_result(intermediate)

    def _validate_input(self) -> None: ...
    async def _fetch_data(self) -> Data: ...
    def _transform_result(self, data: Data) -> Result: ...
```

## Dependencies

### External (Unchanged)

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | >=0.129.0 | API framework |
| langchain | >=1.2.10 | Agent framework |
| chromadb | >=1.5.0 | Vector database |
| httpx | >=0.25.0 | Async HTTP |
| tenacity | >=8.0.0 | Retry logic |
| pydantic | >=2.12.5 | Data validation |

### Internal Dependencies

```
ServiceContainer
    └── depends on: Settings (singleton)

ChatHandlerBase
    ├── depends on: ServiceContainer
    └── depends on: DatasetManager (via property)

RAGPipeline
    ├── depends on: Settings
    └── depends on: ChromaVectorStoreManager (optional)

LangfuseManager
    └── depends on: Settings

DatasetManager
    └── depends on: LangfuseManager (optional)

AgentFactory
    ├── depends on: Settings
    ├── depends on: MemoryStore (optional)
    ├── depends on: LangfuseManager (optional)
    └── depends on: PromptManager (optional)
```

## Integration Points

### FastAPI Lifespan

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    container = ServiceContainer.from_settings(settings)
    await container.initialize()

    app.state.container = container

    yield

    await container.shutdown()
```

### Dependency Injection in Endpoints

```python
@router.post("/chat")
async def chat_complete(
    request: ChatCompleteRequest,
    container: ContainerDep,
):
    handler = ChatCompleteHandler.from_container(container)
    return await handler.handle(request)
```

### LangChain Agent Integration

```python
factory = AgentFactory.with_dependencies(
    settings=settings,
    memory_store=memory_store,
    langfuse_manager=langfuse_manager,
    prompt_manager=prompt_manager,
)
agent, config, handler = await factory.create_agent(session_id)
```

## Data Structures

### ServiceContainer

```python
class ServiceContainer:
    _settings: Settings
    _memory_store: MemoryStore | None
    _langfuse_manager: LangfuseManager | None
    _rag_pipeline: RAGPipeline | None
    _dataset_manager: DatasetManager | None
    _prompt_manager: PromptManager | None

    @classmethod
    def from_settings(cls, settings: Settings) -> "ServiceContainer": ...
    @property
    def settings(self) -> Settings: ...
    @property
    def langfuse_manager(self) -> LangfuseManager | None: ...
    @property
    def is_initialized(self) -> bool: ...
    async def initialize(self) -> None: ...
    async def shutdown(self) -> None: ...
    async def get_memory_store(self) -> MemoryStore: ...
    def get_langfuse_client(self) -> Langfuse | None: ...
    def get_rag_pipeline(self) -> RAGPipeline: ...
    def get_dataset_manager(self) -> DatasetManager: ...
```

### ChatHandlerBase

```python
class ChatHandlerBase:
    @property
    def dataset_manager(self) -> DatasetManager: ...
    async def get_memory_store(self) -> MemoryStore: ...
    def get_langfuse_client(self) -> Langfuse | None: ...
    async def is_opening_message(self, session_id: str) -> bool: ...
    @staticmethod
    def infer_expected_tools(message: str) -> list[str]: ...
    def collect_stock_queries(self, tool_calls: list[ToolCall], ...) -> None: ...
    @classmethod
    def from_container(cls, container: ServiceContainer) -> "ChatHandlerBase": ...
```

### RAGPipeline

```python
class RAGPipeline:
    @classmethod
    def from_settings(cls, settings: Settings) -> "RAGPipeline": ...
    @classmethod
    def with_dependencies(cls, ...) -> "RAGPipeline": ...
    @property
    def status(self) -> RAGPipelineStatus: ...
    @property
    def retriever(self) -> KnowledgeRetriever: ...
    @property
    def is_ready(self) -> bool: ...
    @property
    def has_errors(self) -> bool: ...
    async def initialize(self) -> None: ...
    async def _load_documents(self) -> None: ...
    def _create_retriever(self) -> KnowledgeRetriever: ...
```

### LangfuseManager

```python
class LangfuseManager:
    @classmethod
    def from_settings(cls, settings: Settings) -> "LangfuseManager": ...
    @property
    def is_enabled(self) -> bool: ...
    @property
    def is_prompt_synced(self) -> bool: ...
    @property
    def client(self) -> Langfuse | None: ...
    async def initialize(self) -> Langfuse | None: ...
    def get_handler(self, session_id: str, ...) -> CallbackHandler | None: ...
    def mark_prompt_synced(self) -> None: ...
    def flush(self) -> None: ...
```

### AgentFactory

```python
class AgentFactory:
    @classmethod
    def from_settings(cls, settings: Settings) -> "AgentFactory": ...
    @classmethod
    def with_dependencies(cls, ...) -> "AgentFactory": ...
    @property
    def has_memory_store(self) -> bool: ...
    @property
    def has_langfuse(self) -> bool: ...
    async def create_agent(self, session_id: str) -> tuple[Any, dict, CallbackHandler | None]: ...
    @staticmethod
    def _build_tools() -> list: ...
    @staticmethod
    def _build_middleware_stack() -> list: ...
    @staticmethod
    def _build_config(session_id: str, handler: Any) -> dict: ...
```

## OOP Patterns Summary

| Pattern | Count | Usage |
|---------|-------|-------|
| `@classmethod` | 12+ | Factory methods for common instantiation |
| `@property` | 15+ | Boolean checks, lazy access, computed values |
| `@staticmethod` | 8+ | Pure functions (no self access) |
| Helper methods | 25+ | Extracted complex logic |
| Named booleans | 10+ | `is_ready`, `has_errors`, `is_enabled` |
