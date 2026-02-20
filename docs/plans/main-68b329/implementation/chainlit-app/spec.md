# Chainlit Application Module Implementation

## Overview

The main Chainlit application module that provides the chat UI and connects to the FastAPI backend via SSE streaming.

## Files to Create

| File | Purpose |
|------|---------|
| `src/chainlit/__init__.py` | Module exports |
| `src/chainlit/constants.py` | Timeout values, retry config, error messages |
| `src/chainlit/config.py` | ChainlitSettings Pydantic class |
| `src/chainlit/sse_client.py` | SSE stream client with retry logic |
| `src/chainlit/handlers.py` | Chainlit event handlers |
| `src/chainlit/app.py` | Main application entry point |

## Implementation Guidelines

### constants.py

Define module-level constants:

```
REQUEST_TIMEOUT_SECONDS = 120.0
MAX_RETRY_ATTEMPTS = 3
INITIAL_RETRY_DELAY_SECONDS = 1.0
BACKOFF_MULTIPLIER = 2

WELCOME_MESSAGE = "..."
SUGGESTED_PROMPTS = [...]

ERROR_MESSAGE_UNAUTHORIZED = "Unable to connect to service."
ERROR_MESSAGE_RATE_LIMITED = "Please wait a moment before sending another message."
ERROR_MESSAGE_SERVER_ERROR = "Something went wrong. Please try again."
ERROR_MESSAGE_TIMEOUT = "Request timed out. Please try again."
ERROR_MESSAGE_NETWORK = "Connecting..."
```

### config.py

Pydantic settings class following project patterns:

```
ChainlitSettings(BaseSettings):
    backend_url: str = "http://localhost:8000"
    api_key: str (required)
    request_timeout: float = 120.0
    max_retries: int = 3
    retry_delay: float = 1.0

    model_config = SettingsConfigDict(
        env_prefix="CHAINLIT_",
        env_file=".env",
        case_sensitive=False,
    )
```

### sse_client.py

SSE client implementation:

```
class SSEClient:
    def __init__(self, settings: ChainlitSettings)

    async def stream_chat(
        self,
        message: str,
        session_id: str,
    ) -> AsyncGenerator[SSEEvent, None]

    async def _make_request_with_retry(
        self,
        message: str,
        session_id: str,
    ) -> AsyncGenerator[SSEEvent, None]

    def _parse_sse_line(self, line: str) -> tuple[str | None, str | None]

    def _is_retryable_error(self, status_code: int) -> bool
```

Use tenacity AsyncRetrying for retry logic.

### handlers.py

Event handlers:

```
@cl.on_chat_start
async def on_chat_start() -> None:
    - Initialize settings in cl.user_session
    - Send welcome message with cl.Message
    - Send suggested prompts as cl.Action or text

@cl.on_message
async def on_message(message: cl.Message) -> None:
    - Get settings from cl.user_session
    - Get session_id from cl.context.session.thread_id
    - Create msg = cl.Message(content="")
    - Create SSE client
    - Iterate stream events:
        - token: msg.stream_token(content)
        - tool_call: cl.Step(name, type="tool") with minimal display
        - tool_result: close step (no output)
        - error: show human-readable message inline
        - done: msg.update()
    - Handle exceptions with inline error display
```

### app.py

Main entry point (minimal - just imports):

```
import chainlit as cl
from src.chainlit.handlers import on_chat_start, on_message

# Chainlit discovers handlers via decorators
# No additional code needed
```

## Dependencies

- `chainlit>=2.4.0` (new)
- `httpx>=0.25.0` (existing)
- `tenacity>=8.0.0` (existing)
- `pydantic-settings>=2.13.0` (existing)

## Error Handling

All errors must be caught and displayed inline:

1. httpx.HTTPStatusError - check status code, map to human message
2. httpx.TimeoutException - show timeout message, trigger retry
3. httpx.ConnectError - show network message, trigger retry
4. json.JSONDecodeError - log warning, skip event
5. Generic Exception - show generic error message

## Testing Checklist

- [ ] Welcome message displays on chat start
- [ ] Suggested prompts are visible
- [ ] Message sends to backend successfully
- [ ] Tokens stream to UI in real-time
- [ ] Tool calls show with name only
- [ ] Tool results don't show details
- [ ] Error messages are human-readable
- [ ] Auto-retry works on network failures
- [ ] Session persists across messages
