# Dataset Management Implementation

## Overview

Implement dataset collection for USER_OPENING_MESSAGES and STOCK_QUERIES in the API endpoints.

## Files to Modify

| File | Changes |
|------|---------|
| `src/api/endpoints/chat_complete.py` | Add dataset collection |
| `src/api/endpoints/chat_stream.py` | Add dataset collection |

---

## Opening Message Detection

### Logic

An "opening message" is the first user message in a session:

```
is_opening_message = (
    len(existing_messages) == 0  # No prior messages in memory
)
```

### Where to Check

In the endpoint, after getting memory store but before agent invocation:

```
memory_store = await get_memory_store(settings)
checkpointer = memory_store.get_checkpointer()

# Check if this is an opening message
existing_state = await checkpointer.aget_tuple(config)
existing_messages = existing_state.values.get("messages", []) if existing_state else []
is_opening_message = len(existing_messages) == 0
```

### What to Collect

For USER_OPENING_MESSAGES:

```
add_opening_message_to_dataset(
    client=langfuse_client,
    message=request.message,
    session_id=request.session_id,
    expected_tools=_infer_expected_tools(request.message),
    model=settings.agent_model,
)
```

### Tool Inference (Simple Heuristic)

```
def _infer_expected_tools(message: str) -> list[str]:
    message_lower = message.lower()

    expected = []

    if any(word in message_lower for word in ["weather", "temperature", "clima", "temperatura"]):
        expected.append("weather")

    if any(word in message_lower for word in ["stock", "price", "acción", "precio"]):
        expected.append("stock")

    if any(word in message_lower for word in ["vera", "fintech", "regulation", "bank"]):
        expected.append("knowledge")

    return expected if expected else ["unknown"]
```

---

## Stock Query Detection

### Logic

Detect when stock tool was used:

```
tool_calls_made = [...]  # Extracted from agent response
stock_tool_called = any(tc["tool"] == "stock_price" for tc in tool_calls_made)
```

### Where to Check

After agent invocation, when extracting tool calls:

```
tool_calls = _extract_tool_calls_from_messages(messages)

if stock_tool_called:
    add_stock_query_to_dataset(
        client=langfuse_client,
        query=request.message,
        ticker=_extract_ticker_from_tool_calls(tool_calls),
        session_id=request.session_id,
    )
```

### Ticker Extraction

```
def _extract_ticker_from_tool_calls(tool_calls: list) -> str:
    for tc in tool_calls:
        if tc["tool"] == "stock_price":
            return tc["input"].get("ticker", "UNKNOWN")
    return "UNKNOWN"
```

---

## Trace Metadata

### What to Set

After agent invocation, update trace with:

```
metadata = {
    "model": settings.agent_model,
    "tools": [tc["tool"] for tc in tool_calls],
    "rag_used": any(tc["tool"] == "knowledge" for tc in tool_calls),
}
```

### Where to Set

Use Langfuse SDK's trace update:

```
if langfuse_client:
    langfuse_client.update_current_trace(
        metadata=metadata,
        tags=[f"tool-{tc['tool']}" for tc in tool_calls],
    )
```

---

## chat_complete.py Changes

### Import Section

```
from src.observability import (
    get_langfuse_client,
    add_opening_message_to_dataset,
    add_stock_query_to_dataset,
)
```

### Function Body

1. Get Langfuse client early
2. Check if opening message, add to dataset
3. Get handler, pass to agent config
4. After invocation, add stock queries to dataset
5. Set trace metadata

---

## chat_stream.py Changes

### Same Pattern as chat_complete.py

The streaming endpoint follows the same pattern:

1. Get Langfuse client
2. Check opening message
3. Add to dataset
4. Stream with handler
5. After stream, add stock queries
6. Set metadata

### Streaming Consideration

Metadata and tags should be set after stream completes, not during streaming.

---

## Error Handling

All dataset operations are fire-and-forget:

```
try:
    add_opening_message_to_dataset(...)
except Exception:
    logger.warning("Failed to add opening message to dataset")
    # Continue execution
```

Never let dataset failures affect the response.
