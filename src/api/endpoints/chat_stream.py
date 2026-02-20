from fastapi import APIRouter
from sse_starlette import EventSourceResponse

from src.api.core import (
    APIKeyDep,
    DatasetManagerDep,
    KnowledgeRetrieverDep,
    LangfuseManagerDep,
    MemoryStoreDep,
    PromptManagerDep,
)
from src.api.handlers.chat_stream import ChatStreamHandler
from src.api.schemas import ChatStreamRequest
from src.config import settings


router = APIRouter(prefix="/chat", tags=["chat"])


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
    request: ChatStreamRequest,
    memory_store: MemoryStoreDep,
    langfuse_manager: LangfuseManagerDep,
    dataset_manager: DatasetManagerDep,
    prompt_manager: PromptManagerDep,
    knowledge_retriever: KnowledgeRetrieverDep,
) -> EventSourceResponse:
    handler = ChatStreamHandler(
        settings=settings,
        memory_store=memory_store,
        langfuse_manager=langfuse_manager,
        dataset_manager=dataset_manager,
        prompt_manager=prompt_manager,
        knowledge_retriever=knowledge_retriever,
    )
    return EventSourceResponse(handler.handle(request))
