import logging

from langgraph.checkpoint.postgres import PostgresSaver

from src.config import Settings


logger = logging.getLogger(__name__)

_memory_store_instance: "MemoryStore | None" = None


class MemoryStore:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._checkpointer: PostgresSaver | None = None

    async def initialize(self) -> None:
        connection_uri = self._settings.postgres_memory_uri
        logger.info(f"Initializing memory store connection to {self._settings.postgres_memory_host}")
        self._checkpointer = PostgresSaver.from_conn_string(connection_uri)
        self._checkpointer.setup()
        logger.info("Memory store initialized successfully")

    def get_checkpointer(self) -> PostgresSaver:
        if self._checkpointer is None:
            message = "Memory store not initialized. Call initialize() first."
            raise RuntimeError(message)
        return self._checkpointer

    async def close(self) -> None:
        if self._checkpointer is not None:
            logger.info("Closing memory store connection")
            self._checkpointer = None


async def get_memory_store(settings: Settings) -> MemoryStore:
    global _memory_store_instance  # noqa: PLW0603 - Singleton pattern requires global state
    if _memory_store_instance is None:
        _memory_store_instance = MemoryStore(settings)
        await _memory_store_instance.initialize()
    return _memory_store_instance
