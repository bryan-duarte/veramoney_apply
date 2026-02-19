import logging
from collections.abc import Callable
from typing import Any

from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage


logger = logging.getLogger(__name__)

TOOL_SERVICE_NAMES: dict[str, str] = {
    "get_weather": "weather data",
    "get_stock_price": "stock market data",
}


@wrap_tool_call
async def tool_error_handler(
    request: Any,
    handler: Callable[[Any], ToolMessage],
) -> ToolMessage:
    tool_name = request.tool_call["name"]
    service_name = TOOL_SERVICE_NAMES.get(tool_name, tool_name)
    tool_arguments = request.tool_call.get("args", {})

    try:
        return await handler(request)
    except Exception as error:
        logger.exception(
            "tool_error tool=%s args=%s error=%s",
            tool_name,
            tool_arguments,
            str(error),
        )
        error_message = f"I'm having trouble accessing {service_name} right now. Please try again."
        return ToolMessage(
            content=error_message,
            tool_call_id=request.tool_call["id"],
        )
