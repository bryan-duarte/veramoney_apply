# API Core Implementation

## Overview

Fix timing attack (H1), rate limit key sanitization (M8), and add log sanitization helper (M9).

## Files to Modify

- `src/api/core/dependencies.py` - Timing attack fix
- `src/api/core/rate_limiter.py` - Key sanitization
- `src/utils/logging.py` - NEW: Sanitization helper

## Implementation Guidelines

### Timing Attack Fix (H1)

**Location**: `src/api/core/dependencies.py` - `get_api_key()` function

**Current** (vulnerable):
```python
is_api_key_invalid = x_api_key != settings.api_key
```

**Fix**:
```python
import secrets

def get_api_key(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> str:
    is_api_key_missing = x_api_key is None
    is_api_key_invalid = not secrets.compare_digest(x_api_key or "", settings.api_key)

    if is_api_key_missing or is_api_key_invalid:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    return x_api_key
```

### Rate Limit Key Sanitization (M8)

**Location**: `src/api/core/rate_limiter.py`

**Add validation**:
```python
import re

API_KEY_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,128}$')

def get_rate_limit_key(request: Request) -> str:
    api_key = request.headers.get("X-API-Key")

    if api_key:
        is_valid_format = bool(API_KEY_PATTERN.match(api_key))
        if is_valid_format:
            return f"apikey:{api_key}"
        # Fall back to IP for invalid format

    return f"ip:{get_remote_address(request)}"
```

### Log Sanitization Helper (M9)

**Create**: `src/utils/logging.py`

```python
import re

CONTROL_CHAR_PATTERN = re.compile(r'[\x00-\x1f\x7f-\x9f]')

def sanitize_for_log(value: str, max_length: int = 100) -> str:
    """
    Sanitize a string for safe logging.

    - Escapes control characters (newlines, tabs, etc.)
    - Truncates to max_length
    - Returns safe string for log output
    """
    if not value:
        return ""

    sanitized = CONTROL_CHAR_PATTERN.sub(
        lambda m: f'\\x{ord(m.group()):02x}',
        value
    )

    is_too_long = len(sanitized) > max_length
    if is_too_long:
        sanitized = sanitized[:max_length] + "..."

    return sanitized
```

**Update handlers to use sanitizer**:

In `src/api/handlers/chat_stream.py` and `src/api/handlers/chat_complete.py`:

```python
from src.utils.logging import sanitize_for_log

logger.info(
    "chat_complete session=%s response_len=%d",
    sanitize_for_log(request.session_id),
    len(response.content) if response else 0,
)
```

## Dependencies

- `secrets` (stdlib)
- `re` (stdlib)

## Integration Notes

- Timing attack fix affects all API key validation
- Rate limit validation falls back to IP for invalid formats
- Log sanitization should be used for all user-provided values in logs
