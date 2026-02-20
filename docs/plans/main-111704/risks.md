# Risks & Mitigations

## Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking LangChain agent integration | HIGH | Keep @tool decorator, keep middleware decorators, test agent creation thoroughly |
| Circular import dependencies | MEDIUM | ServiceContainer as single entry point, lazy initialization in getters |
| Async initialization race conditions | MEDIUM | Sequential initialization in ServiceContainer.initialize(), explicit ordering |
| State management across requests | MEDIUM | ServiceContainer stored in app.state, per-request handler instantiation |
| FastAPI dependency injection complexity | LOW | Simple get_container dependency, handler classes don't use FastAPI Depends |

## Integration Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking Chainlit SSE streaming | HIGH | Keep SSEClient class unchanged, only wrap handlers |
| ChromaDB connection issues after refactor | MEDIUM | Keep ChromaVectorStoreManager class, only wrap in RAGPipeline |
| Langfuse callback handler integration | MEDIUM | LangfuseManager returns same handler type, test tracing |
| PostgreSQL memory store connection | LOW | MemoryStore class unchanged, only instantiation changes |

## Edge Cases Identified

### 1. Lazy Initialization Race Condition

**Scenario**: Two concurrent requests trigger lazy initialization of same service.

**Handling**: ServiceContainer uses `asyncio.Lock` for lazy getters:
```python
async def get_memory_store(self) -> MemoryStore:
    async with self._lock:
        if self._memory_store is None:
            self._memory_store = MemoryStore(self._settings)
            await self._memory_store.initialize()
    return self._memory_store
```

### 2. Langfuse Unavailable

**Scenario**: Langfuse server not responding during initialization.

**Handling**: LangfuseManager returns None client, handlers check for None:
```python
langfuse_client = self.get_langfuse_client()
if langfuse_client is not None:
    # Use Langfuse features
```

### 3. RAG Pipeline Partial Failure

**Scenario**: Some documents fail to load, others succeed.

**Handling**: RAGPipeline tracks errors in status:
```python
status = pipeline.get_status()
if status.errors:
    logger.warning("RAG loaded with errors: %s", status.errors)
```

### 4. Memory Store Not Initialized

**Scenario**: Handler requests memory store before ServiceContainer.initialize().

**Handling**: Lazy getter initializes on demand, logs warning:
```python
if self._memory_store is None:
    logger.warning("Lazy initialization of memory store")
    await self._initialize_memory_store()
```

### 5. Missing Optional Dependencies

**Scenario**: Handler instantiated without optional langfuse_client.

**Handling**: Constructor uses None default, methods check:
```python
def __init__(self, langfuse_client: Langfuse | None = None):
    self._langfuse_client = langfuse_client  # May be None

def some_method(self):
    if self._langfuse_client:
        # Use it
```

## Backward Compatibility

| Component | Breaking Change | Mitigation |
|-----------|----------------|------------|
| `create_conversational_agent()` | Replaced by AgentFactory | AgentFactory.create_agent() has same signature |
| `initialize_rag_pipeline()` | Replaced by RAGPipeline | RAGPipeline.initialize() returns same tuple |
| `get_memory_store()` | Moved to ServiceContainer | ServiceContainer.get_memory_store() same signature |
| Module imports | __init__.py exports change | Keep old function exports as aliases temporarily |

## Rollback Strategy

If issues arise:

1. **Phase-level rollback**: Each phase is independent, can revert to previous phase
2. **Feature flags**: Wrap new classes in feature flags for gradual rollout
3. **Git branches**: Each phase on separate branch, merge only after testing
4. **Keep old code**: Don't delete old functions until new classes verified

## Testing Strategy

| Test Type | Coverage |
|-----------|----------|
| Unit tests | Each new class independently |
| Integration tests | ServiceContainer initialization |
| E2E tests | Full chat flow with new handlers |
| Performance tests | Ensure no regression in latency |
