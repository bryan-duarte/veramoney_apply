# Implementation Tasks

## Task Breakdown

### Phase 1: Infrastructure Setup

#### PostgreSQL Memory Service
- [ ] Add postgres-memory service to docker-compose.yml
- [ ] Configure environment variables for PostgreSQL connection
- [ ] Add asyncpg dependency to pyproject.toml
- [ ] Add sse-starlette dependency to pyproject.toml
- [ ] Update Settings class with PostgreSQL memory configuration

### Phase 2: Memory Layer

#### PostgreSQL Memory Store
- [ ] Create `src/agent/__init__.py` with re-exports
- [ ] Create `src/agent/memory/__init__.py` with re-exports
- [ ] Create `src/agent/memory/postgres_store.py`
  - Define `PostgresMemoryStore` class
  - Implement connection pool management
  - Implement `get_conversation(session_id)` method
  - Implement `save_message(session_id, message)` method
  - Implement `trim_messages(session_id, max_count)` method with FIFO
- [ ] Create `src/agent/memory/checkpointer.py`
  - Implement LangGraph checkpointer adapter using PostgresMemoryStore

### Phase 3: Middleware Layer

#### Middleware Foundation
- [ ] Create `src/agent/middleware/__init__.py` with re-exports

#### Tool Error Handler
- [ ] Create `src/agent/middleware/tool_error_handler.py`
  - Implement `@wrap_tool_call` decorator function
  - Catch tool exceptions and return natural error messages
  - Map service names to user-friendly messages
  - Log detailed errors for debugging

#### Output Guardrails
- [ ] Create `src/agent/middleware/output_guardrails.py`
  - Implement `@after_model` decorator function
  - Extract tool results from conversation state
  - Verify response claims are grounded in tool outputs
  - Log warnings for potential hallucinations

#### Request/Response Logging
- [ ] Create `src/agent/middleware/logging_middleware.py`
  - Implement `@wrap_model_call` decorator function
  - Log request: messages count, tool availability
  - Log response: content length, tool calls made, timing
  - Include session_id in all log entries

### Phase 4: Agent Core

#### System Prompts
- [ ] Create `src/agent/core/__init__.py` with re-exports
- [ ] Create `src/agent/core/prompts.py`
  - Define `VERA_FALLBACK_SYSTEM_PROMPT` with agent identity
  - Include capabilities: weather, stock prices, general knowledge
  - Include rules: no hallucination, use tools when needed, be professional
  - Include citation instructions: natural in-text references

#### Agent Factory
- [ ] Create `src/agent/core/conversational_agent.py`
  - Define `create_conversational_agent()` factory function
  - Initialize ChatOpenAI with model and timeout settings
  - Register tools: get_weather, get_stock_price
  - Configure middleware stack in correct order
  - Set system prompt
  - Return configured agent

### Phase 5: API Integration

#### Dependency Injection
- [ ] Update `src/api/core/dependencies.py`
  - Add `get_agent()` dependency function
  - Validate session_id is present
  - Initialize PostgresMemoryStore connection
  - Create agent with conversation context
  - Add `AgentDep` type annotation

#### Streaming Endpoint
- [ ] Create `src/api/endpoints/chat_stream.py`
  - Implement `POST /chat` with SSE response
  - Validate ChatRequest with required session_id
  - Stream token events from agent
  - Emit tool_call events when tools are invoked
  - Emit error events on failures
  - Emit done event on completion
  - Save messages to memory after completion

#### Batch Endpoint
- [ ] Create `src/api/endpoints/chat_complete.py`
  - Implement `POST /chat/complete` endpoint
  - Validate ChatRequest with required session_id
  - Invoke agent without streaming
  - Return ChatResponse with tool_calls tracking
  - Save messages to memory after completion

#### Router Updates
- [ ] Update `src/api/endpoints/__init__.py`
  - Remove old chat_router export
  - Add chat_stream_router export
  - Add chat_complete_router export
- [ ] Update `src/api/app.py`
  - Include chat_stream_router at /chat
  - Include chat_complete_router at /chat/complete

### Phase 6: Configuration Updates

#### Settings Updates
- [ ] Update `src/config/settings.py`
  - Add postgres_memory_host field
  - Add postgres_memory_port field
  - Add postgres_memory_user field
  - Add postgres_memory_password field
  - Add postgres_memory_db field
  - Add agent_model field with default
  - Add agent_timeout_seconds field with default
  - Add agent_max_context_messages field with default

#### Environment Template
- [ ] Update `.env.example`
  - Add PostgreSQL memory service variables
  - Add agent configuration variables

---

## Task Summary

| Phase | Tasks | Components |
|-------|-------|------------|
| Phase 1 | 5 | Infrastructure |
| Phase 2 | 5 | Memory Layer |
| Phase 3 | 7 | Middleware |
| Phase 4 | 6 | Agent Core |
| Phase 5 | 10 | API Integration |
| Phase 6 | 3 | Configuration |
| **Total** | **36** | - |

---

## Implementation Order

```
Phase 1 (Infrastructure)
    │
    ▼
Phase 2 (Memory) ─────────────────┐
    │                              │
    ▼                              ▼
Phase 3 (Middleware) ◄──────── Phase 4 (Agent Core)
    │                              │
    └──────────┬───────────────────┘
               │
               ▼
         Phase 5 (API)
               │
               ▼
         Phase 6 (Config)
```

**Critical Path:** Phase 1 → Phase 2 → Phase 4 → Phase 5 → Phase 6

**Parallelizable:** Phase 3 (Middleware) can be developed in parallel with Phase 4
