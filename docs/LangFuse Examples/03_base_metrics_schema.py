"""
LangFuse Metrics Schema - Structured Tracking

This file demonstrates structured schemas for processing history and metrics
that can be correlated with LangFuse traces.
Source: clickbait project - app/services/metrics/schemas/base_schema.py

Key patterns:
- Dual trace IDs (langfuse_trace_id + trace_id)
- Structured error tracking
- Task correlation with Celery task IDs
- Duration and retry tracking
"""

from typing import Literal

from pydantic import BaseModel, Field


class DetailedErrorSchema(BaseModel):
    """Structured error details for failed operations.

    Provides consistent error reporting across all operations,
    with stage tracking for debugging complex pipelines.
    """

    error_code: str = Field(..., description="Exception class name or error code")
    error_message: str = Field(..., description="Human-readable error message")
    error_stage: str | None = Field(None, description="Stage where error occurred")
    recoverable: bool | None = Field(None, description="Whether error is recoverable")


class BaseMetricsSchema(BaseModel):
    """Base schema for all processing history records.

    This schema provides the foundation for tracking operations
    and correlating them with LangFuse traces.

    Key fields for LangFuse correlation:
    - langfuse_trace_id: External trace ID from LangFuse
    - run_id: Internal execution identifier
    - task_id: Celery/background task identifier

    Usage:
        class ChatAttemptSchema(BaseMetricsSchema):
            entity_type: str = Field(default="chat_message")
            message_length: int | None = None
            tools_called: list[str] | None = None

        schema = ChatAttemptSchema(
            entity_id=123,
            status="success",
            run_id="abc123",
            langfuse_trace_id="trace-xyz",
            duration_ms=1500
        )
    """

    entity_type: str = Field(..., description="Type of entity being processed")
    entity_id: int = Field(..., description="ID of the entity")
    status: Literal["success", "failure", "partial", "error"] = Field(
        ..., description="Operation status"
    )

    task_id: str | None = Field(None, description="Celery task ID")
    run_id: str | None = Field(None, description="Execution run ID")
    langfuse_trace_id: str | None = Field(None, description="LangFuse trace ID")
    trace_id: str | None = Field(None, description="Generic trace ID")

    retry_count: int = Field(0, description="Number of retry attempts")
    duration_ms: int | None = Field(None, description="Execution time in milliseconds")

    error: DetailedErrorSchema | None = Field(
        None, description="Error details if status is failure"
    )


# ============================================================================
# SPECIALIZED SCHEMA EXAMPLES
# ============================================================================


class ChatAttemptSchema(BaseMetricsSchema):
    """Schema for chat attempt records."""

    entity_type: str = Field(default="chat_message")
    message_length: int | None = None
    response_length: int | None = None
    tools_called: list[str] | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None


class ToolExecutionSchema(BaseMetricsSchema):
    """Schema for tool execution records."""

    entity_type: str = Field(default="tool_execution")
    tool_name: str | None = None
    input_params: dict | None = None
    output_size_bytes: int | None = None


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    success_record = ChatAttemptSchema(
        entity_type="chat_message",
        entity_id=12345,
        status="success",
        run_id="run-abc123",
        langfuse_trace_id="trace-xyz789",
        task_id="task-456",
        duration_ms=1500,
        message_length=256,
        response_length=512,
        tools_called=["weather", "stock_price"],
        input_tokens=150,
        output_tokens=300,
    )

    print(f"Success record: {success_record.model_dump_json(indent=2)}")

    error_record = ChatAttemptSchema(
        entity_type="chat_message",
        entity_id=12346,
        status="failure",
        run_id="run-def456",
        langfuse_trace_id="trace-error123",
        duration_ms=500,
        error=DetailedErrorSchema(
            error_code="ExternalAPIError",
            error_message="Weather API timeout after 30 seconds",
            error_stage="tool_execution",
            recoverable=True,
        ),
    )

    print(f"\nError record: {error_record.model_dump_json(indent=2)}")
