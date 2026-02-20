import logging
import time
from collections.abc import Callable

from langchain.agents.middleware import ModelRequest, ModelResponse, wrap_model_call


logger = logging.getLogger(__name__)


@wrap_model_call
async def worker_logging_middleware(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    tool_names = [tool.name for tool in request.tools]

    logger.info(
        "worker_request tools=%s",
        tool_names,
    )

    start_time = time.perf_counter()
    response = await handler(request)
    duration_ms = (time.perf_counter() - start_time) * 1000

    content_length = _extract_content_length(response)

    logger.info(
        "worker_response duration=%.2fms content_len=%d",
        duration_ms,
        content_length,
    )

    return response


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
