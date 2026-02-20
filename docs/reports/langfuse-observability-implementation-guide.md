# Langfuse v3 Observability Implementation Guide

> *"If you can't observe it, did it even happen? Welcome to the Heisenberg Uncertainty Principle of LLM applications."*
> — **El Barto**

## Executive Summary

This report provides a comprehensive implementation guide for integrating Langfuse v3 observability into the VeraMoney Apply codebase using the `@observe` decorator and LangChain CallbackHandler. The implementation addresses all five bonus tasks (B3.1-B3.5) with minimal code changes and graceful degradation when credentials are unavailable.

---

## 1. Requirements Analysis

### Source: `docs/codechallenge/08-bonus-observability/observability.md`

| ID | Task | Current State | Implementation Strategy |
|----|------|---------------|------------------------|
| B3.1 | Log tool calls (tool, input, output, duration) | Partial (count only) | `@observe(as_type="span")` on tools + CallbackHandler |
| B3.2 | Log latency metrics | Partial (total only) | Automatic via `@observe` + nested spans |
| B3.3 | Log token usage | NOT captured | Automatic via LangChain CallbackHandler |
| B3.4 | Integrate Langfuse | Config exists, no integration | CallbackHandler + `@observe` decorators |
| B3.5 | Version prompts | NOT implemented | Langfuse Prompt CMS + `get_prompt()` |

---

## 2. Architecture Overview

### Current Data Flow

```
Client Request
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│  FastAPI Endpoints                                           │
│  src/api/endpoints/chat_stream.py::_generate_stream()       │
│  src/api/endpoints/chat_complete.py::chat_complete()        │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│  Agent Factory                                               │
│  src/agent/core/conversational_agent.py::create_agent()     │
│  - ChatOpenAI model                                          │
│  - Tools: [get_weather, get_stock_price]                    │
│  - Middleware: [logging, error_handler, guardrails]         │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│  Tool Execution                                              │
│  src/tools/weather/tool.py::get_weather()                   │
│  src/tools/stock/tool.py::get_stock_price()                 │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│  External APIs                                               │
│  - OpenAI (LLM)                                              │
│  - OpenWeatherMap (weather data)                            │
│  - Finnhub (stock data)                                      │
└─────────────────────────────────────────────────────────────┘
```

### Target Architecture with Langfuse

```
Client Request
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│  @observe(as_type="trace")  ← NEW: Root trace entry point    │
│  FastAPI Endpoints                                           │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│  CallbackHandler (config["callbacks"])  ← NEW                │
│  Agent Factory                                               │
│  - Automatic token tracking                                  │
│  - Automatic latency tracking                                │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│  @observe(as_type="span")  ← NEW: Tool spans                 │
│  Tool Execution                                              │
│  - Captures: input, output, duration, errors                │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│  Langfuse Server (localhost:3003)                            │
│  - Traces, Spans, Generations                               │
│  - Token usage dashboards                                    │
│  - Prompt version management                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Implementation Components

### 3.1 Langfuse Client Module

**File:** `src/observability/langfuse_client.py`

```python
from langfuse import Langfuse
from src.config import Settings

_langfuse_client: Langfuse | None = None


def get_langfuse_client() -> Langfuse | None:
    global _langfuse_client

    if _langfuse_client is None:
        from src.config import get_settings
        settings = get_settings()

        if not settings.langfuse_public_key or not settings.langfuse_secret_key:
            return None

        _langfuse_client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )

    return _langfuse_client


def is_langfuse_configured() -> bool:
    return get_langfuse_client() is not None
```

### 3.2 Callback Handler Factory

**File:** `src/observability/callbacks.py`

```python
from langfuse.callback import CallbackHandler
from src.config import Settings


def create_langfuse_callback(
    settings: Settings,
    session_id: str,
    trace_id: str | None = None,
    user_id: str | None = None,
) -> CallbackHandler | None:
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return None

    import uuid
    trace_id = trace_id or str(uuid.uuid4())

    return CallbackHandler(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
        session_id=session_id,
        trace_id=trace_id,
        user_id=user_id,
        tags=[settings.app_stage.value],
        metadata={"environment": settings.app_stage.value},
    )
```

### 3.3 Tool Decoration Pattern

**File:** `src/tools/weather/tool.py` (modified)

```python
from langfuse.decorators import observe
from langchain_core.tools import tool

from src.tools.weather.client import OpenWeatherClient
from src.tools.weather.schemas import WeatherInput, WeatherOutput


@observe(as_type="span", name="weather-tool")
@tool(args_schema=WeatherInput)
async def get_weather(city_name: str, country_code: str | None = None) -> str:
    client = OpenWeatherClient()
    weather_data = await client.get_current_weather(city_name, country_code)
    output = WeatherOutput.from_api_response(weather_data)
    return output.model_dump_json()
```

**File:** `src/tools/stock/tool.py` (modified)

```python
from langfuse.decorators import observe
from langchain_core.tools import tool

from src.tools.stock.client import FinnhubClient
from src.tools.stock.schemas import StockInput, StockOutput


@observe(as_type="span", name="stock-tool")
@tool(args_schema=StockInput)
async def get_stock_price(ticker: str) -> str:
    client = FinnhubClient()
    stock_data = await client.get_quote(ticker)
    output = StockOutput.from_api_response(ticker, stock_data)
    return output.model_dump_json()
```

### 3.4 Agent Factory Enhancement

**File:** `src/agent/core/conversational_agent.py` (modified)

```python
import logging
from typing import Any

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from src.agent.core.prompts import VERA_FALLBACK_SYSTEM_PROMPT
from src.agent.memory.store import MemoryStore
from src.agent.middleware import (
    logging_middleware,
    output_guardrails,
    tool_error_handler,
)
from src.config import Settings
from src.observability.callbacks import create_langfuse_callback
from src.tools.stock import get_stock_price
from src.tools.weather import get_weather


logger = logging.getLogger(__name__)


async def create_conversational_agent(
    settings: Settings,
    memory_store: MemoryStore,
    session_id: str,
    trace_id: str | None = None,
    user_id: str | None = None,
) -> tuple[Any, dict]:
    model = ChatOpenAI(
        model=settings.agent_model,
        timeout=settings.agent_timeout_seconds,
        api_key=settings.openai_api_key,
    )

    tools = [get_weather, get_stock_price]

    middleware_stack = [
        logging_middleware,
        tool_error_handler,
        output_guardrails,
    ]

    checkpointer = memory_store.get_checkpointer()

    langfuse_callback = create_langfuse_callback(
        settings=settings,
        session_id=session_id,
        trace_id=trace_id,
        user_id=user_id,
    )

    callbacks = [langfuse_callback] if langfuse_callback else []

    config = {
        "configurable": {
            "thread_id": session_id,
        },
        "callbacks": callbacks,
    }

    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=VERA_FALLBACK_SYSTEM_PROMPT,
        middleware=middleware_stack,
        checkpointer=checkpointer,
    )

    logger.debug(
        "created_agent session=%s model=%s tools=%s langfuse=%s",
        session_id,
        settings.agent_model,
        [tool.name for tool in tools],
        "enabled" if langfuse_callback else "disabled",
    )

    return agent, config
```

### 3.5 Endpoint Integration

**File:** `src/api/endpoints/chat_complete.py` (modified)

```python
from langfuse.decorators import observe
import uuid

@observe(as_type="trace", name="chat-complete-request")
async def chat_complete(
    api_key: APIKeyDep,
    settings: SettingsDep,
    request: ChatCompleteRequest,
) -> ChatCompleteResponse:
    session_id = request.session_id or str(uuid.uuid4())
    trace_id = str(uuid.uuid4())

    agent, config = await create_conversational_agent(
        settings=settings,
        memory_store=memory_store,
        session_id=session_id,
        trace_id=trace_id,
    )

    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": request.message}]},
        config=config,
    )

    return ChatCompleteResponse(
        response=result["messages"][-1].content,
        session_id=session_id,
        trace_id=trace_id,
    )
```

### 3.6 Prompt Versioning Integration

**File:** `src/agent/core/prompts.py` (modified)

```python
from langfuse import get_client
from src.observability.langfuse_client import get_langfuse_client

VERA_FALLBACK_SYSTEM_PROMPT_FALLBACK = """You are Vera, a helpful AI assistant for VeraMoney.

Capabilities:
- Answer general questions
- Get weather information (use get_weather tool)
- Get stock prices (use get_stock_price tool)

Rules:
- Only use tools when explicitly asked about weather/stocks
- Never invent data - only use real tool results
- Be concise and accurate
"""


def get_system_prompt() -> str:
    langfuse = get_langfuse_client()

    if langfuse is None:
        return VERA_FALLBACK_SYSTEM_PROMPT_FALLBACK

    try:
        prompt = langfuse.get_prompt(
            name="vera-system-prompt",
            label="production",
            fallback=VERA_FALLBACK_SYSTEM_PROMPT_FALLBACK,
        )
        return prompt.prompt
    except Exception:
        return VERA_FALLBACK_SYSTEM_PROMPT_FALLBACK


VERA_FALLBACK_SYSTEM_PROMPT = get_system_prompt()
```

---

## 4. `@observe` Decorator Reference

### Import Path

```python
from langfuse.decorators import observe
```

### Full Signature

```python
@observe(
    as_type: str = "span",       # "trace" | "span" | "generation"
    name: str | None = None,      # Custom name (default: function name)
    capture_input: bool = True,   # Capture function arguments
    capture_output: bool = True,  # Capture return value
    metadata: dict | None = None, # Custom metadata
    tags: list[str] | None = None,# Tags for filtering
    level: str | None = None,     # "DEBUG" | "DEFAULT" | "WARNING" | "ERROR"
)
```

### Observable Types

| Type | Purpose | Usage Location |
|------|---------|----------------|
| `trace` | Root container for request | API endpoints, main orchestration |
| `span` | General operations | Tool execution, HTTP calls, DB queries |
| `generation` | LLM API calls | Direct OpenAI calls, custom LLM wrappers |

### Runtime Updates

```python
from langfuse import get_client
from langfuse.decorators import observe, langfuse_context

langfuse = get_client()

@observe(as_type="generation")
async def llm_call(prompt: str) -> str:
    langfuse_prompt = langfuse.get_prompt("assistant-prompt")

    langfuse.update_current_generation(
        model="gpt-4o-mini",
        model_parameters={"temperature": 0.7, "max_tokens": 1000},
        prompt=langfuse_prompt,
    )

    response = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    langfuse.update_current_generation(
        output=response.content,
        usage={
            "input": response.usage.prompt_tokens,
            "output": response.usage.completion_tokens,
        },
    )

    return response.content
```

---

## 5. Metrics Captured

### Automatic via CallbackHandler

| Metric | Source | Description |
|--------|--------|-------------|
| `prompt_tokens` | OpenAI response | Input token count |
| `completion_tokens` | OpenAI response | Output token count |
| `total_tokens` | OpenAI response | Total tokens used |
| `llm_latency_ms` | Wrapper timing | Time for LLM API call |
| `tool_name` | LangChain tool | Which tool was invoked |
| `tool_input` | LangChain args | Tool arguments |
| `tool_output` | LangChain result | Tool return value |
| `tool_latency_ms` | Wrapper timing | Time for tool execution |

### Automatic via `@observe` Decorator

| Metric | Captured | Description |
|--------|----------|-------------|
| `function_input` | Yes | All function arguments |
| `function_output` | Yes | Return value |
| `start_time` | Yes | ISO timestamp |
| `end_time` | Yes | ISO timestamp |
| `duration_ms` | Computed | End - start |
| `level` | On error | ERROR if exception raised |
| `status_message` | On error | Exception message |

---

## 6. Trace Hierarchy Example

```
Trace: chat-complete-request (trace_id: abc123)
│
├── Span: weather-tool
│   ├── Input: {"city_name": "Montevideo"}
│   ├── Output: {"temperature": "22°C", "conditions": "Partly cloudy"}
│   └── Duration: 342ms
│
├── Span: stock-tool
│   ├── Input: {"ticker": "AAPL"}
│   ├── Output: {"price": 178.52, "currency": "USD"}
│   └── Duration: 156ms
│
└── Generation: ChatOpenAI
    ├── Model: gpt-4o-mini
    ├── Prompt Tokens: 124
    ├── Completion Tokens: 87
    └── Duration: 1.2s
```

---

## 7. Dashboard Metrics

| Metric | Description | Langfuse View |
|--------|-------------|---------------|
| `request_count` | Total API requests | Traces list |
| `request_latency_p50` | 50th percentile latency | Trace duration histogram |
| `request_latency_p99` | 99th percentile latency | Trace duration histogram |
| `tool_call_count` | Tool calls by type | Observations filter |
| `tool_latency_avg` | Average tool latency | Span duration stats |
| `token_input_total` | Total input tokens | Usage dashboard |
| `token_output_total` | Total output tokens | Usage dashboard |
| `error_rate` | Error percentage | Trace level filter |

---

## 8. Graceful Degradation Pattern

The implementation ensures the application works without Langfuse credentials:

```python
def create_langfuse_callback(...) -> CallbackHandler | None:
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return None  # Graceful degradation

    return CallbackHandler(...)


# Usage
callbacks = [langfuse_callback] if langfuse_callback else []
config["callbacks"] = callbacks
```

**Behavior:**
- No credentials: Application runs normally, no tracing
- With credentials: Full observability with no code changes

---

## 9. Environment Configuration

**File:** `.env`

```bash
# Required for observability
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3003
```

**File:** `docker-compose.yml` (already configured)

```yaml
services:
  langfuse-server:
    image: langfuse/langfuse:latest
    ports:
      - "3003:3000"
    environment:
      - DATABASE_URL=postgresql://...
      - CLICKHOUSE_URL=http://clickhouse:8123
      # ... other config
```

---

## 10. Implementation Checklist

### Phase 1: Core Integration

- [ ] Create `src/observability/__init__.py` with exports
- [ ] Create `src/observability/langfuse_client.py`
- [ ] Create `src/observability/callbacks.py`
- [ ] Test Langfuse client initialization

### Phase 2: Agent Integration

- [ ] Modify `create_conversational_agent()` to accept callback handler
- [ ] Add callback to `config["callbacks"]`
- [ ] Test with running Langfuse stack

### Phase 3: Tool Decoration

- [ ] Add `@observe(as_type="span")` to `get_weather()`
- [ ] Add `@observe(as_type="span")` to `get_stock_price()`
- [ ] Verify tool spans appear in Langfuse UI

### Phase 4: Endpoint Decoration

- [ ] Add `@observe(as_type="trace")` to `chat_complete()`
- [ ] Add `@observe(as_type="trace")` to `_generate_stream()`
- [ ] Verify trace hierarchy in Langfuse UI

### Phase 5: Prompt Versioning

- [ ] Create `vera-system-prompt` in Langfuse UI
- [ ] Modify `prompts.py` to fetch from Langfuse
- [ ] Test prompt version switching

### Phase 6: Verification

- [ ] Verify token usage appears in dashboard
- [ ] Verify latency metrics are captured
- [ ] Verify tool calls are logged with input/output
- [ ] Test graceful degradation (no credentials)

---

## 11. Key Findings

1. **CallbackHandler provides automatic instrumentation** - No manual token counting needed; LangChain callback captures all LLM metrics automatically.

2. **`@observe` decorator creates hierarchical traces** - Nested decorated functions automatically create parent-child relationships.

3. **Graceful degradation is critical** - The application must function without Langfuse credentials for development/testing.

4. **Session ID doubles as Langfuse session_id** - The existing `session_id` (UUID) can be used directly for trace grouping.

5. **Middleware timing is redundant** - With CallbackHandler, the `logging_middleware` timing becomes supplementary; Langfuse captures more detailed timing.

6. **V3 requires ClickHouse** - Self-hosted deployments need the full stack (PostgreSQL, ClickHouse, Redis, MinIO).

---

## 12. Recommendations

### Primary Recommendation

Implement Langfuse integration using the **CallbackHandler-first** approach:

1. Start with CallbackHandler for automatic LLM tracing
2. Add `@observe` decorators to tools for granular visibility
3. Use Langfuse Prompt CMS for version management

This approach provides 80% of the value with 20% of the code changes.

### Alternative Approaches

| Approach | Pros | Cons |
|----------|------|------|
| **CallbackHandler only** | Minimal code changes, automatic capture | Less granularity for custom operations |
| **`@observe` decorators only** | Full control over trace structure | Manual token tracking required |
| **Hybrid (recommended)** | Best of both worlds | Slightly more complex |

### Risk Assessment

| Risk | Mitigation |
|------|------------|
| Langfuse server unavailable | Graceful degradation pattern |
| Performance overhead | Async client, batch flushing |
| ClickHouse resource usage | Docker resource limits |
| Trace data volume | Retention policies, sampling |

---

## 13. Sources

| Source | URL/Path | Credibility |
|--------|----------|-------------|
| Project Observability Requirements | `docs/codechallenge/08-bonus-observability/observability.md` | Primary |
| Langfuse Python SDK v3 | https://langfuse.com/docs/sdk/python/decorators | Official |
| Langfuse LangChain Integration | https://langfuse.com/docs/integrations/langchain | Official |
| Langfuse Prompt CMS | https://langfuse.com/docs/prompts/get-started | Official |
| Project Settings | `src/config/settings.py` | Primary |
| Conversational Agent | `src/agent/core/conversational_agent.py` | Primary |
| Chat Complete Endpoint | `src/api/endpoints/chat_complete.py` | Primary |
| Langfuse Skill Documentation | `.claude/skills/langfuse_prompt_versioning/SKILL.md` | Project |

---

*Report generated by: El Barto*
*Date: 2026-02-19*
