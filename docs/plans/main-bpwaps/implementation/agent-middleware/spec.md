# Agent Middleware Implementation Spec

## Overview

This module implements three middleware components for the conversational agent: logging, tool error handling, and output guardrails.

## Files to Create

```
src/agent/middleware/
├── __init__.py              # Re-exports
├── logging_middleware.py    # Request/response logging
├── tool_error_handler.py    # Tool error handling
└── output_guardrails.py     # Output validation
```

---

## Implementation Guidelines

### src/agent/middleware/__init__.py

**Purpose:** Module-level exports

**Exports:**
- `logging_middleware` from `.logging_middleware`
- `tool_error_handler` from `.tool_error_handler`
- `output_guardrails` from `.output_guardrails`

---

### src/agent/middleware/logging_middleware.py

**Purpose:** Log all model requests and responses for debugging

**Guidelines:**

1. Use `@wrap_model_call` decorator from `langchain.agents.middleware`

2. Function signature:
   - `logging_middleware(request: ModelRequest, handler) -> ModelResponse`

3. Request logging:
   - Log message count
   - Log available tools
   - Log timestamp
   - Include session_id from request state if available

4. Response logging:
   - Log response content length
   - Log tool calls made (if any)
   - Log duration in milliseconds
   - Include session_id for correlation

5. Use Python logging module with `getLogger(__name__)`

6. Log level: DEBUG for normal operations, INFO for tool calls

7. All functions must be async where handler is async

**Pseudocode:**
```
import logging
import time
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse

logger = logging.getLogger(__name__)

@wrap_model_call
async def logging_middleware(request: ModelRequest, handler) -> ModelResponse:
    session_id = request.state.get("session_id", "unknown")
    message_count = len(request.state.get("messages", []))
    tool_names = [t.name for t in request.tools]

    logger.debug(
        f"Request: session={session_id}, messages={message_count}, tools={tool_names}"
    )

    start_time = time.perf_counter()
    response = await handler(request)
    duration_ms = (time.perf_counter() - start_time) * 1000

    tool_calls = response.message.tool_calls if response.message else []
    content_length = len(response.message.content) if response.message else 0

    logger.debug(
        f"Response: session={session_id}, content_len={content_length}, "
        f"tool_calls={len(tool_calls)}, duration={duration_ms:.2f}ms"
    )

    return response
```

---

### src/agent/middleware/tool_error_handler.py

**Purpose:** Handle tool execution failures with natural error messages

**Guidelines:**

1. Use `@wrap_tool_call` decorator from `langchain.agents.middleware`

2. Function signature:
   - `tool_error_handler(request, handler) -> ToolMessage`

3. Service name mapping:
   - Map tool names to friendly service names
   - `get_weather` → "weather service"
   - `get_stock_price` → "stock market data service"

4. Error handling:
   - Wrap handler call in try/except
   - Catch all exceptions
   - Return ToolMessage with natural error message
   - Include service name in error message

5. Natural error message format:
   - "I'm having trouble accessing [service name] right now."
   - Let the agent formulate the final user-facing response

6. Detailed logging:
   - Log the full exception with traceback
   - Include tool name, arguments, and error details

**Pseudocode:**
```
import logging
from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage

logger = logging.getLogger(__name__)

SERVICE_NAMES = {
    "get_weather": "weather data",
    "get_stock_price": "stock market data"
}

@wrap_tool_call
async def tool_error_handler(request, handler) -> ToolMessage:
    tool_name = request.tool_call["name"]
    service_name = SERVICE_NAMES.get(tool_name, tool_name)

    try:
        return await handler(request)
    except Exception as e:
        logger.exception(
            f"Tool error: tool={tool_name}, args={request.tool_call['args']}, error={e}"
        )
        return ToolMessage(
            content=f"I'm having trouble accessing {service_name} right now. Please try again.",
            tool_call_id=request.tool_call["id"]
        )
```

---

### src/agent/middleware/output_guardrails.py

**Purpose:** Verify outputs don't hallucinate tool results

**Guidelines:**

1. Use `@after_model` decorator from `langchain.agents.middleware`

2. Function signature:
   - `output_guardrails(state: AgentState, response: ModelResponse) -> None`

3. Verification steps:
   - Extract tool results from conversation state
   - Check if response makes claims about tool data
   - Verify claims are grounded in actual tool results

4. Soft validation:
   - Log warning if potential hallucination detected
   - Do NOT block or modify the response
   - Allow response to proceed

5. Detection approach:
   - Look for weather-related terms if weather tool was called
   - Look for stock-related terms if stock tool was called
   - Check if specific data (temperatures, prices) matches tool results

6. Keep implementation simple - perfect detection is not required

7. This is a safety net, not a primary defense

**Pseudocode:**
```
import logging
from langchain.agents.middleware import after_model, AgentState, ModelResponse

logger = logging.getLogger(__name__)

@after_model
async def output_guardrails(state: AgentState, response: ModelResponse) -> None:
    if not response.message or not response.message.content:
        return

    messages = state.get("messages", [])
    tool_results = _extract_tool_results(messages)
    response_content = response.message.content.lower()

    for tool_name, result in tool_results.items():
        if tool_name == "get_weather":
            _check_weather_hallucination(response_content, result)
        elif tool_name == "get_stock_price":
            _check_stock_hallucination(response_content, result)

def _extract_tool_results(messages: list) -> dict:
    results = {}
    for msg in messages:
        if hasattr(msg, "name") and msg.name in ["get_weather", "get_stock_price"]:
            results[msg.name] = msg.content
    return results

def _check_weather_hallucination(content: str, tool_result: str) -> None:
    if "weather" not in content:
        return

    expected_temp = _extract_temperature(tool_result)
    if expected_temp and str(expected_temp) not in content:
        logger.warning(
            f"Potential weather hallucination: expected temp {expected_temp} "
            f"not found in response"
        )

def _check_stock_hallucination(content: str, tool_result: str) -> None:
    if "stock" not in content and "price" not in content:
        return

    expected_price = _extract_price(tool_result)
    if expected_price and str(expected_price) not in content:
        logger.warning(
            f"Potential stock hallucination: expected price {expected_price} "
            f"not found in response"
        )

def _extract_temperature(tool_result: str) -> float | None:
    # Parse temperature from JSON tool result
    pass

def _extract_price(tool_result: str) -> float | None:
    # Parse price from JSON tool result
    pass
```

---

## Middleware Execution Order

```
Request Flow:
1. logging_middleware (logs incoming request)
2. [Model processes]
3. tool_error_handler (catches tool errors)
4. [Tools execute]
5. output_guardrails (validates response)
6. logging_middleware (logs outgoing response)
```

**Order in middleware list:**
```
middleware = [
    logging_middleware,      # Outermost - wraps everything
    tool_error_handler,      # Catches tool errors
    output_guardrails,       # Validates after model
]
```

---

## Dependencies

- `langchain.agents.middleware` - Decorators and types
- `langchain.messages` - Message types
- `logging` - Standard library
- `time` - Timing utilities

---

## Integration Notes

1. Middleware is applied in order - outermost first
2. Each middleware should be stateless
3. Session_id should be passed via request state
4. Logging should not impact performance (use DEBUG level)
5. Guardrails are soft validation - never block
