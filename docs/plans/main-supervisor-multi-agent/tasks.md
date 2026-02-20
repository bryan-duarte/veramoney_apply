# Implementation Tasks

## Task Breakdown

### Phase 1: Worker Infrastructure

#### 1.1 Create Worker Module Structure
- [ ] Create `src/agent/workers/__init__.py` with module exports
- [ ] Create `src/agent/workers/base.py` with `BaseWorkerFactory` class
- [ ] Define `WorkerConfig` Pydantic model in base module
- [ ] Implement worker logging middleware for worker-level logging

#### 1.2 Weather Worker Agent
- [ ] Create `src/agent/workers/weather_worker.py`
- [ ] Define `WEATHER_WORKER_PROMPT` system prompt
- [ ] Implement `create_weather_worker()` factory function
- [ ] Create `ask_weather_agent` tool wrapper with `@tool` decorator
- [ ] Add error handling in tool wrapper

#### 1.3 Stock Worker Agent
- [ ] Create `src/agent/workers/stock_worker.py`
- [ ] Define `STOCK_WORKER_PROMPT` system prompt
- [ ] Implement `create_stock_worker()` factory function
- [ ] Create `ask_stock_agent` tool wrapper with `@tool` decorator
- [ ] Add error handling in tool wrapper

#### 1.4 Knowledge Worker Agent
- [ ] Create `src/agent/workers/knowledge_worker.py`
- [ ] Define `KNOWLEDGE_WORKER_PROMPT` system prompt
- [ ] Implement `create_knowledge_worker()` factory function
- [ ] Create `ask_knowledge_agent` tool wrapper with `@tool` decorator
- [ ] Add error handling in tool wrapper
- [ ] Inject `KnowledgeRetriever` dependency

---

### Phase 2: Supervisor Layer

#### 2.1 Supervisor Prompts
- [ ] Add `SUPERVISOR_SYSTEM_PROMPT` to `src/agent/core/prompts.py`
- [ ] Define supervisor prompt with specialist descriptions
- [ ] Include routing rules and multi-specialist handling

#### 2.2 Supervisor Factory
- [ ] Create `src/agent/core/supervisor.py` with `SupervisorFactory` class
- [ ] Import worker tools from workers module
- [ ] Build supervisor with all three worker tools
- [ ] Apply full middleware stack to supervisor
- [ ] Configure checkpointer for supervisor (PostgreSQL)
- [ ] Configure Langfuse callback handler

#### 2.3 Langfuse Worker Traces
- [ ] Modify worker creation to generate nested trace IDs
- [ ] Pass parent trace ID to worker Langfuse handlers
- [ ] Update `PromptManager` to handle worker prompt names

---

### Phase 3: API Layer Updates

#### 3.1 Response Schema Updates
- [ ] Add `WorkerToolCall` model to `src/api/schemas.py`
- [ ] Update `ChatCompleteResponse` to include `worker_details`
- [ ] Add `WorkerProgressEvent` model for streaming

#### 3.2 Handler Updates
- [ ] Update `ChatHandlerBase` to use `SupervisorFactory` instead of `AgentFactory`
- [ ] Update `ChatCompleteHandler.handle()` to extract worker details
- [ ] Update `ChatStreamHandler.handle()` to emit worker progress events
- [ ] Implement worker event parsing from supervisor stream

#### 3.3 Endpoint Updates
- [ ] Verify streaming endpoint emits new event types
- [ ] Update OpenAPI documentation with new response fields

---

### Phase 4: Observability Updates

#### 4.1 Prompt Management
- [ ] Add worker prompt definitions to `src/agent/core/prompts.py`
- [ ] Update `PromptManager.sync_to_langfuse()` to sync worker prompts
- [ ] Add `get_worker_prompt()` method to `PromptManager`
- [ ] Create Langfuse prompts: `vera-weather-worker`, `vera-stock-worker`, `vera-knowledge-worker`

#### 4.2 Trace Linking
- [ ] Implement trace ID generation for workers (format: `{session_id}-{worker_name}`)
- [ ] Add parent trace metadata to worker traces
- [ ] Verify trace hierarchy in Langfuse UI

---

### Phase 5: Configuration Updates

#### 5.1 Settings
- [ ] Add `worker_model` field to `Settings` class (default: `gpt-5-nano-2025-08-07`)
- [ ] Update `.env.example` with `WORKER_MODEL` variable
- [ ] Add `worker_timeout_seconds` field (default: 15)

#### 5.2 Constants
- [ ] Add worker name constants to `src/tools/constants.py`
- [ ] Define worker tool names: `ASK_WEATHER_AGENT`, `ASK_STOCK_AGENT`, `ASK_KNOWLEDGE_AGENT`

---

### Phase 6: Cleanup & Validation

#### 6.1 Remove Legacy Code
- [ ] Remove single-agent logic from `src/agent/core/factory.py`
- [ ] Clean up unused imports
- [ ] Update any remaining references to `AgentFactory`

#### 6.2 Validation
- [ ] Verify weather queries route to weather worker
- [ ] Verify stock queries route to stock worker
- [ ] Verify knowledge queries route to knowledge worker
- [ ] Verify multi-domain queries invoke multiple workers
- [ ] Verify streaming events include worker progress
- [ ] Verify Langfuse shows nested traces
- [ ] Verify error handling provides user-friendly messages

---

## Task Dependencies

```
Phase 1 (Workers)
    │
    ├── 1.1 Module Structure ──► 1.2, 1.3, 1.4 (can run in parallel)
    │
    └── 1.2, 1.3, 1.4 Workers ──► Phase 2

Phase 2 (Supervisor)
    │
    ├── 2.1 Prompts ──┐
    ├── 2.2 Factory ──┼──► Phase 3
    └── 2.3 Traces ───┘

Phase 3 (API) ──► Phase 4 (Observability) ──► Phase 5 (Config) ──► Phase 6 (Cleanup)
```

---

## Estimated Complexity

| Phase | Complexity | Files Changed |
|-------|------------|---------------|
| Phase 1: Workers | Medium | 5 new files |
| Phase 2: Supervisor | Medium | 2 new files, 1 modified |
| Phase 3: API | Medium | 4 modified files |
| Phase 4: Observability | Low | 2 modified files |
| Phase 5: Configuration | Low | 2 modified files |
| Phase 6: Cleanup | Low | 1 modified file |

**Total: 8 new files, 10 modified files**
