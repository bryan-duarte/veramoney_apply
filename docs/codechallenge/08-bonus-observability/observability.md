# Bonus 3: Observability & Evaluation

> Status: TODO
> Priority: BONUS (Strongly Valued)

## Overview

Implement observability mechanisms for production monitoring.

## Requirements

- Log tool calls (which tool, input, output, duration)
- Log latency metrics (request/response time)
- Log token usage (input/output tokens per request)
- Optional: Integrate Langfuse telemetry
- Version prompts

## Tasks

| ID | Task | Status | Notes |
|----|------|--------|-------|
| B3.1 | Log tool calls | TODO | Which tool, input, output, duration |
| B3.2 | Log latency metrics | TODO | Request/response time |
| B3.3 | Log token usage | TODO | Input/output tokens per request |
| B3.4 | Integrate Langfuse | TODO | Telemetry platform |
| B3.5 | Version prompts | TODO | Track prompt changes |

## Implementation Location

```
src/observability/
├── __init__.py
├── langfuse_client.py      # Langfuse integration
├── metrics.py              # Custom metrics
└── logging_config.py       # Logging setup

src/agent/
├── prompts/
│   ├── v1_initial.py
│   ├── v2_refined.py
│   └── current.py          # Symlink to active version
```

## LangChain Approach

### Langfuse Integration

```python
from langfuse.langchain import CallbackHandler

langfuse_handler = CallbackHandler(
    public_key=settings.langfuse_public_key,
    secret_key=settings.langfuse_secret_key,
    host=settings.langfuse_host
)

# Use with agent
result = await agent.ainvoke(
    {"messages": [HumanMessage(content=message)]},
    config={"callbacks": [langfuse_handler]}
)
```

### Custom Metrics

```python
import time
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ToolCallMetrics:
    tool_name: str
    input: dict
    output: dict
    duration_ms: float
    success: bool

async def track_tool_call(tool_name: str, tool_input: dict, tool_func):
    start_time = time.time()
    try:
        result = await tool_func(tool_input)
        duration = (time.time() - start_time) * 1000
        metrics = ToolCallMetrics(
            tool_name=tool_name,
            input=tool_input,
            output=result,
            duration_ms=duration,
            success=True
        )
        logger.info(f"Tool call: {metrics}")
        return result
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"Tool call failed: {tool_name}", extra={
            "duration_ms": duration,
            "error": str(e)
        })
        raise
```

### Token Tracking

```python
from langchain.callbacks import get_openai_callback

async def track_tokens(agent, message: str):
    with get_openai_callback() as cb:
        result = await agent.ainvoke({"messages": [message]})

        logger.info(f"Token usage: input={cb.prompt_tokens}, output={cb.completion_tokens}, total={cb.total_tokens}, cost=${cb.total_cost}")

        return result, {
            "prompt_tokens": cb.prompt_tokens,
            "completion_tokens": cb.completion_tokens,
            "total_tokens": cb.total_tokens,
            "total_cost": cb.total_cost
        }
```

### Latency Tracking

```python
import time
from functools import wraps

def track_latency(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = (time.time() - start) * 1000
        logger.info(f"{func.__name__} took {duration:.2f}ms")
        return result
    return wrapper
```

## Prompt Versioning

```
src/agent/prompts/
├── v1_initial.py        # Initial prompt
├── v2_added_citations.py  # Added citation instructions
├── v3_refined_routing.py  # Better tool routing
└── current.py -> v3_refined_routing.py  # Active version
```

```python
# v3_refined_routing.py
SYSTEM_PROMPT = """
You are Vera, a helpful AI assistant for VeraMoney.

Version: 3.0
Last updated: 2024-01-15

Capabilities:
- Answer general questions
- Get weather information (use get_weather tool)
- Get stock prices (use get_stock_price tool)

Rules:
- Only use tools when explicitly asked about weather/stocks
- Never invent data - only use real tool results
- Be concise and accurate
- Cite sources: [Source: tool_name]

Changes from v2:
- Better tool routing logic
- Added citation format
"""
```

## Dashboard Metrics

| Metric | Description |
|--------|-------------|
| `request_count` | Total API requests |
| `request_latency_p50` | 50th percentile latency |
| `request_latency_p99` | 99th percentile latency |
| `tool_call_count` | Tool calls by type |
| `tool_latency_avg` | Average tool latency |
| `token_input_total` | Total input tokens |
| `token_output_total` | Total output tokens |
| `error_rate` | Error percentage |

## Dependencies

```toml
langfuse>=3.14.3
```
