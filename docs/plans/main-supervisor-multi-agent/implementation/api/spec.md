# API Layer Implementation

## Overview

Update API handlers and schemas to support the supervisor pattern, including worker details in responses and progress events in streaming.

## Files to Modify

| File | Changes |
|------|---------|
| `src/api/schemas.py` | Add WorkerToolCall, WorkerProgressEvent models |
| `src/api/handlers/base.py` | Use SupervisorFactory instead of AgentFactory |
| `src/api/handlers/chat_complete.py` | Extract worker details for response |
| `src/api/handlers/chat_stream.py` | Emit worker progress events |

## Implementation Guidelines

### schemas.py - New Models

```
WorkerToolCall Model:
  worker_name: str              # "weather", "stock", "knowledge"
  worker_request: str           # Request sent to worker
  worker_response: str          # Worker's final response
  internal_tool_calls: list[ToolCall]  # Tools called by worker
  duration_ms: float | None     # Worker execution time

ChatCompleteResponse Updates:
  response: str                 # Supervisor's synthesized response
  tool_calls: list[ToolCall]    # Workers invoked (supervisor level)
  worker_details: list[WorkerToolCall] | None  # Detailed worker info (NEW)

WorkerProgressEvent Model (for streaming):
  event_type: Literal["worker_started", "worker_tool_call", "worker_tool_result", "worker_completed"]
  worker_name: str
  data: dict  # Event-specific payload
```

### handlers/base.py - Factory Update

```
ChatHandlerBase Changes:

  __init__:
    - Replace agent_factory parameter with supervisor_factory
    - Update type hint: AgentFactory -> SupervisorFactory
    - Keep same dependency injection pattern

  _agent_factory attribute:
    - Rename to _supervisor_factory
    - Update all references

  is_opening_message(session_id):
    - No changes (uses checkpointer directly)

  infer_expected_tools(message):
    - Update to return worker names instead of tool names
    - Return ["weather", "stock", "knowledge"] instead of ["get_weather", ...]
```

### handlers/chat_complete.py - Response Extraction

```
ChatCompleteHandler.handle() Changes:

  1. Get supervisor from factory:
     supervisor, config, handler = await self._supervisor_factory.create_supervisor(session_id)

  2. Invoke supervisor:
     result = await supervisor.ainvoke({"messages": [...]}, config=config)

  3. Extract worker details:
     - Parse tool calls from supervisor response
     - Identify which are worker invocations (ask_*_agent)
     - Extract worker responses from tool results
     - Build WorkerToolCall objects

  4. Return enhanced response:
     return ChatCompleteResponse(
         response=final_content,
         tool_calls=supervisor_tool_calls,
         worker_details=worker_tool_calls,
     )

Worker Detail Extraction Logic:
  - Look for tool calls with names matching ask_*_agent pattern
  - Parse tool result content as worker response
  - Internal tool calls are NOT available (worker is black box)
  - Duration can be approximated from logging middleware timestamps
```

### handlers/chat_stream.py - Progress Events

```
ChatStreamHandler.handle() Changes:

  1. Get supervisor from factory:
     supervisor, config, handler = await self._supervisor_factory.create_supervisor(session_id)

  2. Stream with progress events:
     async for stream_mode, data in supervisor.astream(...):
         if stream_mode == "messages":
             # Handle tokens (existing logic)
             yield {"event": "token", "data": {...}}

             # Handle tool calls - detect worker invocations
             if token.tool_calls:
                 for tc in token.tool_calls:
                     if tc["name"].startswith("ask_"):
                         yield {
                             "event": "worker_started",
                             "data": {"worker": tc["name"], "request": tc["args"]}
                         }

         elif stream_mode == "updates":
             # Handle tool results - detect worker responses
             for source, update in data.items():
                 if source == "tools":
                     for msg in messages:
                         if isinstance(msg, ToolMessage):
                             if msg.name.startswith("ask_"):
                                 yield {
                                     "event": "worker_completed",
                                     "data": {
                                         "worker": msg.name,
                                         "response": msg.content[:200] + "..."  # Truncate for streaming
                                     }
                                 }

  3. Final event with full worker details:
     yield {
         "event": "worker_details",
         "data": {"workers": worker_summaries}
     }
```

## Dependencies

```
src/api/handlers/
├── depends on → src/agent/core/supervisor.py (SupervisorFactory)
├── depends on → src/api/schemas.py (WorkerToolCall, WorkerProgressEvent)
└── depends on → langchain_core.messages (HumanMessage, AIMessage, ToolMessage)
```

## Integration Notes

1. API endpoints remain unchanged (same routes)
2. Request schemas unchanged (ChatCompleteRequest, ChatStreamRequest)
3. Response schema is additive (new optional field)
4. Streaming adds new event types (backward compatible)
5. Error handling unchanged (middleware at supervisor level)
