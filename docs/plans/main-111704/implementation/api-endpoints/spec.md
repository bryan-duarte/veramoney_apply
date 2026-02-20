# API Endpoints Implementation

## Overview

Create handler classes for all API endpoints, with a shared base class to eliminate duplicate session initialization logic.

## Files to Create

- `src/api/handlers/__init__.py` - Handler exports
- `src/api/handlers/base.py` - ChatHandlerBase class
- `src/api/handlers/chat_complete.py` - ChatCompleteHandler class
- `src/api/handlers/chat_stream.py` - ChatStreamHandler class
- `src/api/handlers/health.py` - HealthHandler class

## Files to Modify

- `src/api/endpoints/chat_complete.py` - Use ChatCompleteHandler
- `src/api/endpoints/chat_stream.py` - Use ChatStreamHandler
- `src/api/endpoints/health.py` - Use HealthHandler
- `src/api/__init__.py` - Export handlers

## Implementation Guidelines

### ChatHandlerBase Class

```python
class ChatHandlerBase:
    WEATHER_KEYWORDS = ("weather", "temperature", "clima", "temperatura")
    STOCK_KEYWORDS = ("stock", "price", "acción", "precio")
    KNOWLEDGE_KEYWORDS = ("vera", "fintech", "regulation", "bank")

    def __init__(
        self,
        container: ServiceContainer,
        dataset_manager: DatasetManager | None = None,
    ):
        self._container = container
        self._settings = container.settings
        self._dataset_manager = dataset_manager

    @property
    def dataset_manager(self) -> DatasetManager:
        if self._dataset_manager is None:
            self._dataset_manager = self._container.get_dataset_manager()
        return self._dataset_manager

    async def get_memory_store(self) -> MemoryStore:
        return await self._container.get_memory_store()

    def get_langfuse_client(self) -> Langfuse | None:
        return self._container.get_langfuse_client()

    async def is_opening_message(self, session_id: str) -> bool:
        memory_store = await self.get_memory_store()
        checkpointer = memory_store.get_checkpointer()
        existing_state = await checkpointer.aget_tuple(
            {"configurable": {"thread_id": session_id}}
        )
        existing_messages = existing_state.values.get("messages", []) if existing_state else []
        return len(existing_messages) == 0

    @staticmethod
    def infer_expected_tools(message: str) -> list[str]:
        message_lower = message.lower()
        expected: list[str] = []
        if any(word in message_lower for word in ChatHandlerBase.WEATHER_KEYWORDS):
            expected.append("weather")
        if any(word in message_lower for word in ChatHandlerBase.STOCK_KEYWORDS):
            expected.append("stock")
        if any(word in message_lower for word in ChatHandlerBase.KNOWLEDGE_KEYWORDS):
            expected.append("knowledge")
        return expected if expected else ["unknown"]

    def collect_stock_queries(
        self,
        tool_calls: list[ToolCall],
        user_message: str,
        session_id: str,
    ) -> None:
        langfuse_client = self.get_langfuse_client()
        if langfuse_client is None or not tool_calls:
            return
        for tc in tool_calls:
            is_stock_tool = tc.tool == "get_stock_price"
            if is_stock_tool:
                ticker = tc.input.get("ticker", "UNKNOWN")
                self.dataset_manager.add_stock_query(
                    ticker=ticker,
                    user_message=user_message,
                    session_id=session_id,
                )

    @classmethod
    def from_container(cls, container: ServiceContainer) -> "ChatHandlerBase":
        return cls(container=container)
```

### ChatCompleteHandler Class

```python
class ChatCompleteHandler(ChatHandlerBase):
    async def handle(self, request: ChatCompleteRequest) -> ChatCompleteResponse:
        is_opening = await self.is_opening_message(request.session_id)

        if is_opening:
            expected_tools = self.infer_expected_tools(request.message)
            self.dataset_manager.add_opening_message(
                user_message=request.message,
                session_id=request.session_id,
                expected_tools=expected_tools,
            )

        factory = AgentFactory(
            settings=self._settings,
            memory_store=await self.get_memory_store(),
            langfuse_manager=self._container.langfuse_manager,
        )
        agent, config, langfuse_handler = await factory.create_agent(request.session_id)

        result = await agent.ainvoke(
            {"messages": [HumanMessage(content=request.message)]},
            config=config,
        )

        tool_calls = self._extract_tool_calls(result)
        self.collect_stock_queries(tool_calls, request.message, request.session_id)

        return ChatCompleteResponse(...)

    @staticmethod
    def _extract_tool_calls(result: dict) -> list[ToolCall]:
        messages = result.get("messages", [])
        tool_calls: list[ToolCall] = []

        for message in messages:
            has_tool_calls = hasattr(message, "tool_calls") and message.tool_calls
            if has_tool_calls:
                for tc in message.tool_calls:
                    tool_calls.append(ToolCall(
                        tool=tc.get("name", ""),
                        input=tc.get("args", {}),
                    ))

        return tool_calls
```

### ChatStreamHandler Class

```python
class ChatStreamHandler(ChatHandlerBase):
    async def handle(
        self,
        request: ChatStreamRequest,
    ) -> AsyncGenerator[dict[str, str], None]:
        is_opening = await self.is_opening_message(request.session_id)

        if is_opening:
            expected_tools = self.infer_expected_tools(request.message)
            self.dataset_manager.add_opening_message(
                user_message=request.message,
                session_id=request.session_id,
                expected_tools=expected_tools,
            )

        factory = AgentFactory(
            settings=self._settings,
            memory_store=await self.get_memory_store(),
            langfuse_manager=self._container.langfuse_manager,
        )
        agent, config, _ = await factory.create_agent(request.session_id)

        tool_calls_for_collection: list[dict] = []

        async for stream_mode, data in agent.astream(
            {"messages": [HumanMessage(content=request.message)]},
            config=config,
            stream_mode=["messages", "updates"],
        ):
            if stream_mode == "messages":
                token, _metadata = data
                if isinstance(token, AIMessageChunk):
                    if token.content:
                        yield {"event": "token", "data": json.dumps({"content": token.content})}
                    if token.tool_calls:
                        for tc in token.tool_calls:
                            tool_calls_for_collection.append(tc)
                            yield {"event": "tool_call", "data": json.dumps({
                                "name": tc.get("name"),
                                "args": tc.get("args"),
                            })}
            elif stream_mode == "updates":
                for source, update in data.items():
                    is_tools_update = source == "tools"
                    if is_tools_update:
                        messages = update.get("messages", [])
                        for msg in messages:
                            is_tool_message = isinstance(msg, ToolMessage)
                            if is_tool_message:
                                yield {"event": "tool_result", "data": json.dumps({
                                    "content": msg.content[:500],
                                })}

        self._collect_stock_queries_from_stream(tool_calls_for_collection, request.message, request.session_id)

        yield {"event": "done", "data": "{}"}

    def _collect_stock_queries_from_stream(
        self,
        tool_calls: list[dict],
        user_message: str,
        session_id: str,
    ) -> None:
        langfuse_client = self.get_langfuse_client()
        if langfuse_client is None or not tool_calls:
            return

        for tc in tool_calls:
            is_stock_tool = tc.get("name") == "get_stock_price"
            if is_stock_tool:
                ticker = tc.get("args", {}).get("ticker", "UNKNOWN")
                self.dataset_manager.add_stock_query(
                    ticker=ticker,
                    user_message=user_message,
                    session_id=session_id,
                )
```

### HealthHandler Class

```python
class HealthHandler:
    @classmethod
    def create(cls) -> "HealthHandler":
        return cls()

    async def handle(self) -> HealthResponse:
        return HealthResponse()
```

### Endpoint Update

```python
@router.post("/chat")
async def chat_complete(
    request: ChatCompleteRequest,
    container: ContainerDep,
):
    handler = ChatCompleteHandler.from_container(container)
    return await handler.handle(request)
```

## OOP Patterns Applied

| Pattern | Usage |
|---------|-------|
| `@staticmethod` | `infer_expected_tools()` - pure function of message |
| `@staticmethod` | `_extract_tool_calls()` - pure function of result |
| `@property` | `dataset_manager` - lazy access with caching |
| `@classmethod` | `from_container()` - alternative constructor |
| `@classmethod` | `HealthHandler.create()` - factory method |
| Helper methods | `_collect_stock_queries_from_stream()` - extracted logic |
| Named booleans | `is_stock_tool`, `is_opening`, `has_tool_calls` |

## Dependencies

- ServiceContainer (required)
- DatasetManager (optional, via property)
- AgentFactory (used internally)
- MemoryStore (via container)
- LangfuseManager (via container)

## Integration Notes

- Endpoints become thin wrappers around handlers
- All business logic moves to handler classes
- Duplicate code eliminated via ChatHandlerBase
- Session initialization logic centralized
- Static methods for pure functions improve testability
