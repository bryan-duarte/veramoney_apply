"""Chat endpoint for conversational AI interactions."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Request schema for the chat endpoint."""

    message: str = Field(..., description="The user's message to the assistant")
    session_id: Optional[str] = Field(
        None, description="Optional session ID for conversation continuity"
    )


class ToolCall(BaseModel):
    """Schema for a tool call made by the agent."""

    tool: str = Field(..., description="Name of the tool called")
    input: dict = Field(..., description="Input parameters passed to the tool")


class ChatResponse(BaseModel):
    """Response schema for the chat endpoint."""

    response: str = Field(..., description="The assistant's response")
    tool_calls: Optional[list[ToolCall]] = Field(
        None, description="List of tools called during processing"
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
        500: {"description": "Internal server error"},
    },
)
async def chat(request: ChatRequest) -> ChatResponse:
    """Handle chat messages and return AI-generated responses.

    This endpoint processes user messages through an AI agent that can
    utilize various tools (weather, stock prices) to provide accurate
    and grounded responses.

    Args:
        request: The chat request containing the user's message and
            optional session ID for conversation continuity.

    Returns:
        ChatResponse containing the assistant's response and any tool
        calls made during processing.

    Raises:
        HTTPException: If there's an error processing the request.
    """
    # TODO: Integrate with chat service/agent once implemented
    # For now, return a placeholder response
    try:
        return ChatResponse(
            response=f"Received your message: {request.message}. "
            "Agent integration pending.",
            tool_calls=None,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}",
        )
