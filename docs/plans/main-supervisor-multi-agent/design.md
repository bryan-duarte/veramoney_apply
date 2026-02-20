# Technical Design

## Architecture Decisions

### 1. Supervisor Pattern Selection

The **Supervisor Pattern (Tool-Wrapped Subagents)** was selected from four analyzed options:

| Pattern | Why Not Selected |
|---------|-----------------|
| Router Pattern (StateGraph) | Higher complexity, parallel execution not critical for 3 domains |
| State Machine Pattern | Sequential flows not needed; user queries are independent |
| Subagent Middleware | Requires external `deepagents` dependency |

**Supervisor Pattern Benefits:**
- Minimal code changes to existing structure
- Maintains async-first architecture
- Easy to test each worker independently
- Clear delegation chain for debugging

### 2. Hierarchical Agent Structure

```
SupervisorAgent (gpt-5-mini)
├── ask_weather_agent (Tool)
│   └── WeatherWorkerAgent (gpt-5-nano)
│       └── get_weather (Tool)
├── ask_stock_agent (Tool)
│   └── StockWorkerAgent (gpt-5-nano)
│       └── get_stock_price (Tool)
└── ask_knowledge_agent (Tool)
    └── KnowledgeWorkerAgent (gpt-5-nano)
        └── search_knowledge (Tool)
```

### 3. Data Flow

```
User Request
    │
    ▼
API Handler (ChatCompleteHandler or ChatStreamHandler)
    │
    ▼
SupervisorFactory.create_supervisor(session_id)
    │
    ▼
Supervisor Agent (with checkpointer, middleware, Langfuse)
    │
    ├──▶ ask_weather_agent("What's the weather in Miami?")
    │        │
    │        ▼
    │    Weather Worker Agent (logging only, no checkpointer)
    │        │
    │        ▼
    │    get_weather("Miami") → Weather data
    │        │
    │        ▼
    │    Worker response: "In Miami, it's currently 28°C..."
    │
    ├──▶ ask_stock_agent("What's AAPL price?")
    │        │
    │        ▼
    │    Similar flow...
    │
    └──▶ Supervisor synthesizes and returns final response
```

---

## Patterns & Conventions

### Existing Patterns to Maintain

1. **Async-First** - All worker methods use `async def` and `ainvoke()`
2. **Factory Pattern** - `SupervisorFactory` replaces `AgentFactory`
3. **Dependency Injection** - Workers receive dependencies via constructor
4. **Pydantic Schemas** - All inputs/outputs use typed models
5. **Named Boolean Conditions** - Guard clauses with semantic names
6. **No Comments** - Self-documenting code only
7. **Module-Level Constants** - UPPER_SNAKE_CASE for configuration

### New Patterns to Introduce

1. **Worker Base Class** - `BaseWorkerFactory` for shared worker creation logic
2. **Tool Wrapper Pattern** - Each worker wrapped as `@tool` decorated function
3. **Nested Langfuse Traces** - Workers create child traces with `trace_id` linkage
4. **Progress Event Schema** - Structured events for streaming worker progress

---

## Dependencies

### Current Dependencies (No Changes)

```toml
"langchain>=1.2.10"
"langchain-openai>=1.1.10"
"langchain-community>=0.4.1"
"langgraph-checkpoint-postgres>=3.0.4"
"langfuse>=3.14.3"
```

### No New Dependencies Required

The Supervisor Pattern is fully supported by existing LangChain v1's `create_agent` API and `@tool` decorator.

---

## Integration Points

### 1. API Layer → Supervisor Layer

**Before:**
```python
# ChatCompleteHandler
agent, config, handler = await self._agent_factory.create_agent(session_id)
result = await agent.ainvoke({"messages": [...]}, config=config)
```

**After:**
```python
# ChatCompleteHandler
supervisor, config, handler = await self._supervisor_factory.create_supervisor(session_id)
result = await supervisor.ainvoke({"messages": [...]}, config=config)
```

### 2. Supervisor → Workers

Workers are invoked via tool calling:

```python
@tool
def ask_weather_agent(request: str) -> str:
    """Route weather questions to the weather specialist."""
    result = weather_worker.invoke({"messages": [{"role": "user", "content": request}]})
    return result["messages"][-1].content
```

### 3. Workers → Tools

Each worker has a single tool:

```python
weather_worker = create_agent(
    model=ChatOpenAI(model="gpt-5-nano-2025-08-07"),
    tools=[get_weather],
    system_prompt=WEATHER_WORKER_PROMPT,
    middleware=[worker_logging_middleware],
)
```

### 4. Langfuse Integration

```python
# Supervisor creates main trace
supervisor_trace = langfuse_client.trace(
    id=session_id,
    name="supervisor",
    metadata={"model": "gpt-5-mini"}
)

# Worker creates nested trace
worker_trace = langfuse_client.trace(
    id=f"{session_id}-weather",
    name="weather-worker",
    metadata={"parent_trace": session_id}
)
```

---

## Data Structures

### API Response Schema

```python
class WorkerToolCall(BaseModel):
    worker_name: str  # "weather", "stock", "knowledge"
    worker_request: str  # Original request to worker
    worker_response: str  # Worker's final response
    internal_tool_calls: list[ToolCall]  # Tools called within worker

class SupervisorResponse(BaseModel):
    response: str  # Supervisor's synthesized response
    supervisor_tool_calls: list[ToolCall]  # Workers invoked
    worker_details: list[WorkerToolCall]  # Detailed worker info
```

### Progress Event Schema (Streaming)

```python
class WorkerProgressEvent(BaseModel):
    event_type: Literal["worker_started", "worker_tool_call", "worker_tool_result", "worker_completed"]
    worker_name: str
    data: dict  # Event-specific data
```

### Worker Configuration

```python
class WorkerConfig(BaseModel):
    name: str  # "weather", "stock", "knowledge"
    model: str = "gpt-5-nano-2025-08-07"
    tool_name: str  # "get_weather", "get_stock_price", "search_knowledge"
    prompt_name: str  # Langfuse prompt name
    description: str  # Tool description for supervisor
```

---

## Module Organization

```
src/agent/
├── core/
│   ├── factory.py          # → SupervisorFactory (refactored)
│   ├── prompts.py          # Supervisor + worker prompts
│   └── supervisor.py       # NEW: Supervisor-specific logic
├── workers/
│   ├── __init__.py         # NEW: Worker exports
│   ├── base.py             # NEW: BaseWorkerFactory
│   ├── weather_worker.py   # NEW: Weather worker + tool wrapper
│   ├── stock_worker.py     # NEW: Stock worker + tool wrapper
│   └── knowledge_worker.py # NEW: Knowledge worker + tool wrapper
├── middleware/
│   └── ... (existing)
└── memory/
    └── store.py            # (unchanged - supervisor only)
```

---

## Error Handling Strategy

### Worker Error Wrapping

```python
@tool
def ask_weather_agent(request: str) -> str:
    try:
        result = weather_worker.invoke(...)
        return result["messages"][-1].content
    except Exception as e:
        return f"I encountered an issue processing your weather request. Please try again."
```

### Supervisor Fallback

The supervisor's `tool_error_handler` middleware catches worker tool errors and provides user-friendly messages.

---

## Streaming Strategy

### Event Types

| Event | Description |
|-------|-------------|
| `token` | Streaming token from supervisor response |
| `worker_started` | Worker agent invocation began |
| `worker_tool_call` | Worker called its internal tool |
| `worker_tool_result` | Worker received tool result |
| `worker_completed` | Worker finished, response available |
| `tool_call` | Supervisor calling worker (existing) |
| `tool_result` | Supervisor received worker response (existing) |
| `done` | Stream complete |

### Client Handling

```javascript
// Frontend receives:
event: worker_started
data: {"worker": "weather", "request": "What's the weather in Miami?"}

event: worker_tool_call
data: {"worker": "weather", "tool": "get_weather", "args": {"city_name": "Miami"}}

event: worker_tool_result
data: {"worker": "weather", "result": "{\"temperature\": 28, ...}"}

event: worker_completed
data: {"worker": "weather", "response": "In Miami, it's currently 28°C..."}

event: token
data: {"content": "Based on the weather data..."}
```
