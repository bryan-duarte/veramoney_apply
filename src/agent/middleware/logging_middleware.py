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

    logger.debug(
        "agent_request session=%s messages=%d tools=%s",
        session_id,
        message_count,
        tool_names,
    )

    start_time = time.perf_counter()
    response = await handler(request)
    duration_ms = (time.perf_counter() - start_time) * 1000

    tool_calls = response.message.tool_calls if response.message else []
    content_length = (
        len(response.message.content)
        if response.message and response.message.content
        else 0
    )

    logger.debug(
        "agent_response session=%s content_len=%d tool_calls=%d duration=%.2fms",
        session_id,
        content_length,
        len(tool_calls),
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
