# DI Container Implementation

## Overview

The ServiceContainer provides centralized dependency management with lazy initialization and optional constructor injection support.

## Files to Create

- `src/di/__init__.py` - Module exports
- `src/di/container.py` - ServiceContainer class (NEW)

## Files to Modify

- `src/api/app.py` - Use ServiceContainer in lifespan

## Implementation Guidelines

### ServiceContainer Class

```python
class ServiceContainer:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._lock = asyncio.Lock()

        self._memory_store: MemoryStore | None = None
        self._langfuse_manager: LangfuseManager | None = None
        self._rag_pipeline: RAGPipeline | None = None
        self._dataset_manager: DatasetManager | None = None
        self._prompt_manager: PromptManager | None = None

    @classmethod
    def from_settings(cls, settings: Settings) -> "ServiceContainer":
        return cls(settings=settings)

    @property
    def settings(self) -> Settings:
        return self._settings

    @property
    def langfuse_manager(self) -> LangfuseManager | None:
        return self._langfuse_manager

    @property
    def is_initialized(self) -> bool:
        return self._memory_store is not None

    async def initialize(self) -> None:
        await self._initialize_langfuse()
        await self._initialize_rag_pipeline()
        await self._initialize_memory_store()
        self._initialize_managers()

    async def _initialize_langfuse(self) -> None:
        self._langfuse_manager = LangfuseManager.from_settings(self._settings)
        await self._langfuse_manager.initialize()

        if self._langfuse_manager.is_enabled:
            self._prompt_manager = PromptManager.from_settings(
                settings=self._settings,
                langfuse_manager=self._langfuse_manager,
            )
            await self._prompt_manager.sync_to_langfuse()
            self._langfuse_manager.mark_prompt_synced()

    async def _initialize_rag_pipeline(self) -> None:
        self._rag_pipeline = RAGPipeline.from_settings(self._settings)
        await self._rag_pipeline.initialize()

    async def _initialize_memory_store(self) -> None:
        self._memory_store = MemoryStore.from_settings(self._settings)
        await self._memory_store.initialize()

    def _initialize_managers(self) -> None:
        self._dataset_manager = DatasetManager.from_langfuse_manager(
            self._langfuse_manager
        )

    async def shutdown(self) -> None:
        await self._close_memory_store()
        self._flush_langfuse()

    async def _close_memory_store(self) -> None:
        if self._memory_store:
            await self._memory_store.close()

    def _flush_langfuse(self) -> None:
        if self._langfuse_manager:
            self._langfuse_manager.flush()

    async def get_memory_store(self) -> MemoryStore:
        async with self._lock:
            if self._memory_store is None:
                await self._initialize_memory_store()
        return self._memory_store

    def get_langfuse_client(self) -> Langfuse | None:
        if self._langfuse_manager is None:
            return None
        return self._langfuse_manager.client

    def get_rag_pipeline(self) -> RAGPipeline:
        return self._rag_pipeline

    def get_knowledge_retriever(self) -> KnowledgeRetriever:
        if self._rag_pipeline is None:
            raise RuntimeError("RAG pipeline not initialized")
        return self._rag_pipeline.retriever

    def get_dataset_manager(self) -> DatasetManager:
        if self._dataset_manager is None:
            self._dataset_manager = DatasetManager.from_langfuse_manager(
                self._langfuse_manager
            )
        return self._dataset_manager

    def get_prompt_manager(self) -> PromptManager | None:
        return self._prompt_manager
```

### FastAPI Lifespan Integration

Update `src/api/app.py`:

```python
from src.di import ServiceContainer

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging()

    container = ServiceContainer.from_settings(settings)
    await container.initialize()

    app.state.container = container

    rag_pipeline = container.get_rag_pipeline()
    app.state.rag_initialized = rag_pipeline.is_ready

    yield

    await container.shutdown()
```

### Endpoint Dependency

Add to `src/api/core/dependencies.py`:

```python
from fastapi import Request
from src.di import ServiceContainer

def get_container(request: Request) -> ServiceContainer:
    return request.app.state.container

ContainerDep = Annotated[ServiceContainer, Depends(get_container)]
```

## OOP Patterns Applied

| Pattern | Usage |
|---------|-------|
| `@classmethod` | `from_settings()` - factory method for common instantiation |
| `@property` | `settings` - read-only access to configuration |
| `@property` | `langfuse_manager` - read-only access to manager |
| `@property` | `is_initialized` - boolean state check |
| Helper methods | `_initialize_langfuse()`, `_initialize_rag_pipeline()`, etc. |
| Named booleans | `is_enabled`, `is_ready` |
| Constructor injection | All services injectable via `__init__` |
| Private attributes | `self._settings`, `self._lock`, `self._memory_store` |

## Dependencies

- Settings (required, via constructor)
- MemoryStore (created internally, lazy)
- LangfuseManager (created internally)
- RAGPipeline (created internally)
- DatasetManager (created internally)
- PromptManager (created internally)

## Integration Notes

- ServiceContainer is created once during app startup via `from_settings()`
- Stored in `app.state.container` for request access
- All services use lazy initialization for optional dependencies
- Lock ensures thread-safe lazy loading
- Properties provide read-only access to internal services
- Helper methods break down initialization into focused steps
