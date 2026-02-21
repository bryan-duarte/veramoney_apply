# Config & Schemas Implementation

## Overview

Consolidate duplicate request schemas (M4) and add ChatRequest base class.

## Files to Modify

- `src/api/schemas.py` - Schema consolidation

## Implementation Guidelines

### Schema Consolidation (M4)

**Location**: `src/api/schemas.py`

**Create base class**:
```python
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

MESSAGE_MIN_LENGTH = 1
MESSAGE_MAX_LENGTH = 32000


class ChatRequest(BaseModel):
    """Base request for chat endpoints."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"message": "What's the weather in Montevideo?", "session_id": "550e8400-e29b-41d4-a716-446655440000"}
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
            UUID(value)
        except ValueError as exc:
            raise ValueError("session_id must be a valid UUID") from exc
        return value
```

**Update ChatCompleteRequest**:
```python
class ChatCompleteRequest(ChatRequest):
    """Request for non-streaming chat endpoint."""

    pass
```

**Update ChatStreamRequest**:
```python
class ChatStreamRequest(ChatRequest):
    """Request for streaming chat endpoint."""

    pass
```

### Remove Duplicated Code

- Remove duplicated `message` field definition
- Remove duplicated `session_id` field definition
- Remove duplicated `validate_session_id_format` validator

### Update Endpoint Imports

**No changes needed** - endpoints import the same class names, just from updated base.

## Dependencies

- No new dependencies

## Integration Notes

- Both request classes now inherit from ChatRequest
- They can diverge in the future by adding endpoint-specific fields
- Example schemas are preserved in base class
- Validation logic is centralized
