# Observability Module Implementation

## Overview

Create the complete Langfuse integration layer under `src/observability/` with multi-module structure.

## Files to Create

| File | Purpose |
|------|---------|
| `src/observability/__init__.py` | Public API exports |
| `src/observability/client.py` | Langfuse client singleton |
| `src/observability/handler.py` | CallbackHandler factory |
| `src/observability/datasets.py` | Dataset management service |
| `src/observability/prompts.py` | Prompt sync service (chat-type) |

---

## Module: client.py

### Purpose

Singleton Langfuse client with graceful degradation.

### Responsibilities

- Initialize Langfuse client from settings
- Check if Langfuse is configured (keys present)
- Provide singleton access via `get_langfuse_client()`
- Handle connection failures gracefully
- Log warnings on failures (not errors)

### Key Functions

```
get_langfuse_client() -> Langfuse | None
    Returns singleton client or None if not configured

is_langfuse_enabled() -> bool
    Check if client is available and healthy

create_langfuse_client(settings: Settings) -> Langfuse | None
    Factory function for client creation
```

### Error Handling

- If keys missing: return None, log debug
- If connection fails: return None, log warning
- Never raise exceptions to caller

### Constants

```
LANGFUSE_CLIENT_NAME = "veramoney-api"
TRACE_NAME_PREFIX = "veramoney-"
```

---

## Module: handler.py

### Purpose

Factory for LangChain CallbackHandler integration.

### Responsibilities

- Create CallbackHandler instances
- Configure handler with session_id as trace_id
- Set trace name with `veramoney-` prefix
- Handle None client gracefully

### Key Functions

```
get_langfuse_handler(
    client: Langfuse | None,
    session_id: str,
    trace_name: str = "veramoney-chat"
) -> CallbackHandler | None
    Returns configured handler or None if client unavailable
```

### Configuration

- `trace_id` = session_id
- `trace_name` = "veramoney-chat" (default)
- `public_key` / `secret_key` from client
- `host` from client

---

## Module: datasets.py

### Purpose

Manage dataset creation and item insertion.

### Responsibilities

- Create USER_OPENING_MESSAGES dataset lazily
- Create STOCK_QUERIES dataset lazily
- Add items to datasets with proper structure
- Handle failures gracefully (log warning, continue)

### Constants

```
DATASET_USER_OPENING_MESSAGES = "USER_OPENING_MESSAGES"
DATASET_STOCK_QUERIES = "STOCK_QUERIES"
```

### Key Functions

```
add_opening_message_to_dataset(
    client: Langfuse | None,
    message: str,
    session_id: str,
    expected_tools: list[str],
    model: str
) -> None
    Adds opening message to dataset (fire-and-forget)

add_stock_query_to_dataset(
    client: Langfuse | None,
    query: str,
    ticker: str,
    session_id: str
) -> None
    Adds stock query to dataset (fire-and-forget)

_create_dataset_if_not_exists(
    client: Langfuse,
    name: str
) -> None
    Internal helper for lazy creation
```

### Dataset Item Structure

**USER_OPENING_MESSAGES:**
```
input: { message, session_id }
expected_output: None
metadata: { timestamp, model, expected_tools }
```

**STOCK_QUERIES:**
```
input: { query, ticker }
expected_output: None
metadata: { timestamp, session_id }
```

---

## Module: prompts.py

### Purpose

Sync and fetch system prompts from Langfuse with chat-type structure.

### CRITICAL: Use Chat-Type Prompts

The prompt must be created as `type="chat"` for:
- Proper LangChain integration via `get_langchain_prompt()`
- Placeholder support for `chat_history`
- Variable interpolation at runtime
- Trace linking with prompt metadata

### Constants

```
PROMPT_NAME_VERA_SYSTEM = "vera-system-prompt"
PROMPT_TYPE = "chat"
```

### Key Functions

#### Date Formatting

```
def format_current_date() -> str:
    current = datetime.now()
    return current.strftime("%d %B, %y")
    # Example: "20 February, 26"
```

#### Prompt Sync

```
sync_prompt_to_langfuse(
    client: Langfuse | None,
    prompt_name: str,
    system_content: str
) -> None
    Creates chat-type prompt if missing:
    - type: "chat"
    - prompt: [
        {"role": "system", "content": "{{system_content}}"},
        {"type": "placeholder", "name": "chat_history"},
        {"role": "user", "content": "{{user_message}}"}
      ]
```

#### Prompt Fetch with Variables

```
get_compiled_prompt(
    client: Langfuse | None,
    fallback_system: str,
    current_date: str,
    model_name: str,
    version: str,
    user_message: str,
    chat_history: list[dict] | None = None
) -> tuple[ChatPromptTemplate, dict] | None
    Returns LangChain template with compiled variables

    Returns:
        (langchain_prompt, metadata) or None if unavailable
```

#### Get Prompt for LangChain

```
get_langchain_prompt(
    client: Langfuse | None,
    fallback_system: str
) -> ChatPromptTemplate
    Returns ChatPromptTemplate with:
    - System message with {{current_date}}, {{model_name}}, {{version}}
    - MessagesPlaceholder for chat_history
    - Human message for user input

    Always returns valid template (uses fallback if needed)
```

### Prompt Template Structure

The Langfuse prompt stores the template with variables:

```
[
    {
        "role": "system",
        "content": "<temporal_context>\nToday's date: {{current_date}}\n</temporal_context>\n\n<identity>\nYou are Vera AI v{{version}}, an AI-powered financial assistant...\nBuilt on: {{model_name}}\n...</identity>\n\n<!-- Rest of VERA_FALLBACK_SYSTEM_PROMPT with XML structure -->"
    },
    {
        "type": "placeholder",
        "name": "chat_history"
    },
    {
        "role": "user",
        "content": "{{user_message}}"
    }
]
```

### Variable Injection Flow

```
1. At startup: sync_prompt_to_langfuse()
   - Creates prompt with template (variables as {{var}})

2. At request time: get_compiled_prompt()
   - Fetch prompt from Langfuse
   - Format current_date: datetime.now().strftime("%d %B, %y")
   - Get model_name from settings
   - Get chat_history from checkpointer
   - Compile with all variables
   - Convert to ChatPromptTemplate

3. In agent: Use template in create_agent()
   - Pass template with metadata for trace linking
```

### Fallback Behavior

If Langfuse unavailable:

```
def _create_fallback_template(system_content: str) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        ("system", system_content),
        MessagesPlaceholder("chat_history"),
        ("human", "{user_message}")
    ])
```

Note: Fallback does NOT include dynamic date injection (uses hardcoded prompt).

### Error Handling

- Langfuse fetch fails: use fallback template
- Log warning, not error
- Never block agent creation

---

## Module: __init__.py

### Public Exports

```
__all__ = [
    # Client
    "get_langfuse_client",
    "is_langfuse_enabled",

    # Handler
    "get_langfuse_handler",

    # Datasets
    "add_opening_message_to_dataset",
    "add_stock_query_to_dataset",
    "DATASET_USER_OPENING_MESSAGES",
    "DATASET_STOCK_QUERIES",

    # Prompts
    "get_compiled_prompt",
    "get_langchain_prompt",
    "sync_prompt_to_langfuse",
    "format_current_date",
    "PROMPT_NAME_VERA_SYSTEM",

    # Constants
    "TRACE_NAME_PREFIX",
]
```

---

## Integration Notes

### Dependencies

- `langfuse` package (already installed)
- `langfuse.langchain.CallbackHandler`
- `langchain_core.prompts.ChatPromptTemplate`
- `langchain_core.prompts.MessagesPlaceholder`
- `src.config.settings.Settings`

### Import Pattern

```
from src.observability import (
    get_langfuse_client,
    get_langfuse_handler,
    add_opening_message_to_dataset,
    get_compiled_prompt,
    format_current_date,
)
```

### Error Logging

All modules use:

```
logger = logging.getLogger(__name__)
logger.warning("Langfuse operation failed: %s", error)
```

Never use `logger.error()` or `logger.exception()` - Langfuse failures are warnings, not errors.

---

## Testing Checklist

- [ ] Prompt created as `type="chat"` in Langfuse UI
- [ ] Variables compile correctly (date, model, version)
- [ ] Placeholder expands with chat_history
- [ ] Fallback works when Langfuse unavailable
- [ ] Trace metadata includes prompt version
- [ ] Date updates on each request (not cached)
