import json
import logging
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter
from langchain.messages import AIMessageChunk, HumanMessage, ToolMessage
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sse_starlette import EventSourceResponse

from src.agent import create_conversational_agent, get_memory_store
from src.api.core import APIKeyDep, SettingsDep
from src.config import Settings


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

MESSAGE_MIN_LENGTH = 1
MESSAGE_MAX_LENGTH = 32000


class ChatStreamRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "message": "What is the current weather in Montevideo, Uruguay?",
                    "session_id": "550e8400-e29b-41d4-a716-446655440000",
                },
                {
                    "message": "What is the stock price of Apple (AAPL) and Microsoft (MSFT)?",
                    "session_id": "660e8400-e29b-41d4-a716-446655440001",
                },
            ]
        }
    )

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


@router.post(
    "",
    summary="Send a chat message with streaming response",
    description="Send a message to the AI assistant and receive a streaming response via Server-Sent Events. "
    "The assistant can use weather and stock price tools to answer questions.\n\n"
    "**Features:**\n"
    "- Real-time token streaming for faster perceived response\n"
    "- Tool call events with arguments\n"
    "- Tool result events with responses\n\n"
    "**SSE Event Types:**\n"
    '- `token`: Content chunk ` {"content": "..."}`\n'
    '- `tool_call`: Tool invocation `{"tool": "...", "args": {...}}`\n'
    '- `tool_result`: Tool response `{"tool": "...", "result": "..."}`\n'
    "- `done`: Stream completion `{}`\n"
    '- `error`: Error occurred `{"message": "..."}`',
    response_description="Server-Sent Events stream with token, tool_call, tool_result, done, and error events",
    responses={
        200: {
            "description": "Streaming response from the assistant (SSE)",
            "content": {
                "text/event-stream": {
                    "example": (
                        'event: token\\ndata: {"content": "In Montevideo"}\\n\\n'
                        'event: tool_call\\ndata: {"tool": "weather", "args": {"city_name": "Montevideo"}}\\n\\n'
                        'event: tool_result\\ndata: {"tool": "weather", "result": "22C, partly cloudy"}\\n\\n'
                        "event: done\\ndata: {}\\n\\n"
                    )
                }
            },
        },
        400: {
            "description": "Invalid request body or malformed session_id (must be UUID)"
        },
        401: {"description": "Invalid or missing X-API-Key header"},
        429: {"description": "Rate limit exceeded (60 requests/minute)"},
        500: {"description": "Internal server error during processing"},
    },
)
async def chat_stream(
    api_key: APIKeyDep,
    settings: SettingsDep,
    request: ChatStreamRequest,
) -> EventSourceResponse:
    return EventSourceResponse(
        _generate_stream(
            message=request.message,
            session_id=request.session_id,
            settings=settings,
        ),
    )


async def _generate_stream(
    message: str,
    session_id: str,
    settings: Settings,
) -> AsyncGenerator[dict[str, str], None]:
    try:
        memory_store = await get_memory_store(settings)
        agent, config = await create_conversational_agent(
            settings=settings,
            memory_store=memory_store,
            session_id=session_id,
        )

        user_message = HumanMessage(content=message)

        async for stream_mode, data in agent.astream(
            {"messages": [user_message]},
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
                            yield {
                                "event": "tool_call",
                                "data": json.dumps(
                                    {
                                        "tool": tool_call.get("name"),
                                        "args": tool_call.get("args", {}),
                                    }
                                ),
                            }
            elif stream_mode == "updates":
                for source, update in data.items():
                    if source == "tools":
                        messages = update.get("messages", [])
                        for msg in messages:
                            if isinstance(msg, ToolMessage):
                                yield {
                                    "event": "tool_result",
                                    "data": json.dumps(
                                        {
                                            "tool": getattr(msg, "name", "unknown"),
                                            "result": msg.content,
                                        }
                                    ),
                                }

        yield {"event": "done", "data": "{}"}

    except Exception as error:
        logger.exception("stream_error session=%s error=%s", session_id, str(error))
        yield {
            "event": "error",
            "data": json.dumps({"message": "An error occurred during processing"}),
        }
