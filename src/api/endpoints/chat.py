import uuid

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field, field_validator

from src.api.core import APIKeyDep


router = APIRouter(prefix="/chat", tags=["chat"])

MESSAGE_MIN_LENGTH = 1
MESSAGE_MAX_LENGTH = 32000


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        description="The user's message to the assistant",
        min_length=MESSAGE_MIN_LENGTH,
        max_length=MESSAGE_MAX_LENGTH,
    )
    session_id: str | None = Field(
        None,
        description="Optional session ID for conversation continuity",
    )

    @field_validator("session_id")
    @classmethod
    def validate_session_id_format(cls, value: str | None) -> str | None:
        if value is None:
            return value
        try:
            uuid.UUID(value)
        except ValueError as exc:
            raise ValueError("session_id must be a valid UUID") from exc
        return value


class ToolCall(BaseModel):
    tool: str = Field(..., description="Name of the tool called")
    input: dict = Field(..., description="Input parameters passed to the tool")


class ChatResponse(BaseModel):
    response: str = Field(..., description="The assistant's response")
    tool_calls: list[ToolCall] | None = Field(
        None,
        description="List of tools called during processing",
    )


@router.post(
    "",
    response_model=ChatResponse,
    summary="Send a chat message",
    description="Send a message to the AI assistant and receive a response. "
    "The assistant can use weather and stock price tools to answer questions.",
    responses={
        200: {"description": "Successful response from the assistant"},
        400: {"description": "Invalid request body"},
        401: {"description": "Invalid or missing API key"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
    },
)
async def chat(
    request: Request,
    api_key: APIKeyDep,
    chat_request: ChatRequest,
) -> ChatResponse:
    return ChatResponse(
        response=f"Received your message: {chat_request.message}. Agent integration pending.",
        tool_calls=None,
    )
