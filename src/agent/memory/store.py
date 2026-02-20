import logging
from typing import TYPE_CHECKING

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from src.config import Settings


if TYPE_CHECKING:
    from contextlib import AbstractAsyncContextManager


logger = logging.getLogger(__name__)


class MemoryStore:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._checkpointer: AsyncPostgresSaver | None = None
        self._async_context_manager: AbstractAsyncContextManager[AsyncPostgresSaver] | None = None

    async def initialize(self) -> None:
        connection_uri = self._settings.postgres_memory_uri
        logger.info(
            f"Initializing memory store connection to {self._settings.postgres_memory_host}"
        )
        self._async_context_manager = AsyncPostgresSaver.from_conn_string(connection_uri)
        self._checkpointer = await self._async_context_manager.__aenter__()
        await self._checkpointer.setup()
        logger.info("Memory store initialized successfully")

    def get_checkpointer(self) -> AsyncPostgresSaver:
        if self._checkpointer is None:
            message = "Memory store not initialized. Call initialize() first."
            raise RuntimeError(message)
        return self._checkpointer

    async def close(self) -> None:
        if self._async_context_manager is not None:
            logger.info("Closing memory store connection")
            await self._async_context_manager.__aexit__(None, None, None)
            self._checkpointer = None
            self._async_context_manager = None


