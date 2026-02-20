# Technical Design

## Architecture Overview

Pattern B (Proxy Integration) architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Browser                              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Chainlit Service (:8002)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  handlers   │  │  sse_client │  │     Chainlit UI         │  │
│  │ (on_message)│──▶│ (httpx)     │──▶│  (cl.Message, cl.Step) │  │
│  └─────────────┘  └──────┬──────┘  └─────────────────────────┘  │
└──────────────────────────┼──────────────────────────────────────┘
                           │ HTTP/SSE
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FastAPI Backend (:8000)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Rate Limiter│  │  API Auth   │  │   Agent + Tools         │  │
│  │ (60/min)    │  │ (X-API-Key) │  │   (LangChain)           │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Module Design

### src/chainlit/ Module Structure

```
src/chainlit/
├── __init__.py           # Module exports
├── app.py                # Main Chainlit entry point
├── config.py             # Settings class for Chainlit
├── handlers.py           # Event handlers (on_chat_start, on_message)
├── sse_client.py         # SSE stream client
└── constants.py          # Constants (timeouts, retry config)
```

### Component Responsibilities

| Component | Responsibility |
|-----------|---------------|
| `app.py` | Chainlit decorators and main entry |
| `config.py` | Pydantic settings for Chainlit-specific config |
| `handlers.py` | `@cl.on_chat_start`, `@cl.on_message` logic |
| `sse_client.py` | httpx SSE stream handling, retry logic |
| `constants.py` | Timeout values, retry counts, error messages |

## SSE Protocol

### Request Format

```
POST /chat HTTP/1.1
Host: backend:8000
Content-Type: application/json
X-API-Key: <shared-api-key>
Accept: text/event-stream

{
  "message": "What's the weather in Montevideo?",
  "session_id": "cl-context-session-thread-id"
}
```

### Response Events

| Event | Data Format | Chainlit Action |
|-------|-------------|-----------------|
| `token` | `{"content": "..."}` | `msg.stream_token(content)` |
| `tool_call` | `{"tool": "name", "args": {...}}` | `cl.Step(name=tool, type="tool")` |
| `tool_result` | `{"tool": "name", "result": "..."}` | Close step (no output display) |
| `done` | `{}` | `msg.update()` |
| `error` | `{"message": "..."}` | Show inline error |

### SSE Parsing Logic

1. Iterate `response.aiter_lines()`
2. Parse `event:` line for event type
3. Parse `data:` line for JSON payload
4. Handle empty lines between events
5. Break on `done` event

## Error Handling Strategy

### Error Categories

| HTTP Status | Cause | UI Response | Retry? |
|-------------|-------|-------------|--------|
| 401 | Invalid API key | "Unable to connect to service" | No |
| 429 | Rate limit | "Please wait a moment..." | No |
| 500 | Server error | "Something went wrong" | Yes (3x) |
| Network | Connection failed | "Connecting..." | Yes (3x) |
| Timeout | 120s exceeded | "Request timed out" | Yes (3x) |

### Retry Configuration

- Max attempts: 3
- Initial delay: 1 second
- Backoff multiplier: 2 (1s, 2s, 4s)
- Retry on: Network errors, 500, Timeout
- No retry on: 401, 429

## Configuration Schema

### ChainlitSettings (src/chainlit/config.py)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `backend_url` | str | "http://localhost:8000" | FastAPI backend URL |
| `api_key` | str | Required | Shared API key for backend |
| `request_timeout` | float | 120.0 | SSE stream timeout |
| `max_retries` | int | 3 | Network failure retries |
| `retry_delay` | float | 1.0 | Initial retry delay |

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `CHAINLIT_API_KEY` | Yes | API key for backend auth |
| `BACKEND_URL` | No | Override backend URL |
| `CHAINLIT_PORT` | No | Chainlit server port (default: 8002) |

## Integration Points

### FastAPI Backend (No Changes Required)

- Endpoint: `POST /chat`
- Auth: `X-API-Key` header
- Rate Limit: 60/min per API key
- Response: SSE stream

### CORS Configuration (Backend)

Add Chainlit origin to `CORS_ORIGINS`:
```
CORS_ORIGINS=http://localhost:8002,https://chainlit.yourdomain.com
```

## Docker Configuration

### docker-compose.yml Addition

```yaml
chainlit:
  build:
    context: .
    dockerfile: Dockerfile
    target: development
  container_name: veramoney-chainlit
  restart: unless-stopped
  ports:
    - "${CHAINLIT_PORT:-8002}:8000"
  environment:
    - BACKEND_URL=http://app:8000
    - CHAINLIT_API_KEY=${API_KEY}
  depends_on:
    - app
  networks:
    - vera-network
  command: chainlit run src/chainlit/app.py --host 0.0.0.0 --port 8000
```

## Coding Conventions

All Chainlit code must follow project conventions:

1. **Async-First**: All I/O functions must be `async def`
2. **No Comments**: Self-documenting code only
3. **Pydantic Schemas**: Use `BaseModel`, `Field` for configuration
4. **Structured Logging**: `logger = logging.getLogger(__name__)`
5. **Named Boolean Conditions**: Guard clauses over nesting
6. **Type Hints**: Python 3.11+ syntax (`str | None`, `dict[str, str]`)
7. **Constants**: UPPER_SNAKE_CASE at module level
8. **Error Messages**: Human-readable, not technical

## Dependencies

### Required Additions to pyproject.toml

| Package | Version | Purpose |
|---------|---------|---------|
| `chainlit` | >=2.4.0 | Chat UI framework |

Already available:
- `httpx>=0.25.0` - SSE client
- `tenacity>=8.0.0` - Retry logic
- `pydantic-settings>=2.13.0` - Configuration

## Security Considerations

1. **API Key**: Never log or expose the API key
2. **CORS**: Restrict to known origins in production
3. **Error Messages**: Sanitize technical details before display
4. **Timeout**: Prevent hanging connections with 120s limit
5. **Rate Limiting**: Chainlit shares the backend's 60/min limit
