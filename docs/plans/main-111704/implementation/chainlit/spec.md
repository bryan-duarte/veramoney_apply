# Chainlit Implementation

## Overview

Convert Chainlit handler functions to a class-based structure while keeping SSEClient unchanged.

## Files to Modify

- `src/chainlit/handlers.py` - Convert to ChainlitHandlers class

## Files Unchanged

- `src/chainlit/app.py` - Entry point (minor update to instantiate class)
- `src/chainlit/config.py` - ChainlitSettings class (keep)
- `src/chainlit/constants.py` - Constants (keep)
- `src/chainlit/sse_client.py` - SSEClient class (keep, already OOP)

## Implementation Guidelines

### ChainlitHandlers Class

```python
class ChainlitHandlers:
    def __init__(self, settings: ChainlitSettings):
        self._settings = settings
        self._sse_client: SSEClient | None = None

    def _get_sse_client(self) -> SSEClient:
        if self._sse_client is None:
            self._sse_client = SSEClient(self._settings)
        return self._sse_client

    async def on_chat_start(self) -> None:
        await cl.Message(content=WELCOME_MESSAGE).send()

    async def set_starters(self) -> list[cl.Starter]:
        return [
            cl.Starter(
                label=prompt[:STARTER_LABEL_MAX_LENGTH],
                message=prompt,
            )
            for prompt in SUGGESTED_PROMPTS
        ]

    async def on_message(self, message: cl.Message) -> None:
        session_id = self._get_or_create_session_id()

        client = self._get_sse_client()
        async for event in client.stream_chat(message.content, session_id):
            await self._handle_sse_event(event)

    def _get_or_create_session_id(self) -> str:
        # Session management logic

    async def _handle_sse_event(self, event: SSEEvent) -> None:
        if event.type == "token":
            await self._handle_token(event.data)
        elif event.type == "tool_call":
            await self._handle_tool_call(event.data)
        elif event.type == "tool_result":
            await self._handle_tool_result(event.data)
        elif event.type == "error":
            await self._handle_error(event.data)
        elif event.type == "done":
            pass

    async def _handle_token(self, data: dict) -> None:
        content = data.get("content", "")
        await cl.Message(content=content).stream_token()

    async def _handle_tool_call(self, data: dict) -> None:
        tool_name = data.get("name", "unknown")
        tool_args = data.get("args", {})
        # Create step for tool call visualization

    async def _handle_tool_result(self, data: dict) -> None:
        # Update step with result

    async def _handle_error(self, data: dict) -> None:
        message = data.get("message", ERROR_MESSAGE_GENERIC)
        await cl.ErrorMessage(content=message).send()
```

### App Entry Point Update

```python
# src/chainlit/app.py
from src.chainlit.handlers import ChainlitHandlers
from src.chainlit.config import ChainlitSettings

_settings = ChainlitSettings()
_handlers = ChainlitHandlers(_settings)

# Chainlit decorators call handler methods
@cl.on_chat_start
async def on_chat_start():
    await _handlers.on_chat_start()

@cl.set_starters
async def set_starters():
    return await _handlers.set_starters()

@cl.on_message
async def on_message(message: cl.Message):
    await _handlers.on_message(message)
```

## Dependencies

- ChainlitSettings (required)
- SSEClient (created internally)

## Integration Notes

- SSEClient class remains unchanged (already OOP)
- Handler functions become methods of ChainlitHandlers
- Settings injected via constructor
- SSE client created lazily
- Event handling methods replace inline logic
