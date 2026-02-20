from fastapi import APIRouter

from src.api.core import (
    APIKeyDep,
    DatasetManagerDep,
    KnowledgeRetrieverDep,
    LangfuseManagerDep,
    MemoryStoreDep,
    PromptManagerDep,
)
from src.api.handlers.chat_complete import ChatCompleteHandler
from src.api.schemas import ChatCompleteRequest, ChatCompleteResponse
from src.config import settings


router = APIRouter(prefix="/chat/complete", tags=["chat"])


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
    request: ChatCompleteRequest,
    memory_store: MemoryStoreDep,
    langfuse_manager: LangfuseManagerDep,
    dataset_manager: DatasetManagerDep,
    prompt_manager: PromptManagerDep,
    knowledge_retriever: KnowledgeRetrieverDep,
) -> ChatCompleteResponse:
    handler = ChatCompleteHandler(
        settings=settings,
        memory_store=memory_store,
        langfuse_manager=langfuse_manager,
        dataset_manager=dataset_manager,
        prompt_manager=prompt_manager,
        knowledge_retriever=knowledge_retriever,
    )
    return await handler.handle(request)
