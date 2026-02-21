from langfuse import Langfuse

from src.agent.constants import ASK_STOCK_AGENT
from src.agent.memory.store import MemoryStore
from src.observability.datasets import DatasetManager
from src.observability.manager import LangfuseManager


WEATHER_KEYWORDS = ("weather", "temperature", "clima", "temperatura")
STOCK_KEYWORDS = ("stock", "price", "acción", "precio")
KNOWLEDGE_KEYWORDS = ("vera", "fintech", "regulation", "bank")


class ToolIntentMixin:
    @staticmethod
    def infer_expected_tools(message: str) -> list[str]:
        message_lower = message.lower()

        has_weather_keyword = any(
            kw in message_lower for kw in WEATHER_KEYWORDS
        )
        has_stock_keyword = any(
            kw in message_lower for kw in STOCK_KEYWORDS
        )
        has_knowledge_keyword = any(
            kw in message_lower for kw in KNOWLEDGE_KEYWORDS
        )

        expected_tools: list[str] = []
        if has_weather_keyword:
            expected_tools.append("weather")
        if has_stock_keyword:
            expected_tools.append("stock")
        if has_knowledge_keyword:
            expected_tools.append("knowledge")

        return expected_tools if expected_tools else ["unknown"]


class SessionStateMixin:
    _memory_store: MemoryStore

    async def is_opening_message(self, session_id: str) -> bool:
        checkpointer = self._memory_store.get_checkpointer()
        existing_state = await checkpointer.aget_tuple(
            {"configurable": {"thread_id": session_id}}
        )

        is_state_missing = existing_state is None
        is_checkpoint_missing = (
            existing_state.checkpoint is None
            if existing_state
            else True
        )

        if is_state_missing or is_checkpoint_missing:
            return True

        channel_values = existing_state.checkpoint.get(
            "channel_values", {}
        )
        existing_messages = channel_values.get("messages", [])
        return len(existing_messages) == 0


class StockQueryMixin:
    _dataset_manager: DatasetManager
    _langfuse_manager: LangfuseManager | None

    @property
    def dataset_manager(self) -> DatasetManager:
        return self._dataset_manager

    def get_langfuse_client(self) -> Langfuse | None:
        if self._langfuse_manager is None:
            return None
        return self._langfuse_manager.client

    def collect_stock_queries(
        self,
        tool_calls: list,
        user_message: str,
        session_id: str,
    ) -> None:
        langfuse_client = self.get_langfuse_client()
        if langfuse_client is None or not tool_calls:
            return

        for tc in tool_calls:
            is_stock_tool = (
                getattr(tc, "tool", None) == ASK_STOCK_AGENT
            )
            if is_stock_tool:
                ticker = tc.input.get("ticker", "UNKNOWN")
                self._dataset_manager.add_stock_query(
                    ticker=ticker,
                    user_message=user_message,
                    session_id=session_id,
                )
