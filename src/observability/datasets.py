import logging
from datetime import datetime, timezone

from langfuse import Langfuse

logger = logging.getLogger(__name__)

DATASET_USER_OPENING_MESSAGES = "USER_OPENING_MESSAGES"
DATASET_STOCK_QUERIES = "STOCK_QUERIES"


def add_opening_message_to_dataset(
    client: Langfuse | None,
    message: str,
    session_id: str,
    expected_tools: list[str],
    model: str,
) -> None:
    if client is None:
        return

    try:
        client.create_dataset(name=DATASET_USER_OPENING_MESSAGES)

        timestamp = datetime.now(tz=timezone.utc).isoformat()

        client.create_dataset_item(
            dataset_name=DATASET_USER_OPENING_MESSAGES,
            input={"message": message, "session_id": session_id},
            expected_output=None,
            metadata={
                "timestamp": timestamp,
                "model": model,
                "expected_tools": expected_tools,
            },
        )
    except Exception as exc:
        logger.warning("Failed to add opening message to dataset: %s", exc)


def add_stock_query_to_dataset(
    client: Langfuse | None,
    query: str,
    ticker: str,
    session_id: str,
) -> None:
    if client is None:
        return

    try:
        client.create_dataset(name=DATASET_STOCK_QUERIES)

        timestamp = datetime.now(tz=timezone.utc).isoformat()

        client.create_dataset_item(
            dataset_name=DATASET_STOCK_QUERIES,
            input={"query": query, "ticker": ticker},
            expected_output=None,
            metadata={
                "timestamp": timestamp,
                "session_id": session_id,
            },
        )
    except Exception as exc:
        logger.warning("Failed to add stock query to dataset: %s", exc)
