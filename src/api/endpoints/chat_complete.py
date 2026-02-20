import logging
import uuid

from fastapi import APIRouter, HTTPException
from langchain.messages import AIMessage, HumanMessage
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.agent import create_conversational_agent, get_memory_store
from src.api.core import APIKeyDep, SettingsDep
from src.observability import (
    add_opening_message_to_dataset,
    add_stock_query_to_dataset,
    get_langfuse_client,
    initialize_langfuse_client,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat/complete", tags=["chat"])

MESSAGE_MIN_LENGTH = 1
MESSAGE_MAX_LENGTH = 32000


class ChatCompleteRequest(BaseModel):
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


class ToolCall(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "tool": "weather",
                    "input": {"city_name": "Montevideo", "country_code": "UY"},
                },
                {"tool": "stock_price", "input": {"ticker": "AAPL"}},
            ]
        }
    )

    tool: str = Field(..., description="Name of the tool called")
    input: dict = Field(..., description="Input parameters passed to the tool")


class ChatCompleteResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "response": "In Montevideo, Uruguay, it's currently 22C and partly cloudy "
                    "with 65% humidity. The wind speed is 12 km/h.",
                    "tool_calls": [
                        {
                            "tool": "weather",
                            "input": {"city_name": "Montevideo", "country_code": "UY"},
                        }
                    ],
                },
                {
                    "response": "Apple (AAPL) is currently trading at $178.52 USD, "
                    "up 1.23% from the previous close. Microsoft (MSFT) is at $378.91 USD, "
                    "down 0.45%.",
                    "tool_calls": [
                        {"tool": "stock_price", "input": {"ticker": "AAPL"}},
                        {"tool": "stock_price", "input": {"ticker": "MSFT"}},
                    ],
                },
            ]
        }
    )

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
    "The assistant can use weather and stock price tools to answer questions.\n\n"
    "**Features:**\n"
    "- Multi-turn conversation with context management\n"
    "- Automatic tool calling for weather and stock data\n"
    "- Structured response with tool call transparency",
    response_description="The complete assistant response including any tool calls made",
    responses={
        200: {
            "description": "Complete response from the assistant",
            "content": {
                "application/json": {
                    "example": {
                        "response": "In Montevideo, Uruguay, it's currently 22C and partly cloudy.",
                        "tool_calls": [
                            {"tool": "weather", "input": {"city_name": "Montevideo"}}
                        ],
                    }
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
async def chat_complete(
    api_key: APIKeyDep,
    settings: SettingsDep,
    request: ChatCompleteRequest,
) -> ChatCompleteResponse:
    try:
        memory_store = await get_memory_store(settings)

        langfuse_client = await initialize_langfuse_client()

        checkpointer = memory_store.get_checkpointer()
        existing_state = await checkpointer.aget_tuple(
            {"configurable": {"thread_id": request.session_id}}
        )
        existing_messages = (
            existing_state.values.get("messages", []) if existing_state else []
        )
        is_opening_message = len(existing_messages) == 0

        if is_opening_message and langfuse_client:
            expected_tools = _infer_expected_tools(request.message)
            add_opening_message_to_dataset(
                client=langfuse_client,
                message=request.message,
                session_id=request.session_id,
                expected_tools=expected_tools,
                model=settings.agent_model,
            )

        agent, config, langfuse_handler = await create_conversational_agent(
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
            return ChatCompleteResponse(
                response="No response generated.", tool_calls=None
            )

        final_message = messages[-1]
        if not isinstance(final_message, AIMessage):
            return ChatCompleteResponse(
                response="Unexpected response format.", tool_calls=None
            )

        tool_calls = _extract_tool_calls(messages)

        _collect_stock_queries_to_dataset(
            langfuse_client, tool_calls, request.message, request.session_id
        )

        lf_client = get_langfuse_client()
        if langfuse_handler and lf_client:
            lf_client.flush()
            logger.debug("Langfuse flushed session=%s", request.session_id)

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
        logger.exception(
            "chat_complete_error session=%s error=%s", request.session_id, str(error)
        )
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


WEATHER_KEYWORDS = ("weather", "temperature", "clima", "temperatura")
STOCK_KEYWORDS = ("stock", "price", "acción", "precio")
KNOWLEDGE_KEYWORDS = ("vera", "fintech", "regulation", "bank")
STOCK_TOOL_NAME = "get_stock_price"


def _infer_expected_tools(message: str) -> list[str]:
    message_lower = message.lower()
    expected: list[str] = []

    if any(word in message_lower for word in WEATHER_KEYWORDS):
        expected.append("weather")

    if any(word in message_lower for word in STOCK_KEYWORDS):
        expected.append("stock")

    if any(word in message_lower for word in KNOWLEDGE_KEYWORDS):
        expected.append("knowledge")

    return expected if expected else ["unknown"]


def _collect_stock_queries_to_dataset(
    client,
    tool_calls: list[ToolCall] | None,
    user_message: str,
    session_id: str,
) -> None:
    if client is None or not tool_calls:
        return

    for tc in tool_calls:
        is_stock_tool = tc.tool == STOCK_TOOL_NAME
        if is_stock_tool:
            ticker = tc.input.get("ticker", "UNKNOWN")
            add_stock_query_to_dataset(
                client=client,
                query=user_message,
                ticker=ticker,
                session_id=session_id,
            )
