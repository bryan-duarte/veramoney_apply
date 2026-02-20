import logging
from typing import Any

from langfuse.langchain import CallbackHandler

logger = logging.getLogger(__name__)

DEFAULT_TRACE_NAME = "veramoney-chat"


def _build_handler_metadata(
    langfuse_prompt: Any | None,
) -> dict[str, Any] | None:
    if langfuse_prompt is None:
        return None
    return {"langfuse_prompt": langfuse_prompt}


def get_langfuse_handler(
    enabled: bool,
    session_id: str,
    trace_name: str = DEFAULT_TRACE_NAME,
    langfuse_prompt: Any | None = None,
) -> CallbackHandler | None:
    if not enabled:
        return None

    try:
        handler = CallbackHandler()
        logger.debug("Langfuse handler created session=%s trace=%s", session_id, trace_name)
        return handler

    except Exception as exc:
        logger.warning("Failed to create Langfuse handler: %s", exc)
        return None
