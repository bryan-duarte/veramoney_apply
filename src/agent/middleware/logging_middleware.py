import logging
import time
from collections.abc import Callable

from langchain.agents.middleware import ModelRequest, ModelResponse, wrap_model_call


logger = logging.getLogger(__name__)


@wrap_model_call
async def logging_middleware(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    session_id = _extract_session_id(request)
    message_count = len(request.state.get("messages", []))
    tool_names = [tool.name for tool in request.tools]

    logger.info(
        "agent_request session=%s messages=%d tools=%s",
        session_id,
        message_count,
        tool_names,
    )

    start_time = time.perf_counter()
    response = await handler(request)
    duration_ms = (time.perf_counter() - start_time) * 1000

    tool_calls_count = _extract_tool_calls_count(response)
    content_length = _extract_content_length(response)

    logger.info(
        "agent_response session=%s content_len=%d tool_calls=%d duration=%.2fms",
        session_id,
        content_length,
        tool_calls_count,
        duration_ms,
    )

    return response


def _extract_session_id(request: ModelRequest) -> str:
    runtime = getattr(request, "runtime", None)
    if runtime is None:
        return "unknown"
    context = getattr(runtime, "context", None)
    if context is None:
        return "unknown"
    return getattr(context, "session_id", "unknown")


def _extract_tool_calls_count(response: ModelResponse) -> int:
    message = getattr(response, "message", None)
    if message is not None:
        return len(getattr(message, "tool_calls", []))
    return len(getattr(response, "tool_calls", []))


def _extract_content_length(response: ModelResponse) -> int:
    message = getattr(response, "message", None)
    if message is not None:
        content = getattr(message, "content", None)
        if content:
            return len(content)
        return 0
    content = getattr(response, "content", None)
    if content:
        return len(content)
    return 0
