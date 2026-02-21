import logging

from src.agent.core.supervisor import SupervisorFactory
from src.agent.memory.store import MemoryStore
from src.api.handlers.mixins import SessionStateMixin, StockQueryMixin, ToolIntentMixin
from src.config import Settings
from src.observability.datasets import DatasetManager
from src.observability.manager import LangfuseManager
from src.observability.prompts import PromptManager
from src.rag.retriever import KnowledgeRetriever


logger = logging.getLogger(__name__)

STOCK_TOOL_NAME = "ask_stock_agent"


class ChatHandlerBase(ToolIntentMixin, SessionStateMixin, StockQueryMixin):
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
        self._dataset_manager = dataset_manager or DatasetManager(
            langfuse_manager=langfuse_manager,
        )
        self._prompt_manager = prompt_manager
        self._knowledge_retriever = knowledge_retriever
        self._supervisor_factory = supervisor_factory or SupervisorFactory(
            settings=settings,
            memory_store=memory_store,
            langfuse_manager=langfuse_manager,
            prompt_manager=prompt_manager,
            knowledge_retriever=knowledge_retriever,
        )
