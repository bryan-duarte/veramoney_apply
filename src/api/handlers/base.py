import logging

from langfuse import Langfuse

from src.agent.core.supervisor import SupervisorFactory
from src.agent.memory.store import MemoryStore
from src.config import Settings
from src.observability.datasets import DatasetManager
from src.observability.manager import LangfuseManager
from src.observability.prompts import PromptManager
from src.rag.retriever import KnowledgeRetriever
from src.tools.constants import ASK_STOCK_AGENT


logger = logging.getLogger(__name__)

WEATHER_KEYWORDS = ("weather", "temperature", "clima", "temperatura")
STOCK_KEYWORDS = ("stock", "price", "acción", "precio")
KNOWLEDGE_KEYWORDS = ("vera", "fintech", "regulation", "bank")
STOCK_TOOL_NAME = ASK_STOCK_AGENT


class ChatHandlerBase:
    def __init__(
        self,
        settings: Settings,
        memory_store: MemoryStore,
        supervisor_factory: SupervisorFactory | None = None,
        langfuse_manager: LangfuseManager | None = None,
        dataset_manager: DatasetManager | None = None,
        prompt_manager: PromptManager | None = None,
        knowledge_retriever: KnowledgeRetriever | None = None,
    ):
        self._settings = settings
        self._memory_store = memory_store
        self._langfuse_manager = langfuse_manager
        self._dataset_manager = dataset_manager or DatasetManager(langfuse_manager=langfuse_manager)
        self._prompt_manager = prompt_manager
        self._knowledge_retriever = knowledge_retriever
        self._supervisor_factory = supervisor_factory or SupervisorFactory(
            settings=settings,
            memory_store=memory_store,
            langfuse_manager=langfuse_manager,
            prompt_manager=prompt_manager,
            knowledge_retriever=knowledge_retriever,
        )

    @property
    def dataset_manager(self) -> DatasetManager:
        return self._dataset_manager

    def get_langfuse_client(self) -> Langfuse | None:
        if self._langfuse_manager is None:
            return None
        return self._langfuse_manager.client

    async def is_opening_message(self, session_id: str) -> bool:
        checkpointer = self._memory_store.get_checkpointer()
        existing_state = await checkpointer.aget_tuple(
            {"configurable": {"thread_id": session_id}}
        )
        existing_messages = existing_state.checkpoint.get("channel_values", {}).get("messages", []) if existing_state else []
        return len(existing_messages) == 0

    @staticmethod
    def infer_expected_tools(message: str) -> list[str]:
        message_lower = message.lower()
        expected: list[str] = []
        if any(word in message_lower for word in WEATHER_KEYWORDS):
            expected.append("weather")
        if any(word in message_lower for word in STOCK_KEYWORDS):
            expected.append("stock")
        if any(word in message_lower for word in KNOWLEDGE_KEYWORDS):
            expected.append("knowledge")
        return expected if expected else ["unknown"]

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
            is_stock_tool = getattr(tc, "tool", None) == STOCK_TOOL_NAME
            if is_stock_tool:
                ticker = tc.input.get("ticker", "UNKNOWN")
                self.dataset_manager.add_stock_query(
                    ticker=ticker,
                    user_message=user_message,
                    session_id=session_id,
                )
