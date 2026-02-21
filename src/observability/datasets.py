import asyncio
import logging
from datetime import UTC, datetime

from src.observability.manager import LangfuseManager


logger = logging.getLogger(__name__)


class DatasetManager:
    USER_OPENING_MESSAGES: str = "USER_OPENING_MESSAGES"
    STOCK_QUERIES: str = "STOCK_QUERIES"

    DATASET_DESCRIPTIONS: dict[str, str] = {
        "USER_OPENING_MESSAGES": "Tracks initial user messages with expected tool usage for evaluation",
        "STOCK_QUERIES": "Tracks stock price queries with ticker information for evaluation",
    }

    def __init__(self, langfuse_manager: LangfuseManager | None = None):
        self._langfuse_manager = langfuse_manager

    @property
    def _is_available(self) -> bool:
        return self._langfuse_manager is not None and self._langfuse_manager.is_enabled

    async def initialize(self) -> None:
        if not self._is_available:
            return

        client = self._langfuse_manager.client
        dataset_names = [self.USER_OPENING_MESSAGES, self.STOCK_QUERIES]

        try:
            creation_tasks = [
                asyncio.to_thread(
                    client.create_dataset,
                    name=name,
                    description=self.DATASET_DESCRIPTIONS.get(name, ""),
                )
                for name in dataset_names
            ]
            await asyncio.gather(*creation_tasks)
            logger.info("Datasets initialized: %s", ", ".join(dataset_names))
        except Exception as exc:
            logger.warning("Failed to pre-create datasets: %s", exc)

    def add_opening_message(
        self,
        user_message: str,
        session_id: str,
        expected_tools: list[str],
        model: str | None = None,
    ) -> None:
        if not self._is_available:
            return
        try:
            client = self._langfuse_manager.client
            client.create_dataset(name=self.USER_OPENING_MESSAGES)
            client.create_dataset_item(
                dataset_name=self.USER_OPENING_MESSAGES,
                input={"message": user_message, "session_id": session_id},
                expected_output=None,
                metadata={
                    "timestamp": datetime.now(tz=UTC).isoformat(),
                    "model": model or "",
                    "expected_tools": expected_tools,
                },
            )
        except Exception as exc:
            logger.warning("Failed to add opening message to dataset: %s", exc)

    def add_stock_query(
        self,
        ticker: str,
        user_message: str,
        session_id: str,
    ) -> None:
        if not self._is_available:
            return
        try:
            client = self._langfuse_manager.client
            client.create_dataset(name=self.STOCK_QUERIES)
            client.create_dataset_item(
                dataset_name=self.STOCK_QUERIES,
                input={"query": user_message, "ticker": ticker},
                expected_output=None,
                metadata={
                    "timestamp": datetime.now(tz=UTC).isoformat(),
                    "session_id": session_id,
                },
            )
        except Exception as exc:
            logger.warning("Failed to add stock query to dataset: %s", exc)
