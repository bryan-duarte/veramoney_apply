# API Integration Implementation Spec

## Overview

This module implements the streaming and batch chat endpoints, replacing the existing placeholder endpoint with SSE streaming.

## Files to Create/Modify

```
src/api/
├── core/
│   └── dependencies.py    # MODIFY - Add AgentDep
└── endpoints/
    ├── chat_stream.py     # CREATE - Streaming endpoint (SSE)
    ├── chat_complete.py   # CREATE - Batch endpoint
    ├── chat.py            # DELETE or archive - Replace with streaming
    └── __init__.py        # MODIFY - Update exports
```

---

## Implementation Guidelines

### src/api/core/dependencies.py (MODIFY)

**Purpose:** Add agent dependency injection

**Additions:**

1. Import agent components:
   - `create_conversational_agent` from `src.agent.core`
   - `PostgresMemoryStore` from `src.agent.memory`

2. Create memory store singleton:
   - Initialize at module load or in lifespan
   - Use settings for connection configuration

3. Add `get_agent()` dependency function:
   - Validate session_id is provided
   - Get or create memory store
   - Create agent with session context
   - Return agent instance

4. Define `AgentDep` type alias:
   - `AgentDep = Annotated[Agent, Depends(get_agent)]`

**Pseudocode:**
```
from typing import Annotated
from fastapi import Depends, HTTPException
from src.agent.core import create_conversational_agent
from src.agent.memory import PostgresMemoryStore
from src.config import settings

_memory_store: PostgresMemoryStore | None = None

async def get_memory_store() -> PostgresMemoryStore:
    global _memory_store
    if _memory_store is None:
        _memory_store = PostgresMemoryStore(settings)
        await _memory_store.initialize()
    return _memory_store

async def get_agent(
    session_id: str = Query(..., description="Session ID for conversation"),
    memory_store: PostgresMemoryStore = Depends(get_memory_store)
):
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    agent = await create_conversational_agent(session_id, memory_store)
    return agent

AgentDep = Annotated[Agent, Depends(get_agent)]
```

---

### src/api/endpoints/chat_stream.py (CREATE)

**Purpose:** Streaming chat endpoint using Server-Sent Events

**Guidelines:**

1. Create router with prefix `/chat` and tag `chat`

2. Import SSE utilities:
   - `EventSourceResponse` from `sse-starlette`

3. Define endpoint `POST /chat`:
   - Accept `ChatRequest` body
   - Require `session_id` in request body
   - Return `EventSourceResponse`

4. Stream event types:
   - `token` - Individual token chunks
   - `tool_call` - Tool execution notification
   - `error` - Error message
   - `done` - Stream completion

5. Event format:
   ```
   event: token
   data: {"content": "The weather"}

   event: tool_call
   data: {"tool": "get_weather", "args": {"city": "Montevideo"}}

   event: done
   data: {}
   ```

6. Implementation:
   - Get agent from dependency
   - Invoke agent with `stream()` method
   - Iterate over stream events
   - Yield SSE events
   - Save final messages to memory

7. Error handling:
   - Catch exceptions during streaming
   - Yield error event
   - Close stream gracefully

8. All functions must be async

**Pseudocode:**
```
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sse_starlette import EventSourceResponse
from src.agent.core import create_conversational_agent
from src.agent.memory import PostgresMemoryStore
from src.config import SettingsDep

router = APIRouter()

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=32000)
    session_id: str = Field(description="UUID session identifier")

@router.post("")
async def chat_stream(
    request: ChatRequest,
    settings: SettingsDep
) -> EventSourceResponse:
    return EventSourceResponse(
        _generate_stream(request.message, request.session_id, settings)
    )

async def _generate_stream(message: str, session_id: str, settings):
    try:
        memory_store = await _get_memory_store(settings)
        agent = await create_conversational_agent(session_id, memory_store)

        conversation = await memory_store.get_conversation(session_id)
        conversation.append({"role": "user", "content": message})

        async for event in agent.stream(
            {"messages": conversation},
            stream_mode="values"
        ):
            latest = event.get("messages", [])[-1] if event.get("messages") else None

            if latest and latest.content:
                yield {
                    "event": "token",
                    "data": json.dumps({"content": latest.content})
                }

            if latest and latest.tool_calls:
                for tc in latest.tool_calls:
                    yield {
                        "event": "tool_call",
                        "data": json.dumps({
                            "tool": tc["name"],
                            "args": tc["args"]
                        })
                    }

        yield {"event": "done", "data": "{}"}

    except Exception as e:
        logger.exception(f"Stream error: {e}")
        yield {
            "event": "error",
            "data": json.dumps({"message": "An error occurred during processing"})
        }
```

---

### src/api/endpoints/chat_complete.py (CREATE)

**Purpose:** Batch (non-streaming) chat endpoint

**Guidelines:**

1. Create router with prefix `/chat/complete` and tag `chat`

2. Define endpoint `POST /chat/complete`:
   - Accept `ChatRequest` body
   - Require `session_id` in request body
   - Return `ChatResponse`

3. Response model:
   ```
   ChatResponse:
     response: str
     tool_calls: list[ToolCall] | None
   ```

4. Implementation:
   - Get agent from dependency
   - Invoke agent with `invoke()` method (not stream)
   - Extract response and tool calls
   - Save messages to memory
   - Return response

5. All functions must be async

**Pseudocode:**
```
from fastapi import APIRouter
from pydantic import BaseModel, Field
from src.agent.core import create_conversational_agent
from src.agent.memory import PostgresMemoryStore
from src.config import SettingsDep

router = APIRouter()

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=32000)
    session_id: str = Field(description="UUID session identifier")

class ToolCall(BaseModel):
    tool: str
    input: dict

class ChatResponse(BaseModel):
    response: str
    tool_calls: list[ToolCall] | None = None

@router.post("", response_model=ChatResponse)
async def chat_complete(
    request: ChatRequest,
    settings: SettingsDep
) -> ChatResponse:
    memory_store = await _get_memory_store(settings)
    agent = await create_conversational_agent(request.session_id, memory_store)

    conversation = await memory_store.get_conversation(request.session_id)
    conversation.append({"role": "user", "content": request.message})

    result = await agent.invoke({"messages": conversation})

    final_message = result["messages"][-1]
    tool_calls = None

    if hasattr(final_message, "tool_calls") and final_message.tool_calls:
        tool_calls = [
            ToolCall(tool=tc["name"], input=tc["args"])
            for tc in final_message.tool_calls
        ]

    await memory_store.save_message(request.session_id, final_message.dict())

    return ChatResponse(
        response=final_message.content,
        tool_calls=tool_calls
    )
```

---

### src/api/endpoints/__init__.py (MODIFY)

**Purpose:** Update exports for new routers

**Changes:**
- Remove: `chat_router`
- Add: `chat_stream_router`, `chat_complete_router`

**Pseudocode:**
```
from .chat_stream import router as chat_stream_router
from .chat_complete import router as chat_complete_router
from .health import router as health_router

__all__ = [
    "chat_stream_router",
    "chat_complete_router",
    "health_router",
]
```

---

### src/api/app.py (MODIFY)

**Purpose:** Include new routers

**Changes:**
- Remove: `chat_router` include
- Add: `chat_stream_router` at `/chat`
- Add: `chat_complete_router` at `/chat/complete`

**Pseudocode:**
```
from src.api.endpoints import chat_stream_router, chat_complete_router, health_router

def create_app() -> FastAPI:
    app = FastAPI(...)

    app.include_router(chat_stream_router, prefix="/chat", tags=["chat"])
    app.include_router(chat_complete_router, prefix="/chat/complete", tags=["chat"])
    app.include_router(health_router, tags=["health"])

    return app
```

---

## Dependencies

- `sse-starlette` - SSE support for FastAPI
- `fastapi` - API framework
- `pydantic` - Data validation
- `src.agent.core` - Agent factory
- `src.agent.memory` - Memory store
- `src.config` - Settings

---

## Integration Notes

1. `/chat` is now streaming by default
2. `/chat/complete` provides batch alternative
3. session_id is required for both endpoints
4. Memory is persisted after each message
5. Error events are sent via SSE for streaming
6. Batch endpoint returns 500 on errors
