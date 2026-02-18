# Phase 4: API Layer

> Status: PARTIAL
> Priority: HIGH (Core Requirement)

## Overview

Create the FastAPI endpoints for the chat service.

## Current Status

| ID | Task | Status | Notes |
|----|------|--------|-------|
| 4.1 | Create FastAPI application | DONE | `src/api/app.py` |
| 4.2 | Create `/chat` endpoint | PARTIAL | Endpoint exists, needs agent integration |
| 4.3 | Define request schema | DONE | ChatRequest with message, session_id |
| 4.4 | Define response schema | DONE | ChatResponse with response, tool_calls |
| 4.5 | Implement session management | TODO | Track conversation context |
| 4.6 | Add error handling | DONE | Global exception handler |
| 4.7 | Add API documentation | N/A | Disabled for security |

## Implementation Location

```
src/api/
├── app.py                    # FastAPI app factory
├── core/                     # Infrastructure
│   ├── dependencies.py       # API key auth
│   ├── exception_handlers.py # Error handlers
│   ├── middleware.py         # Security headers
│   └── rate_limiter.py       # Rate limiting
└── endpoints/
    ├── chat.py               # Chat endpoint
    └── health.py             # Health check
```

## API Schema

### Request

```python
class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=32000,
        description="The user's message to the assistant"
    )
    session_id: str | None = Field(
        None,
        description="Optional session ID for conversation continuity"
    )
```

### Response

```python
class ToolCall(BaseModel):
    tool: str
    input: dict

class ChatResponse(BaseModel):
    response: str
    tool_calls: list[ToolCall] | None = None
```

## Session Management

### Option A: In-Memory (Simple)

```python
sessions: dict[str, list[Message]] = {}

def get_session_history(session_id: str) -> list[Message]:
    return sessions.get(session_id, [])

def add_to_session(session_id: str, message: Message):
    if session_id not in sessions:
        sessions[session_id] = []
    sessions[session_id].append(message)
```

### Option B: Redis (Production)

```python
import redis.asyncio as redis

redis_client = redis.from_url(settings.redis_url)

async def get_session_history(session_id: str) -> list[Message]:
    data = await redis_client.get(f"session:{session_id}")
    return json.loads(data) if data else []

async def add_to_session(session_id: str, message: Message):
    history = await get_session_history(session_id)
    history.append(message)
    await redis_client.setex(
        f"session:{session_id}",
        3600,  # 1 hour TTL
        json.dumps(history)
    )
```

## Integration with Agent

```python
@router.post("", response_model=ChatResponse)
async def chat(
    request: Request,
    api_key: APIKeyDep,
    chat_request: ChatRequest,
) -> ChatResponse:
    session_id = chat_request.session_id or str(uuid.uuid4())

    # Get conversation history
    history = await get_session_history(session_id)

    # Call agent
    result = await agent.ainvoke({
        "messages": history + [HumanMessage(content=chat_request.message)]
    })

    # Update history
    await add_to_session(session_id, result["messages"])

    return ChatResponse(
        response=result["response"],
        tool_calls=result.get("tool_calls")
    )
```

## Testing

```bash
# Health check
curl http://localhost:8000/health

# Chat without session
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key" \
  -d '{"message": "Hello"}'

# Chat with session
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key" \
  -d '{"message": "What about AAPL?", "session_id": "user-123"}'
```

## Dependencies

```toml
fastapi>=0.129.0
uvicorn[standard]>=0.41.0
```
