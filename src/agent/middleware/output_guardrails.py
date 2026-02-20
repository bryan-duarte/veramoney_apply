import logging
import re

from langchain.agents.middleware import AgentState, after_model
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langgraph.runtime import Runtime

from src.tools.constants import TOOL_STOCK, TOOL_WEATHER

from .utils import extract_float_field, parse_json_content


logger = logging.getLogger(__name__)


@after_model
async def output_guardrails(state: AgentState, _runtime: Runtime) -> dict[str, str] | None:
    messages = state.get("messages", [])
    if not messages:
        return None

    last_message = messages[-1]
    if not isinstance(last_message, AIMessage):
        return None

    if not last_message.content:
        return None

    tool_results = _extract_tool_results(messages)
    response_content = last_message.content.lower()

    for tool_name, result_content in tool_results.items():
        if tool_name == TOOL_WEATHER:
            _check_weather_hallucination(response_content, result_content)
        elif tool_name == TOOL_STOCK:
            _check_stock_hallucination(response_content, result_content)

    return None


def _extract_tool_results(messages: list[BaseMessage]) -> dict[str, str]:
    hallucination_check_tools = {TOOL_WEATHER, TOOL_STOCK}
    results: dict[str, str] = {}
    for message in messages:
        if isinstance(message, ToolMessage):
            tool_name = getattr(message, "name", None)
            if tool_name and tool_name in hallucination_check_tools:
                results[tool_name] = message.content
    return results


def _check_weather_hallucination(response_content: str, tool_result: str) -> None:
    if "weather" not in response_content and "temperature" not in response_content:
        return

    temperature = _extract_temperature_from_json(tool_result)
    if temperature is None:
        return

    temperature_in_response = _find_temperature_in_text(response_content)
    if (
        temperature_in_response is not None
        and abs(temperature_in_response - temperature) > 1
    ):
        logger.warning(
            "potential_weather_hallucination expected_temp=%.1f found_temp=%.1f",
            temperature,
            temperature_in_response,
        )


def _check_stock_hallucination(response_content: str, tool_result: str) -> None:
    price_tolerance = 0.01
    if "stock" not in response_content and "price" not in response_content:
        return

    price = _extract_price_from_json(tool_result)
    if price is None:
        return

    price_in_response = _find_price_in_text(response_content)
    if (
        price_in_response is not None
        and abs(price_in_response - price) > price_tolerance
    ):
        logger.warning(
            "potential_stock_hallucination expected_price=%.2f found_price=%.2f",
            price,
            price_in_response,
        )


def _extract_temperature_from_json(content: str) -> float | None:
    data = parse_json_content(content)
    if data is None:
        return None
    return extract_float_field(data, "temperature")


def _extract_price_from_json(content: str) -> float | None:
    data = parse_json_content(content)
    if data is None:
        return None
    return extract_float_field(data, "price")


def _find_temperature_in_text(text: str) -> float | None:
    patterns = [
        r"(\d+(?:\.\d+)?)\s*[°]?[cC]",
        r"(\d+(?:\.\d+)?)\s*[°]?[fF]",
        r"temperature\s*(?:is|of)?\s*(\d+(?:\.\d+)?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return float(match.group(1))
    return None


def _find_price_in_text(text: str) -> float | None:
    patterns = [
        r"\$(\d+(?:\.\d+)?)",
        r"price\s*(?:is|of)?\s*\$?(\d+(?:\.\d+)?)",
        r"(\d+(?:\.\d+)?)\s*(?:usd|dollars?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None
