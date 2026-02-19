import logging
from typing import Any

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from src.config import Settings


logger = logging.getLogger(__name__)

_memory_store_instance: "MemoryStore | None" = None


class MemoryStore:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._checkpointer: AsyncPostgresSaver | None = None
        self._async_context_manager: Any = None

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


async def get_memory_store(settings: Settings) -> MemoryStore:
    global _memory_store_instance
    if _memory_store_instance is None:
        _memory_store_instance = MemoryStore(settings)
        await _memory_store_instance.initialize()
    return _memory_store_instance
