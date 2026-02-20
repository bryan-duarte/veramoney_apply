import logging
from typing import Any

from langchain.agents import create_agent
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ConfigDict

from src.agent.middleware.worker_logging import worker_logging_middleware
from src.config import Settings


logger = logging.getLogger(__name__)


class WorkerConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    model: str = "gpt-5-nano-2025-08-07"
    tool: BaseTool
    prompt: str
    description: str


class BaseWorkerFactory:
    def __init__(
        self,
        settings: Settings | None = None,
    ):
        from src.config.settings import settings as default_settings
        self._settings = settings or default_settings

    def create_worker(self, config: WorkerConfig) -> Any:
        model = self._build_model(config.model)
        middleware = self._build_middleware()
        agent = create_agent(
            model=model,
            tools=[config.tool],
            system_prompt=config.prompt,
            middleware=middleware,
            checkpointer=None,
        )
        logger.info(
            "created_worker name=%s model=%s",
            config.name,
            config.model,
        )
        return agent

    def _build_model(self, model_name: str) -> ChatOpenAI:
        return ChatOpenAI(
            model=model_name,
            timeout=self._settings.worker_timeout_seconds,
            api_key=self._settings.openai_api_key,
        )

    @staticmethod
    def _build_middleware() -> list:
        return [worker_logging_middleware]
