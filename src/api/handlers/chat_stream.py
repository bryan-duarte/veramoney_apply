import json
import logging
from collections.abc import AsyncGenerator

from langchain.messages import AIMessageChunk, HumanMessage, ToolMessage

from src.api.handlers.base import STOCK_TOOL_NAME, ChatHandlerBase
from src.api.schemas import ChatStreamRequest


logger = logging.getLogger(__name__)


class ChatStreamHandler(ChatHandlerBase):
    async def handle(
        self,
        request: ChatStreamRequest,
    ) -> AsyncGenerator[dict[str, str], None]:
        try:
            is_opening = await self.is_opening_message(request.session_id)

            if is_opening:
                expected_tools = self.infer_expected_tools(request.message)
                self.dataset_manager.add_opening_message(
                    user_message=request.message,
                    session_id=request.session_id,
                    expected_tools=expected_tools,
                    model=self._settings.agent_model,
                )

            agent, config, langfuse_handler = await self._agent_factory.create_agent(request.session_id)

            stream_tool_calls: list[dict] = []

            async for stream_mode, data in agent.astream(
                {"messages": [HumanMessage(content=request.message)]},
                config=config,
                stream_mode=["messages", "updates"],
            ):
                if stream_mode == "messages":
                    token, _metadata = data
                    if isinstance(token, AIMessageChunk):
                        if token.content:
                            yield {
                                "event": "token",
                                "data": json.dumps({"content": token.content}),
                            }
                        if token.tool_calls:
                            for tool_call in token.tool_calls:
                                tool_name = tool_call.get("name")
                                tool_args = tool_call.get("args", {})
                                stream_tool_calls.append({"tool": tool_name, "args": tool_args})
                                yield {
                                    "event": "tool_call",
                                    "data": json.dumps({"tool": tool_name, "args": tool_args}),
                                }
                elif stream_mode == "updates":
                    for source, update in data.items():
                        is_tools_update = source == "tools"
                        if is_tools_update:
                            messages = update.get("messages", [])
                            for msg in messages:
                                is_tool_message = isinstance(msg, ToolMessage)
                                if is_tool_message:
                                    yield {
                                        "event": "tool_result",
                                        "data": json.dumps({
                                            "tool": getattr(msg, "name", "unknown"),
                                            "result": msg.content,
                                        }),
                                    }

            self._collect_stock_queries_from_stream(
                stream_tool_calls, request.message, request.session_id
            )

            langfuse_client = self.get_langfuse_client()
            if langfuse_handler and langfuse_client:
                langfuse_client.flush()
                logger.debug("Langfuse flushed session=%s", request.session_id)

            yield {"event": "done", "data": "{}"}

        except Exception as error:
            logger.exception("stream_error session=%s error=%s", request.session_id, str(error))
            yield {
                "event": "error",
                "data": json.dumps({"message": "An error occurred during processing"}),
            }

    def _collect_stock_queries_from_stream(
        self,
        tool_calls: list[dict],
        user_message: str,
        session_id: str,
    ) -> None:
        langfuse_client = self.get_langfuse_client()
        if langfuse_client is None or not tool_calls:
            return

        for tc in tool_calls:
            is_stock_tool = tc.get("tool") == STOCK_TOOL_NAME
            if is_stock_tool:
                ticker = tc.get("args", {}).get("ticker", "UNKNOWN")
                self.dataset_manager.add_stock_query(
                    ticker=ticker,
                    user_message=user_message,
                    session_id=session_id,
                )
