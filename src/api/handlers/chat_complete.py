import logging

from fastapi import HTTPException
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from src.api.handlers.base import ChatHandlerBase
from src.api.schemas import ChatCompleteRequest, ChatCompleteResponse, ToolCall, WorkerToolCall
from src.tools.constants import ALL_WORKER_TOOLS


logger = logging.getLogger(__name__)


class ChatCompleteHandler(ChatHandlerBase):
    async def handle(self, request: ChatCompleteRequest) -> ChatCompleteResponse:
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

            supervisor, config, langfuse_handler = await self._supervisor_factory.create_supervisor(request.session_id)

            result = await supervisor.ainvoke(
                {"messages": [HumanMessage(content=request.message)]},
                config=config,
            )

            messages = result.get("messages", [])
            if not messages:
                return ChatCompleteResponse(response="No response generated.", tool_calls=None)

            final_message = messages[-1]
            if not isinstance(final_message, AIMessage):
                return ChatCompleteResponse(response="Unexpected response format.", tool_calls=None)

            tool_calls = self._extract_tool_calls(messages)
            worker_details = self._extract_worker_details(messages)
            self.collect_stock_queries(tool_calls or [], request.message, request.session_id)

            langfuse_client = self.get_langfuse_client()
            if langfuse_handler and langfuse_client:
                langfuse_client.flush()
                logger.debug("Langfuse flushed session=%s", request.session_id)

            logger.info(
                "chat_complete session=%s response_len=%d worker_calls=%d",
                request.session_id,
                len(final_message.content) if final_message.content else 0,
                len(worker_details) if worker_details else 0,
            )

            return ChatCompleteResponse(
                response=final_message.content or "",
                tool_calls=tool_calls,
                worker_details=worker_details,
            )

        except Exception as error:
            logger.exception(
                "chat_complete_error session=%s error=%s", request.session_id, str(error)
            )
            raise HTTPException(status_code=500, detail="Internal server error") from error

    @staticmethod
    def _extract_tool_calls(messages: list) -> list[ToolCall] | None:
        tool_calls: list[ToolCall] = []
        seen_tools: set[tuple[str, str]] = set()

        for message in messages:
            has_tool_calls = isinstance(message, AIMessage) and message.tool_calls
            if has_tool_calls:
                for tc in message.tool_calls:
                    tool_name = tc.get("name", "")
                    tool_args = tc.get("args", {})
                    args_key = str(sorted(tool_args.items()))
                    tool_key = (tool_name, args_key)
                    if tool_key not in seen_tools:
                        seen_tools.add(tool_key)
                        tool_calls.append(ToolCall(tool=tool_name, input=tool_args))

        return tool_calls if tool_calls else None

    @staticmethod
    def _extract_worker_details(messages: list) -> list[WorkerToolCall] | None:
        worker_request_map: dict[str, str] = {}
        worker_details: list[WorkerToolCall] = []

        for message in messages:
            is_ai_with_tool_calls = isinstance(message, AIMessage) and message.tool_calls
            if is_ai_with_tool_calls:
                for tc in message.tool_calls:
                    tool_name = tc.get("name", "")
                    is_worker_call = tool_name in ALL_WORKER_TOOLS
                    if is_worker_call:
                        tool_id = tc.get("id", tool_name)
                        worker_request_map[tool_id] = tc.get("args", {}).get("request", "")

        for message in messages:
            is_tool_message = isinstance(message, ToolMessage)
            if is_tool_message and message.name in ALL_WORKER_TOOLS:
                worker_name = message.name.replace("ask_", "").replace("_agent", "")
                worker_request = worker_request_map.get(message.tool_call_id, "")
                worker_details.append(
                    WorkerToolCall(
                        worker_name=worker_name,
                        worker_request=worker_request,
                        worker_response=message.content,
                    )
                )

        return worker_details if worker_details else None
