import logging
from typing import Any

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from src.agent.core.prompts import VERA_SYSTEM_PROMPT
from src.agent.memory.store import MemoryStore
from src.agent.middleware import (
    logging_middleware,
    output_guardrails,
    tool_error_handler,
)
from src.config import Settings
from src.tools.stock import get_stock_price
from src.tools.weather import get_weather


logger = logging.getLogger(__name__)


async def create_conversational_agent(
    settings: Settings,
    memory_store: MemoryStore,
    session_id: str,
) -> Any:
    model = ChatOpenAI(
        model=settings.agent_model,
        timeout=settings.agent_timeout_seconds,
        api_key=settings.openai_api_key,
    )

    tools = [get_weather, get_stock_price]

    middleware_stack = [
        logging_middleware,
        tool_error_handler,
        output_guardrails,
    ]

    checkpointer = memory_store.get_checkpointer()

    config = {
        "configurable": {
            "thread_id": session_id,
        },
    }

    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=VERA_SYSTEM_PROMPT,
        middleware=middleware_stack,
        checkpointer=checkpointer,
    )

    logger.debug(
        "created_agent session=%s model=%s tools=%s",
        session_id,
        settings.agent_model,
        [tool.name for tool in tools],
    )

    return agent, config
