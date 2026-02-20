"""
LangFuse Task Helpers - Run ID Extraction

This file demonstrates how to extract and manage run IDs from LangFuse traces.
Source: clickbait project - app/tasks/task_helpers.py

Key patterns:
- Getting current trace ID from LangFuse
- Fallback to UUID when trace ID unavailable
- Graceful error handling
"""

import logging
import uuid

from langfuse import Langfuse


def get_run_id_from_langfuse(langfuse: Langfuse) -> str:
    """Extract run_id from LangFuse trace or generate a fallback UUID.

    This helper ensures trace IDs are always available, even when
    LangFuse fails or trace hasn't been initialized.

    Args:
        langfuse: Initialized Langfuse client

    Returns:
        Langfuse trace_id or UUID generated as fallback

    Usage:
        from langfuse import get_client

        langfuse = get_client()
        langfuse.update_current_trace(
            name="my-operation",
            tags=["api", "production"],
            metadata={"user_id": 123}
        )

        run_id = get_run_id_from_langfuse(langfuse)

        # Use run_id for correlation across services
        result = process_data(run_id=run_id)
    """
    try:
        trace_id = langfuse.get_current_trace_id()
        if trace_id:
            return trace_id

        logging.warning("Could not get trace_id from LangFuse, using fallback UUID")
        return uuid.uuid4().hex

    except Exception as e:
        logging.warning(f"Error getting trace_id from LangFuse, using fallback: {e}")
        return uuid.uuid4().hex


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    from langfuse import get_client

    langfuse = get_client()

    langfuse.update_current_trace(
        name="example-operation",
        tags=["example", "demo"],
        metadata={"operation": "get_run_id_example"},
    )

    run_id = get_run_id_from_langfuse(langfuse)
    print(f"Run ID: {run_id}")

    get_client().flush()
