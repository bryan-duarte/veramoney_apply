"""
LangFuse Celery Task Integration Example

This file demonstrates the complete pattern for integrating LangFuse
with Celery background tasks.
Source: clickbait project - app/tasks/grouped_news/enrich_grouped_news.py

Key patterns:
- @observe decorator for automatic tracing
- CallbackHandler for LangChain integration
- get_client() for singleton LangFuse client
- update_current_trace() for metadata
- finally block with flush() for guaranteed delivery
"""

import logging
import traceback

from celery.exceptions import SoftTimeLimitExceeded
from langfuse import get_client, observe
from langfuse.langchain import CallbackHandler


APP_ENV = "DEV"


class TaskResponse:
    """Example task response class."""

    def __init__(self, status: str, message: str, data: dict | None = None):
        self.status = status
        self.message = message
        self.data = data or {}


class TaskResponseFactory:
    """Factory for creating task responses."""

    @staticmethod
    def success(message: str, data: dict | None = None) -> TaskResponse:
        return TaskResponse(status="success", message=message, data=data)

    @staticmethod
    def error(message: str, data: dict | None = None) -> TaskResponse:
        return TaskResponse(status="error", message=message, data=data)

    @staticmethod
    def skipped(message: str, data: dict | None = None) -> TaskResponse:
        return TaskResponse(status="skipped", message=message, data=data)


def get_run_id_from_langfuse(langfuse) -> str:
    """Helper to get run ID from LangFuse (see 02_task_helpers.py)."""
    try:
        trace_id = langfuse.get_current_trace_id()
        if trace_id:
            return trace_id
        import uuid
        return uuid.uuid4().hex
    except Exception:
        import uuid
        return uuid.uuid4().hex


# ============================================================================
# MAIN PATTERN: Celery Task with LangFuse Tracing
# ============================================================================

# In a real Celery app, you would use:
# @celery_app.task(
#     max_retries=3,
#     default_retry_delay=30,
#     queue="my_queue",
#     time_limit=900,
#     soft_time_limit=750,
# )
@observe(name="celery_enrich_grouped_news_task")
def enrich_grouped_news_task(
    grouped_news_id: int,
    force_execution: bool | None = False,
) -> TaskResponse:
    """Background task for enriching grouped news with LangFuse tracing.

    This demonstrates the complete pattern for LangFuse integration
    in Celery tasks.

    Key steps:
    1. Get LangFuse client with get_client()
    2. Update trace with name, tags, metadata
    3. Create CallbackHandler for LangChain
    4. Get run_id for correlation
    5. Pass callbacks to downstream services
    6. Flush in finally block

    Args:
        grouped_news_id: ID of the grouped news to enrich
        force_execution: Force re-enrichment even if already done

    Returns:
        TaskResponse with status and data
    """
    logging.warning(f"Starting enrichment for grouped news ID: {grouped_news_id}")

    try:
        # Step 1: Get LangFuse client (reads from environment variables)
        langfuse = get_client()

        # Step 2: Update the current trace with descriptive metadata
        langfuse.update_current_trace(
            name=f"enrich-grouped-news-{grouped_news_id}",
            tags=["celery", "grouped-news-enrichment", APP_ENV],
            metadata={
                "grouped_news_id": grouped_news_id,
                "force_execution": force_execution,
            },
        )

        # Step 3: Create CallbackHandler for LangChain integration
        # This automatically captures LLM calls, tool calls, and token usage
        langfuse_handler = CallbackHandler()

        # Step 4: Get run_id for correlation across services
        run_id = get_run_id_from_langfuse(langfuse)

        # Step 5: Execute business logic, passing callbacks
        # In real code, this would call an orchestrator:
        # result = enrichment_orchestrator.enrich_grouped_news(
        #     grouped_news_id=grouped_news_id,
        #     run_id=run_id,
        #     task_id=task_id,
        #     callbacks=[langfuse_handler],
        # )

        # Simulated result for example
        result = {
            "status": "success",
            "grouped_news_id": grouped_news_id,
            "run_id": run_id,
        }

        # Update trace with output
        langfuse.update_current_trace(output=result)

        result_status = result.get("status")
        if result_status == "success":
            print(f"SUCCESS - Group ID: {grouped_news_id} enriched | Run ID: {run_id}")
            return TaskResponseFactory.success(
                message=f"Group {grouped_news_id} enriched successfully",
                data=result,
            )
        elif result_status == "blocked":
            return TaskResponseFactory.skipped(
                message=f"Group {grouped_news_id} is blocked",
                data=result,
            )
        else:
            return TaskResponseFactory.error(
                message=result.get("message", "Unknown error"),
                data={"grouped_news_id": grouped_news_id},
            )

    except SoftTimeLimitExceeded:
        logging.warning(f"Soft time limit exceeded for group {grouped_news_id}")
        raise

    except Exception as e:
        error_msg = f"Critical error enriching group {grouped_news_id}: {e!s}"
        logging.exception(error_msg)
        logging.exception(traceback.format_exc())
        return TaskResponseFactory.error(
            message=error_msg,
            data={"grouped_news_id": grouped_news_id},
        )

    finally:
        # CRITICAL: Always flush to ensure traces are sent
        get_client().flush()


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    import os

    os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-test"
    os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-test"
    os.environ["LANGFUSE_BASE_URL"] = "https://cloud.langfuse.com"

    result = enrich_grouped_news_task(grouped_news_id=123, force_execution=False)
    print(f"Result: {result.status} - {result.message}")
