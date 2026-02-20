# Error Management

Errors are state, not just logs. Build predictable systems that are transparent about failures.

## Core Principles

1. **Model Errors Explicitly** - Function return values must reflect errors
2. **Return Structured State** - Include `status`, `data`, and `errors` fields
3. **Error-Based Control Flow** - Calling code must check and react to status
4. **Eliminate "Log and Forget"** - `except` blocks must update return state

## Structured Response Pattern

```python
from pydantic import BaseModel
from enum import Enum

class OperationStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"

class OperationResult(BaseModel, generic=T]):
    status: OperationStatus
    data: T | None = None
    errors: list[str] = []
```

## Examples

```python
# WRONG: Log and forget
async def fetch_user(user_id: str) -> User | None:
    try:
        response = await client.get(f"/users/{user_id}")
        return User(**response.json())
    except Exception as e:
        logging.error(f"Failed to fetch user: {e}")
        return None

# CORRECT: Return structured state
async def fetch_user(user_id: str) -> OperationResult[User]:
    try:
        response = await client.get(f"/users/{user_id}")
        user = User(**response.json())
        return OperationResult(status=OperationStatus.SUCCESS, data=user)
    except httpx.HTTPError as e:
        return OperationResult(
            status=OperationStatus.FAILED,
            errors=[f"HTTP error: {e}"]
        )
    except pydantic.ValidationError as e:
        return OperationResult(
            status=OperationStatus.FAILED,
            errors=[f"Validation error: {e}"]
        )
```

## Caller Pattern

```python
result = await fetch_user(user_id="123")

if result.status == OperationStatus.FAILED:
    logger.warning("User fetch failed", extra={"errors": result.errors})
    raise HTTPException(status_code=500, detail=result.errors)

return result.data
```

## Checklist

- [ ] Identify `except` blocks that only log errors
- [ ] Ensure all error paths update return state
- [ ] Verify callers check status before using data
