import logging

import chainlit as cl
from src.chainlit.config import ChainlitSettings
from src.chainlit.constants import (
    ERROR_MESSAGE_GENERIC,
    STARTER_LABEL_MAX_LENGTH,
    SUGGESTED_PROMPTS,
)
from src.chainlit.sse_client import SSEClient


logger = logging.getLogger(__name__)


class ChainlitHandlers:
    TOOL_STOCK: str = "get_stock_price"
    TOOL_WEATHER: str = "get_weather"
    TOOL_KNOWLEDGE: str = "search_knowledge"

    def __init__(self, settings: ChainlitSettings):
        self._settings = settings
        self._sse_client: SSEClient | None = None

    def _get_sse_client(self) -> SSEClient:
        if self._sse_client is None:
            self._sse_client = SSEClient(self._settings)
        return self._sse_client

    async def on_chat_start(self) -> None:
        cl.user_session.set("settings", self._settings)

    async def set_starters(self) -> list[cl.Starter]:
        return [
            cl.Starter(
                label=prompt[:STARTER_LABEL_MAX_LENGTH] + "..."
                if len(prompt) > STARTER_LABEL_MAX_LENGTH
                else prompt,
                message=prompt,
            )
            for prompt in SUGGESTED_PROMPTS
        ]

    async def on_message(self, message: cl.Message) -> None:
        session_id = cl.context.session.thread_id
        client = self._get_sse_client()
        msg = cl.Message(content="")
        await msg.send()

        pending_tools: dict[str, dict] = {}

        try:
            async for event in client.stream_chat(message.content, session_id):
                if event.type == "token":
                    content = str(event.data.get("content", ""))
                    await msg.stream_token(content)

                elif event.type == "tool_call":
                    tool_name = str(event.data.get("tool", "tool"))
                    tool_args = event.data.get("args")
                    args_dict = dict(tool_args) if isinstance(tool_args, dict) else {}
                    context = self._extract_tool_context(tool_name, args_dict)
                    pending_tools[tool_name] = {"context": context}

                elif event.type == "tool_result":
                    tool_name = str(event.data.get("tool", "tool"))
                    tool_info = pending_tools.pop(tool_name, None)
                    if tool_info:
                        context = tool_info.get("context", "")
                        step_name = self._build_step_name(tool_name, context)
                        step_output = self._build_step_output(tool_name, context)
                        step = cl.Step(name=step_name, type="tool")
                        step.output = step_output
                        await step.send()

                elif event.type == "error":
                    error_message = str(event.data.get("message", ERROR_MESSAGE_GENERIC))
                    await msg.update()
                    await cl.Message(content=f"⚠️ {error_message}").send()
                    return

                elif event.type == "done":
                    break

        except Exception:
            logger.exception("handler_error session=%s", session_id)
            await msg.update()
            await cl.Message(content=f"⚠️ {ERROR_MESSAGE_GENERIC}").send()
            return

        await msg.update()

    @staticmethod
    def _extract_tool_context(tool_name: str, tool_args: dict) -> str:
        if tool_name == ChainlitHandlers.TOOL_STOCK:
            return tool_args.get("ticker", "")
        if tool_name == ChainlitHandlers.TOOL_WEATHER:
            return tool_args.get("city_name", "")
        if tool_name == ChainlitHandlers.TOOL_KNOWLEDGE:
            document_type = tool_args.get("document_type", "")
            return document_type if document_type else "all documents"
        return ""

    @staticmethod
    def _build_step_name(tool_name: str, context: str) -> str:
        if tool_name == ChainlitHandlers.TOOL_STOCK:
            return f"Fetching stock data for {context}" if context else "Fetching stock data"
        if tool_name == ChainlitHandlers.TOOL_WEATHER:
            return f"Fetching weather for {context}" if context else "Fetching weather"
        if tool_name == ChainlitHandlers.TOOL_KNOWLEDGE:
            return f"Searching knowledge base ({context})" if context else "Searching knowledge base"
        return tool_name.replace("_", " ").title()

    @staticmethod
    def _build_step_output(tool_name: str, context: str) -> str:
        if tool_name == ChainlitHandlers.TOOL_STOCK:
            return f"Retrieved stock data for {context}" if context else "Retrieved stock data"
        if tool_name == ChainlitHandlers.TOOL_WEATHER:
            return f"Retrieved weather for {context}" if context else "Retrieved weather"
        if tool_name == ChainlitHandlers.TOOL_KNOWLEDGE:
            return "Found relevant documents"
        return "Completed"
