from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from langchain.agents import create_agent
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ConfigDict

from src.agent.middleware.worker_logging import worker_logging_middleware
from src.config import Settings


if TYPE_CHECKING:
    from src.observability.prompts import PromptManager


logger = logging.getLogger(__name__)


class WorkerConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    model: str = "gpt-5-nano-2025-08-07"
    tool: BaseTool
    prompt: str
    description: str
    max_iterations: int = 5


class BaseWorkerFactory:
    def __init__(
        self,
        settings: Settings | None = None,
        prompt_manager: PromptManager | None = None,
    ):
        from src.config.settings import settings as default_settings
        self._settings = settings or default_settings
        self._prompt_manager = prompt_manager

    def create_worker(self, config: WorkerConfig) -> Any:
        model = self._build_model(config.model)
        middleware = self._build_middleware()
        prompt, prompt_source = self._resolve_prompt(config)
        agent = create_agent(
            model=model,
            tools=[config.tool],
            system_prompt=prompt,
            middleware=middleware,
            checkpointer=None,
        )
        logger.info(
            "created_worker name=%s model=%s prompt_source=%s",
            config.name,
            config.model,
            prompt_source,
        )
        return agent

    def _resolve_prompt(self, config: WorkerConfig) -> tuple[str, str]:
        if self._prompt_manager is not None:
            compiled_prompt, metadata = self._prompt_manager.get_worker_prompt(config.name)
            return compiled_prompt, metadata.get("prompt_source", "unknown")
        return config.prompt, "hardcoded"

    def _build_model(self, model_name: str) -> ChatOpenAI:
        return ChatOpenAI(
            model=model_name,
            timeout=self._settings.worker_timeout_seconds,
            api_key=self._settings.openai_api_key,
        )

    @staticmethod
    def _build_middleware() -> list:
        return [worker_logging_middleware]
