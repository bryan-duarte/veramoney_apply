import asyncio
import logging
from typing import Any

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langfuse.langchain import CallbackHandler

from src.agent.memory.store import MemoryStore
from src.agent.middleware import (
    knowledge_guardrails,
    logging_middleware,
    output_guardrails,
    tool_error_handler,
)
from src.agent.workers.knowledge_worker import build_ask_knowledge_agent_tool
from src.agent.workers.stock_worker import build_ask_stock_agent_tool
from src.agent.workers.weather_worker import build_ask_weather_agent_tool
from src.config import Settings
from src.observability.manager import LangfuseManager
from src.observability.prompts import PromptManager
from src.rag.retriever import KnowledgeRetriever


logger = logging.getLogger(__name__)


class SupervisorFactory:
    AGENT_VERSION = "2.0"

    def __init__(
        self,
        settings: Settings,
        memory_store: MemoryStore | None = None,
        langfuse_manager: LangfuseManager | None = None,
        prompt_manager: PromptManager | None = None,
        knowledge_retriever: KnowledgeRetriever | None = None,
    ):
        self._settings = settings
        self._memory_store = memory_store
        self._langfuse_manager = langfuse_manager
        self._prompt_manager = prompt_manager
        self._knowledge_retriever = knowledge_retriever
        self._init_lock = asyncio.Lock()

    @property
    def has_memory_store(self) -> bool:
        return self._memory_store is not None

    @property
    def has_langfuse(self) -> bool:
        return self._langfuse_manager is not None and self._langfuse_manager.is_enabled

    async def create_supervisor(
        self,
        session_id: str,
    ) -> tuple[Any, dict, CallbackHandler | None]:
        memory_store = await self._get_memory_store()
        langfuse_handler = self._get_langfuse_handler(session_id)
        compiled_prompt, prompt_metadata = self._get_compiled_prompt()

        model = self._build_model()
        worker_tools = self._build_worker_tools()
        middleware = self._build_middleware_stack()
        checkpointer = memory_store.get_checkpointer()

        agent = create_agent(
            model=model,
            tools=worker_tools,
            system_prompt=compiled_prompt,
            middleware=middleware,
            checkpointer=checkpointer,
        )

        config = self._build_config(session_id, langfuse_handler, prompt_metadata)

        logger.info(
            "created_supervisor session=%s model=%s workers=%s prompt_source=%s langfuse_enabled=%s",
            session_id,
            self._settings.agent_model,
            [t.name for t in worker_tools],
            prompt_metadata.get("prompt_source", "unknown"),
            self.has_langfuse,
        )

        return agent, config, langfuse_handler

    async def _get_memory_store(self) -> MemoryStore:
        if self._memory_store is not None:
            return self._memory_store

        async with self._init_lock:
            if self._memory_store is not None:
                return self._memory_store

            self._memory_store = MemoryStore(settings=self._settings)
            await self._memory_store.initialize()

        return self._memory_store

    def _get_langfuse_handler(self, session_id: str) -> CallbackHandler | None:
        if not self.has_langfuse:
            return None
        return self._langfuse_manager.get_handler(session_id=session_id)

    def _get_compiled_prompt(self) -> tuple[str, dict]:
        if self._prompt_manager is None:
            self._prompt_manager = PromptManager(
                settings=self._settings,
                langfuse_manager=self._langfuse_manager,
            )
        return self._prompt_manager.get_compiled_supervisor_prompt()

    def _build_model(self) -> ChatOpenAI:
        return ChatOpenAI(
            model=self._settings.agent_model,
            timeout=self._settings.agent_timeout_seconds,
            api_key=self._settings.openai_api_key,
        )

    def _build_worker_tools(self) -> list:
        ask_weather = build_ask_weather_agent_tool(
            settings=self._settings,
            prompt_manager=self._prompt_manager,
        )
        ask_stock = build_ask_stock_agent_tool(
            settings=self._settings,
            prompt_manager=self._prompt_manager,
        )
        ask_knowledge = build_ask_knowledge_agent_tool(
            knowledge_retriever=self._knowledge_retriever,
            settings=self._settings,
            prompt_manager=self._prompt_manager,
        )
        return [ask_weather, ask_stock, ask_knowledge]

    @staticmethod
    def _build_middleware_stack() -> list:
        return [
            logging_middleware,
            tool_error_handler,
            output_guardrails,
            knowledge_guardrails,
        ]

    @staticmethod
    def _build_config(
        session_id: str,
        handler: CallbackHandler | None,
        prompt_metadata: dict | None = None,
    ) -> dict:
        callbacks = [handler] if handler else []
        safe_prompt_metadata = {
            k: v for k, v in (prompt_metadata or {}).items()
            if k != "langfuse_prompt"
        }
        metadata = {
            **safe_prompt_metadata,
            "langfuse_session_id": session_id,
            "langfuse_tags": ["veramoney-chat", "supervisor"],
        }
        return {
            "configurable": {"thread_id": session_id},
            "run_name": "veramoney-supervisor",
            "callbacks": callbacks,
            "metadata": metadata,
        }
