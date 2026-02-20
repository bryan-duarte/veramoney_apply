# Technical Design

## Architecture Decisions

### Prompt Structure (Chat-Type with Variables)

**CRITICAL CHANGE**: Use `type="chat"` instead of `type="text"` for proper LangChain integration.

```
┌─────────────────────────────────────────────────────────────────┐
│  Langfuse Prompt: vera-system-prompt                            │
├─────────────────────────────────────────────────────────────────┤
│  type: "chat"                                                   │
│  prompt: [                                                      │
│    {"role": "system", "content": "{{system_content}}"},        │
│    {"type": "placeholder", "name": "chat_history"},            │
│    {"role": "user", "content": "{{user_message}}"}             │
│  ]                                                              │
│  config: {model, temperature}                                   │
│  labels: ["production"]                                         │
│  variables: {                                                   │
│    current_date: "20 February, 26",                            │
│    model_name: "GPT-5-mini",                                   │
│    version: "1.0"                                              │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

#### Dynamic Variables

| Variable | Source | Format | Example |
|----------|--------|--------|---------|
| `current_date` | `datetime.now()` | `DD Month, YY` | "20 February, 26" |
| `model_name` | `settings.agent_model` | String | "GPT-5-mini" |
| `version` | Constant | String | "1.0" |

#### Placeholder Integration

| Placeholder | Purpose | Source |
|-------------|---------|--------|
| `chat_history` | Conversation memory | LangGraph checkpointer |

#### Prompt Template Structure

```xml
<temporal_context>
Today's date: {{current_date}}
</temporal_context>

<identity>
You are Vera AI v{{version}}, a specialized financial assistant...
Built on: {{model_name}}
</identity>

<!-- Rest of system prompt sections -->
```

### Trace Structure

```
┌─────────────────────────────────────────────────────────────────┐
│  Langfuse Trace (id = session_id)                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Span: veramoney-chat-request                                   │
│  ├── Metadata: {model, tools: [], rag_used: bool}              │
│  ├── Tags: [tool-weather, tool-stock, tool-knowledge]          │
│  │                                                              │
│  ├── Span: veramoney-llm-call                                   │
│  │   └── Token usage, latency, model version                   │
│  │                                                              │
│  ├── Span: veramoney-tool-weather                               │
│  │   ├── Input: {city_name, country_code}                      │
│  │   └── Output: WeatherOutput JSON                            │
│  │                                                              │
│  ├── Span: veramoney-tool-stock                                 │
│  │   ├── Input: {ticker}                                       │
│  │   └── Output: StockOutput JSON                              │
│  │                                                              │
│  └── Span: veramoney-rag-retrieval                              │
│      ├── Input: {query, document_type, k}                      │
│      ├── Span: veramoney-embedding-generation                   │
│      └── Output: {chunks: [], total_results}                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Integration Points

1. **API Layer** (`src/api/endpoints/`)
   - Create/update trace with session_id
   - Collect opening messages for dataset
   - Collect stock queries for dataset
   - Set trace metadata and tags

2. **Agent Layer** (`src/agent/core/`)
   - Pass CallbackHandler to create_agent()
   - Fetch system prompt from Langfuse
   - Fall back to code-based prompt

3. **Observability Layer** (`src/observability/`)
   - Client singleton with graceful degradation
   - Handler factory for CallbackHandler
   - Dataset service for lazy creation
   - Prompt service for sync logic

### CallbackHandler Flow

```
chat_complete.py / chat_stream.py
       │
       ├── get_langfuse_handler() ──► Creates CallbackHandler
       │                                    │
       ▼                                    ▼
create_conversational_agent()         Langfuse SDK
       │                                    │
       ├── config = {                      │
       │     "callbacks": [handler],       │
       │     "configurable": {...}         │
       │  }                                │
       │                                    │
       ▼                                    ▼
agent.ainvoke() ──────────────────► Auto-traces to Langfuse
```

---

## Patterns & Conventions

### Async-First (MANDATORY)

All Langfuse operations must be async:

- Use `langfuse` SDK's async methods where available
- Wrap synchronous SDK calls in `asyncio.to_thread()` if needed
- Never block the event loop

### Graceful Degradation Pattern

```
try:
    langfuse_operation()
except Exception:
    logger.warning("Langfuse operation failed: %s", exc_info=True)
    # Continue execution - never fail user request
```

### Singleton Pattern

Follow existing pattern from `MemoryStore`:

```
_langfuse_client_instance: LangfuseClient | None = None

def get_langfuse_client() -> LangfuseClient | None:
    global _langfuse_client_instance
    if _langfuse_client_instance is None and _is_configured():
        _langfuse_client_instance = LangfuseClient(...)
    return _langfuse_client_instance
```

### Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Trace | `veramoney-chat` | session_id as trace_id |
| LLM Span | `veramoney-llm-call` | Model invocation |
| Tool Span | `veramoney-tool-{name}` | veramoney-tool-weather |
| RAG Span | `veramoney-rag-retrieval` | Knowledge search |
| Dataset | `UPPER_SNAKE_CASE` | USER_OPENING_MESSAGES |

---

## Dependencies

### Existing (Already Installed)

| Package | Version | Purpose |
|---------|---------|---------|
| `langfuse` | >=3.14.3 | SDK for tracing |
| `langchain` | >=1.2.10 | CallbackHandler integration |

### No New Dependencies Required

The existing `langfuse` package includes:
- `langfuse.langchain.CallbackHandler` - LangChain integration
- `langfuse.client` - Direct API access
- Async support via background threads

---

## Integration Points

### 1. Application Startup (`src/api/app.py`)

```
lifespan():
    1. Initialize Langfuse client (if configured)
    2. Sync prompts from code to Langfuse (create if missing)
    3. Log connection status
    yield
    4. Flush pending traces
    5. Close client
```

### 2. Chat Endpoints (`src/api/endpoints/chat_*.py`)

```
chat_complete/chat_stream():
    1. Get or create trace (session_id = trace_id)
    2. Check if opening message → add to dataset
    3. Get CallbackHandler
    4. Invoke agent with handler in config
    5. Set trace metadata (model, tools, rag_used)
    6. Set trace tags based on tools used
    7. Add stock queries to dataset
```

### 3. Agent Creation (`src/agent/core/conversational_agent.py`)

```
create_conversational_agent():
    1. Get Langfuse CallbackHandler
    2. Fetch system prompt from Langfuse (or fallback to code)
    3. Add handler to config.callbacks
    4. Create agent with config
```

---

## Data Structures

### Prompt Variables Schema

```
PromptVariables:
    current_date: str        # Formatted as "DD Month, YY"
    model_name: str          # From settings.agent_model
    version: str             # "1.0"
    user_message: str        # The user's input
    chat_history: list       # From checkpointer (placeholder)
```

### Date Formatting

```
from datetime import datetime

def format_current_date() -> str:
    current = datetime.now()
    return current.strftime("%d %B, %y")
    # Example: "20 February, 26"
```

### LangfuseConfig (Internal)

```
LangfuseConfig:
    enabled: bool              # Computed from keys presence
    public_key: str | None
    secret_key: str | None
    host: str
    environment: str           # From app_stage
```

### DatasetItem Structure

**USER_OPENING_MESSAGES:**
```
{
    "input": {
        "message": str,           # User's opening message
        "session_id": str         # Session identifier
    },
    "expected_output": None,      # Not applicable
    "metadata": {
        "timestamp": str,         # ISO 8601
        "model": str,             # Model used
        "expected_tools": list    # Tools likely needed
    }
}
```

**STOCK_QUERIES:**
```
{
    "input": {
        "query": str,             # User's query about stock
        "ticker": str             # Extracted ticker
    },
    "expected_output": None,      # Manual evaluation
    "metadata": {
        "timestamp": str,
        "session_id": str
    }
}
```

---

## Error Handling

### Connection Failures

- Log warning, continue execution
- Mark client as unhealthy
- Retry on next request

### Authentication Errors

- Log error with sanitized message
- Disable client for session
- Continue without tracing

### API Rate Limits

- Log warning
- Continue without tracing
- No retry (SDK handles internally)

### Dataset Creation Failures

- Log warning
- Skip dataset collection for this request
- Continue with tracing

---

## Performance Considerations

### Background Flushing

- SDK handles background flush automatically
- No explicit flush() calls in request path
- Flush on application shutdown only

### Connection Pooling

- Langfuse SDK manages HTTP connections internally
- No additional pooling needed

### Memory Footprint

- Single client instance
- Handler created per request (lightweight)
- No trace data stored in memory (sent to SDK)

---

## Security

### API Key Handling

- Keys from environment variables only
- Never logged or exposed in traces
- Validated at startup (if configured)

### Sensitive Data

- User messages ARE traced (needed for debugging)
- API keys NOT traced
- No PII filtering (out of scope)

### Network Security

- Langfuse hosted on internal Docker network
- No external cloud exposure (self-hosted)
- HTTPS for production deployment

---

## Key Improvements from Analysis

### Chat-Type Prompts (vs Text-Type)

| Aspect | Text-Type (Before) | Chat-Type (After) |
|--------|-------------------|-------------------|
| Structure | Single string | Array of messages |
| LangChain | Manual parsing | `get_langchain_prompt()` |
| Placeholders | Not supported | `chat_history` placeholder |
| Variables | Not supported | `{{current_date}}`, etc. |
| Trace linking | Manual | Automatic via metadata |

### Dynamic Date Injection

The agent needs temporal context for accurate responses:

```
<temporal_context>
Today's date: 20 February, 26

Note: Stock prices and weather data are retrieved in real-time...
</temporal_context>
```

This enables:
- Understanding "today" references
- Contextualizing stock data timestamps
- Accurate weather date interpretation

### LangChain Integration Flow

```
Langfuse Chat Prompt
        │
        ▼
get_langchain_prompt()
        │
        ▼
ChatPromptTemplate
├── SystemMessage with {{variables}}
├── MessagesPlaceholder("chat_history")
└── HumanMessage("{{user_message}}")
        │
        ▼
compile(current_date=..., model_name=..., ...)
        │
        ▼
Rendered Messages for Agent
```
