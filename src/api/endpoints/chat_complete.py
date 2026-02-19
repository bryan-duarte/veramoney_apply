import logging
import uuid

from fastapi import APIRouter, HTTPException
from langchain.messages import AIMessage, HumanMessage
from pydantic import BaseModel, Field, field_validator

from src.agent import create_conversational_agent, get_memory_store
from src.api.core import APIKeyDep, SettingsDep


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat/complete", tags=["chat"])

MESSAGE_MIN_LENGTH = 1
MESSAGE_MAX_LENGTH = 32000


class ChatCompleteRequest(BaseModel):
    message: str = Field(
        ...,
        description="The user's message to the assistant",
        min_length=MESSAGE_MIN_LENGTH,
        max_length=MESSAGE_MAX_LENGTH,
    )
    session_id: str = Field(
        ...,
        description="Session ID for conversation continuity (required UUID format)",
    )

    @field_validator("session_id")
    @classmethod
    def validate_session_id_format(cls, value: str) -> str:
        try:
            uuid.UUID(value)
        except ValueError as exc:
            raise ValueError("session_id must be a valid UUID") from exc
        return value


class ToolCall(BaseModel):
    tool: str = Field(..., description="Name of the tool called")
    input: dict = Field(..., description="Input parameters passed to the tool")


class ChatCompleteResponse(BaseModel):
    response: str = Field(..., description="The assistant's response")
    tool_calls: list[ToolCall] | None = Field(
        None,
        description="List of tools called during processing",
    )


@router.post(
    "",
    response_model=ChatCompleteResponse,
    summary="Send a chat message with complete response",
    description="Send a message to the AI assistant and receive a complete (non-streaming) response. "
    "The assistant can use weather and stock price tools to answer questions.",
    responses={
        200: {"description": "Complete response from the assistant"},
        400: {"description": "Invalid request body or missing session_id"},
        401: {"description": "Invalid or missing API key"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
    },
)
async def chat_complete(
    api_key: APIKeyDep,
    settings: SettingsDep,
    request: ChatCompleteRequest,
) -> ChatCompleteResponse:
    try:
        memory_store = await get_memory_store(settings)
        agent, config = await create_conversational_agent(
            settings=settings,
            memory_store=memory_store,
            session_id=request.session_id,
        )

        user_message = HumanMessage(content=request.message)

        result = await agent.ainvoke(
            {"messages": [user_message]},
            config=config,
        )

        messages = result.get("messages", [])
        if not messages:
            return ChatCompleteResponse(response="No response generated.", tool_calls=None)

        final_message = messages[-1]
        if not isinstance(final_message, AIMessage):
            return ChatCompleteResponse(response="Unexpected response format.", tool_calls=None)

        tool_calls = _extract_tool_calls(messages)

        logger.info(
            "chat_complete session=%s response_len=%d tool_calls=%d",
            request.session_id,
            len(final_message.content) if final_message.content else 0,
            len(tool_calls) if tool_calls else 0,
        )

        return ChatCompleteResponse(
            response=final_message.content or "",
            tool_calls=tool_calls,
        )

    except Exception as error:
        logger.exception("chat_complete_error session=%s error=%s", request.session_id, str(error))
        raise HTTPException(status_code=500, detail="Internal server error") from error


def _extract_tool_calls(messages: list) -> list[ToolCall] | None:
    tool_calls: list[ToolCall] = []
    seen_tools: set[tuple[str, str]] = set()

    for message in messages:
        if isinstance(message, AIMessage) and message.tool_calls:
            for tc in message.tool_calls:
                tool_name = tc.get("name", "")
                tool_args = tc.get("args", {})
                args_key = str(sorted(tool_args.items()))
                tool_key = (tool_name, args_key)

                if tool_key not in seen_tools:
                    seen_tools.add(tool_key)
                    tool_calls.append(ToolCall(tool=tool_name, input=tool_args))

    return tool_calls if tool_calls else None
