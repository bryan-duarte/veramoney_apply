# Technical Design

## Architecture Decisions

### Agent Pattern: create_agent with Middleware

**Decision:** Use LangChain v1's `create_agent()` function with middleware stack

**Rationale:**
- `create_agent()` is the recommended LangChain v1 approach (deprecated: AgentExecutor, initialize_agent)
- Middleware provides clean separation of cross-cutting concerns
- Built-in support for tools, memory, and streaming
- LangGraph-based runtime with proper state management

**Architecture:**
```
HTTP Request
    │
    ▼
┌─────────────────────────────────────────────────┐
│ FastAPI Endpoint (chat_stream.py)               │
│ - Validate session_id                           │
│ - Get conversation from PostgreSQL              │
│ - Create agent with session context             │
└───────────────────┬─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│ Agent (create_agent)                            │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │ Middleware Stack                         │   │
│  │ 1. Request/Response Logging              │   │
│  │ 2. Tool Error Handler                    │   │
│  │ 3. Output Guardrails                     │   │
│  └─────────────────────────────────────────┘   │
│                    │                            │
│                    ▼                            │
│  ┌─────────────────────────────────────────┐   │
│  │ LLM (ChatOpenAI - gpt-5-mini)           │   │
│  │ - 30s timeout                           │   │
│  │ - Default temperature                    │   │
│  │ - No token limit                         │   │
│  └─────────────────────────────────────────┘   │
│                    │                            │
│                    ▼                            │
│  ┌─────────────────────────────────────────┐   │
│  │ Tools                                    │   │
│  │ - get_weather                            │   │
│  │ - get_stock_price                        │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│ PostgreSQL Memory Store                          │
│ - conversations table with JSONB messages       │
│ - thread_id = session_id                        │
│ - FIFO trimming at 20 messages                  │
└─────────────────────────────────────────────────┘
```

---

## Module Structure

```
src/agent/
├── __init__.py                    # Re-exports: create_conversational_agent, AgentDep
├── core/
│   ├── __init__.py                # Re-exports: create_conversational_agent
│   ├── conversational_agent.py    # Agent factory with middleware stack
│   └── prompts.py                 # System prompt definitions
├── memory/
│   ├── __init__.py                # Re-exports: PostgresMemoryStore
│   ├── postgres_store.py          # PostgreSQL memory implementation
│   └── checkpointer.py            # LangGraph checkpointer adapter
└── middleware/
    ├── __init__.py                # Re-exports: all middleware
    ├── tool_error_handler.py      # Tool error handling middleware
    ├── output_guardrails.py       # Output validation middleware
    └── logging_middleware.py      # Request/response logging
```

---

## Data Structures

### Chat Request (Modified)

```
ChatRequest:
  message: str           # 1-32000 chars
  session_id: str        # REQUIRED - UUID format for conversation threading
```

### Chat Response (Streaming SSE)

```
Event Types:
  - token: str           # Individual token chunk
  - tool_call: str       # Tool call notification
  - error: str           # Error message
  - done: None           # Stream completion signal
```

### PostgreSQL Schema

```
conversations:
  id: UUID               # Primary key
  session_id: UUID       # Unique, indexed
  messages: JSONB        # Array of message objects
  created_at: timestamp  # Session creation time
  updated_at: timestamp  # Last message time
```

### Message Object (JSONB)

```
Message:
  role: str              # "user" | "assistant" | "tool"
  content: str           # Message content
  tool_calls: list|None  # Tool call info if applicable
  tool_call_id: str|None # ID for tool responses
  timestamp: int         # Unix timestamp
```

---

## Integration Points

### API Layer Integration

**File:** `src/api/core/dependencies.py`

New dependency:
```
AgentDep = Annotated[Agent, Depends(get_agent)]
```

The `get_agent()` function:
1. Validates session_id from request
2. Creates/retrieves conversation from PostgreSQL
3. Instantiates agent with conversation context
4. Returns agent instance for request handling

### Tool Registration

**Tools to register:**
- `get_weather` from `src/tools/weather`
- `get_stock_price` from `src/tools/stock`

**Pattern:** Static tool registration at agent creation time (no dynamic tools needed)

### Memory Integration

**Store Implementation:**
- PostgreSQL-backed memory store
- Uses session_id as thread_id for LangGraph checkpointer
- FIFO message trimming when exceeding 20 messages

---

## Middleware Architecture

### 1. Request/Response Logging Middleware

**Purpose:** Log all model requests and responses for debugging

**Behavior:**
- Log request: messages, tool calls requested
- Log response: content, tool calls executed, timing
- Include session_id for correlation

### 2. Tool Error Handler Middleware

**Purpose:** Handle tool execution failures gracefully

**Behavior:**
- Catch tool execution exceptions
- Return natural error message to LLM: "I'm having trouble with [service name]..."
- Allow agent to formulate user-friendly response
- Log detailed error for debugging

### 3. Output Guardrails Middleware

**Purpose:** Verify outputs don't hallucinate tool results

**Behavior:**
- Extract tool results from conversation
- Verify response claims are grounded in actual tool outputs
- Flag potential hallucinations for review (log only, don't block)

---

## Streaming Architecture

### Server-Sent Events (SSE)

**Endpoint:** `/chat` (replacing existing)

**Response Format:**
```
event: token
data: {"content": "The"}

event: token
data: {"content": " weather"}

event: tool_call
data: {"tool": "get_weather", "args": {"city": "Montevideo"}}

event: token
data: {"content": " in Montevideo is 22°C"}

event: done
data: {}
```

### Batch Endpoint

**Endpoint:** `/chat/complete` (new)

**Purpose:** Non-streaming alternative for clients that prefer batch responses

**Response Format:** Same as current `ChatResponse`

---

## Dependencies

### Existing Dependencies (No Changes)

| Package | Version | Purpose |
|---------|---------|---------|
| langchain | >=1.2.10 | Agent framework |
| langchain-openai | >=1.1.10 | OpenAI integration |
| langchain-community | >=0.4.1 | Community tools |
| pydantic | >=2.12.5 | Data validation |
| pydantic-settings | >=2.13.0 | Configuration |
| httpx | >=0.25.0 | Async HTTP |
| asyncpg | - | PostgreSQL async driver (add) |

### New Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| asyncpg | >=0.30.0 | PostgreSQL async driver |
| sse-starlette | >=2.1.0 | SSE support for FastAPI |

---

## Configuration

### New Environment Variables

```
# PostgreSQL Memory Store
POSTGRES_MEMORY_HOST=postgres-memory
POSTGRES_MEMORY_PORT=5432
POSTGRES_MEMORY_USER=veramoney
POSTGRES_MEMORY_PASSWORD=veramoney_secret
POSTGRES_MEMORY_DB=veramoney_memory
```

### Settings Additions

```
class Settings:
    # ... existing settings ...

    # Memory Store
    postgres_memory_host: str
    postgres_memory_port: int
    postgres_memory_user: str
    postgres_memory_password: str
    postgres_memory_db: str

    # Agent Configuration
    agent_model: str = "gpt-5-mini"
    agent_timeout_seconds: float = 30.0
    agent_max_context_messages: int = 20
```

---

## Error Handling Strategy

### Tool Errors

1. **Weather Tool Unavailable:**
   - Middleware catches exception
   - Returns: "I'm having trouble accessing weather data right now"
   - Agent responds naturally to user

2. **Stock Tool Unavailable:**
   - Middleware catches exception
   - Returns: "I'm having trouble accessing stock market data right now"
   - Agent responds naturally to user

3. **Invalid Tool Input:**
   - Tool validation catches error
   - Returns structured error JSON
   - Agent sees error and asks for clarification

### LLM Errors

1. **Timeout:**
   - 30 second timeout triggers
   - Return 504 Gateway Timeout to client

2. **Rate Limit:**
   - OpenAI rate limit hit
   - Return 503 Service Unavailable with retry-after

3. **Invalid Response:**
   - Guardrails detect issue
   - Log warning, still return response (soft validation)

### Memory Errors

1. **PostgreSQL Unavailable:**
   - Connection error at startup
   - Fail fast with clear error message

2. **Session Not Found:**
   - Invalid session_id provided
   - Return 404 Not Found

---

## Performance Considerations

1. **Connection Pooling:**
   - PostgreSQL connection pool (min 5, max 20)
   - HTTP client reuse for tools (already implemented)

2. **Streaming Latency:**
   - First token target: < 500ms
   - Tool execution: parallel when possible

3. **Memory Efficiency:**
   - 20 message limit prevents unbounded growth
   - JSONB storage for efficient message operations

4. **Middleware Overhead:**
   - Logging: async, non-blocking
   - Guardrails: minimal regex checks only
