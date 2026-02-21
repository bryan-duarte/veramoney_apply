# API Handlers Implementation

## Overview

Refactor ChatHandlerBase using mixin composition (H7) to address SRP violation.

## Files to Modify

- `src/api/handlers/base.py` - Refactor to use mixins
- `src/api/handlers/mixins.py` - NEW: Extract mixin classes
- `src/api/handlers/chat_complete.py` - Update if needed
- `src/api/handlers/chat_stream.py` - Update if needed

## Implementation Guidelines

### Create Mixins

**Create**: `src/api/handlers/mixins.py`

```python
from langfuse import Langfuse

from src.agent.memory.store import MemoryStore
from src.observability.datasets import DatasetManager
from src.observability.manager import LangfuseManager
from src.tools.constants import ASK_STOCK_AGENT

WEATHER_KEYWORDS = ("weather", "temperature", "clima", "temperatura")
STOCK_KEYWORDS = ("stock", "price", "acción", "precio")
KNOWLEDGE_KEYWORDS = ("vera", "fintech", "regulation", "bank")


class ToolIntentMixin:
    @staticmethod
    def infer_expected_tools(message: str) -> list[str]:
        message_lower = message.lower()

        has_weather_keyword = any(kw in message_lower for kw in WEATHER_KEYWORDS)
        has_stock_keyword = any(kw in message_lower for kw in STOCK_KEYWORDS)
        has_knowledge_keyword = any(kw in message_lower for kw in KNOWLEDGE_KEYWORDS)

        expected_tools = []
        if has_weather_keyword:
            expected_tools.append("weather")
        if has_stock_keyword:
            expected_tools.append("stock")
        if has_knowledge_keyword:
            expected_tools.append("knowledge")

        return expected_tools


class SessionStateMixin:
    def __init__(self, memory_store: MemoryStore):
        self._memory_store = memory_store

    async def is_opening_message(self, session_id: str) -> bool:
        existing_state = await self._memory_store.get_checkpointer().aget_tuple(
            config={"configurable": {"thread_id": session_id}}
        )

        is_state_missing = existing_state is None
        is_checkpoint_missing = existing_state.checkpoint is None if existing_state else True

        if is_state_missing or is_checkpoint_missing:
            return True

        existing_messages = existing_state.checkpoint.get("channel_values", {}).get("messages", [])
        return len(existing_messages) == 0


class StockQueryMixin:
    def __init__(self, dataset_manager: DatasetManager, langfuse_manager: LangfuseManager | None):
        self._dataset_manager = dataset_manager
        self._langfuse_manager = langfuse_manager

    @property
    def dataset_manager(self) -> DatasetManager:
        return self._dataset_manager

    def get_langfuse_client(self) -> Langfuse | None:
        has_langfuse_manager = self._langfuse_manager is not None
        if has_langfuse_manager:
            return self._langfuse_manager.client
        return None

    def collect_stock_queries(
        self,
        tool_calls: list,
        user_message: str,
        session_id: str,
    ) -> None:
        langfuse_client = self.get_langfuse_client()
        has_no_client = langfuse_client is None

        if has_no_client:
            return

        for tool_call in tool_calls:
            is_stock_tool = tool_call.tool == ASK_STOCK_AGENT
            if is_stock_tool:
                self._dataset_manager.add_stock_query(
                    query=user_message,
                    session_id=session_id,
                )
```

### Update ChatHandlerBase

**Location**: `src/api/handlers/base.py`

```python
from src.agent.core.supervisor import SupervisorFactory
from src.agent.memory.store import MemoryStore
from src.api.handlers.mixins import SessionStateMixin, StockQueryMixin, ToolIntentMixin
from src.config import Settings
from src.observability.datasets import DatasetManager
from src.observability.manager import LangfuseManager
from src.observability.prompts import PromptManager
from src.rag.retriever import KnowledgeRetriever


class ChatHandlerBase(ToolIntentMixin, SessionStateMixin, StockQueryMixin):
    def __init__(
        self,
        settings: Settings,
        memory_store: MemoryStore,
        langfuse_manager: LangfuseManager | None,
        dataset_manager: DatasetManager | None = None,
        prompt_manager: PromptManager | None = None,
        knowledge_retriever: KnowledgeRetriever | None = None,
        supervisor_factory: SupervisorFactory | None = None,
    ):
        SessionStateMixin.__init__(self, memory_store)
        StockQueryMixin.__init__(
            self,
            dataset_manager or DatasetManager(langfuse_manager=langfuse_manager),
            langfuse_manager,
        )

        self._settings = settings
        self._langfuse_manager = langfuse_manager
        self._prompt_manager = prompt_manager
        self._knowledge_retriever = knowledge_retriever
        self._supervisor_factory = supervisor_factory or SupervisorFactory(
            settings=settings,
            langfuse_manager=langfuse_manager,
            prompt_manager=prompt_manager,
            knowledge_retriever=knowledge_retriever,
        )
```

## Dependencies

- No new dependencies

## Integration Notes

- MRO (Method Resolution Order) is: ChatHandlerBase → ToolIntentMixin → SessionStateMixin → StockQueryMixin → object
- Explicit `__init__` calls ensure proper initialization
- `infer_expected_tools()` remains a static method (no self needed)
