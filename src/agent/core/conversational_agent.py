import logging
from typing import Any

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langfuse.langchain import CallbackHandler

from src.agent.core.prompts import VERA_SYSTEM_PROMPT
from src.agent.memory.store import MemoryStore
from src.agent.middleware import (
    knowledge_guardrails,
    logging_middleware,
    output_guardrails,
    tool_error_handler,
)
from src.config import Settings
from src.observability import (
    PROMPT_NAME_VERA_SYSTEM,
    format_current_date,
    get_compiled_system_prompt,
    get_langfuse_handler,
    initialize_langfuse_client,
    is_prompt_synced,
    mark_prompt_synced,
    sync_prompt_to_langfuse,
)
from src.tools.knowledge import search_knowledge
from src.tools.stock import get_stock_price
from src.tools.weather import get_weather

logger = logging.getLogger(__name__)

AGENT_VERSION = "1.0"


async def create_conversational_agent(
    settings: Settings,
    memory_store: MemoryStore,
    session_id: str,
) -> tuple[Any, dict, CallbackHandler | None]:
    model = ChatOpenAI(
        model=settings.agent_model,
        timeout=settings.agent_timeout_seconds,
        api_key=settings.openai_api_key,
    )

    tools = [get_weather, get_stock_price, search_knowledge]

    middleware_stack = [
        logging_middleware,
        tool_error_handler,
        output_guardrails,
        knowledge_guardrails,
    ]

    checkpointer = memory_store.get_checkpointer()

    langfuse_client = await initialize_langfuse_client()
    langfuse_active = langfuse_client is not None

    if langfuse_client is not None and not is_prompt_synced():
        sync_prompt_to_langfuse(
            client=langfuse_client,
            prompt_name=PROMPT_NAME_VERA_SYSTEM,
            prompt_content=VERA_SYSTEM_PROMPT,
        )
        mark_prompt_synced()

    current_date = format_current_date()
    compiled_prompt, prompt_metadata = get_compiled_system_prompt(
        client=langfuse_client,
        fallback_system=VERA_SYSTEM_PROMPT,
        current_date=current_date,
        model_name=settings.agent_model,
        version=AGENT_VERSION,
    )

    langfuse_prompt = prompt_metadata.get("langfuse_prompt")

    langfuse_handler = get_langfuse_handler(
        enabled=langfuse_active,
        session_id=session_id,
        langfuse_prompt=langfuse_prompt,
    )

    callbacks = [langfuse_handler] if langfuse_handler else []

    langfuse_metadata = {
        **prompt_metadata,
        "langfuse_session_id": session_id,
        "langfuse_trace_name": "veramoney-chat",
    }

    config = {
        "configurable": {
            "thread_id": session_id,
        },
        "callbacks": callbacks,
        "metadata": langfuse_metadata,
    }

    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=compiled_prompt,
        middleware=middleware_stack,
        checkpointer=checkpointer,
    )

    logger.info(
        "created_agent session=%s model=%s tools=%s prompt_source=%s langfuse_enabled=%s callbacks_count=%d",
        session_id,
        settings.agent_model,
        [tool.name for tool in tools],
        prompt_metadata.get("prompt_source", "unknown"),
        langfuse_active,
        len(callbacks),
    )

    return agent, config, langfuse_handler
