import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator


MESSAGE_MIN_LENGTH = 1
MESSAGE_MAX_LENGTH = 32000


class ChatRequest(BaseModel):
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


class ChatCompleteRequest(ChatRequest):
    pass


class ChatStreamRequest(ChatRequest):
    pass


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


class WorkerToolCall(BaseModel):
    worker_name: str = Field(..., description="Worker specialist name: weather, stock, or knowledge")
    worker_request: str = Field(..., description="Request sent to the worker specialist")
    worker_response: str = Field(..., description="Worker specialist's final response")
    duration_ms: float | None = Field(None, description="Worker execution time in milliseconds")


class ChatCompleteResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "response": "In Montevideo, Uruguay, it's currently 22C and partly cloudy "
                    "with 65% humidity. The wind speed is 12 km/h.",
                    "tool_calls": [
                        {
                            "tool": "ask_weather_agent",
                            "input": {"request": "What is the weather in Montevideo?"},
                        }
                    ],
                    "worker_details": [
                        {
                            "worker_name": "weather",
                            "worker_request": "What is the weather in Montevideo?",
                            "worker_response": "In Montevideo, it's currently 22C and partly cloudy.",
                            "duration_ms": None,
                        }
                    ],
                },
            ]
        }
    )

    response: str = Field(..., description="The supervisor's synthesized response")
    tool_calls: list[ToolCall] | None = Field(
        None,
        description="List of worker tools invoked by the supervisor",
    )
    worker_details: list[WorkerToolCall] | None = Field(
        None,
        description="Detailed information about each worker specialist invocation",
    )
