# Agent Core Implementation

## Overview

Fix None dereference (C4), race condition (H3), and move constants from tools layer (M2).

## Files to Modify

- `src/agent/core/supervisor.py` - None check + race condition fix
- `src/agent/constants.py` - NEW: Move worker constants here
- `src/tools/constants.py` - Remove worker agent constants

## Implementation Guidelines

### None Dereference Fix (C4)

**Location**: `src/agent/core/supervisor.py` - `is_opening_message()` or equivalent check

**Current** (problematic):
```python
existing_messages = existing_state.checkpoint.get("channel_values", {}).get("messages", [])
```

**Fix**:
```python
is_state_missing = existing_state is None
is_checkpoint_missing = existing_state.checkpoint is None if existing_state else True

if is_state_missing or is_checkpoint_missing:
    return True

existing_messages = existing_state.checkpoint.get("channel_values", {}).get("messages", [])
```

### Race Condition Fix (H3)

**Location**: `src/agent/core/supervisor.py` - `SupervisorFactory` class

**Add lock in __init__**:
```python
def __init__(
    self,
    settings: Settings,
    langfuse_manager: LangfuseManager | None = None,
    prompt_manager: PromptManager | None = None,
    knowledge_retriever: KnowledgeRetriever | None = None,
):
    self._settings = settings
    self._memory_store: MemoryStore | None = None
    self._langfuse_manager = langfuse_manager
    self._prompt_manager: PromptManager | None = prompt_manager
    self._knowledge_retriever = knowledge_retriever
    self._init_lock = asyncio.Lock()  # ADD THIS
```

**Update _get_memory_store**:
```python
async def _get_memory_store(self) -> MemoryStore:
    if self._memory_store is not None:
        return self._memory_store

    async with self._init_lock:
        if self._memory_store is not None:
            return self._memory_store

        self._memory_store = MemoryStore(settings=self._settings)
        await self._memory_store.initialize()

    return self._memory_store
```

### Constants Move (M2)

**Create**: `src/agent/constants.py`

```python
ASK_WEATHER_AGENT = "ask_weather_agent"
ASK_STOCK_AGENT = "ask_stock_agent"
ASK_KNOWLEDGE_AGENT = "ask_knowledge_agent"

ALL_WORKER_TOOLS = [ASK_WEATHER_AGENT, ASK_STOCK_AGENT, ASK_KNOWLEDGE_AGENT]
```

**Update imports in**:
- `src/agent/core/supervisor.py`
- `src/agent/middleware/tool_error_handler.py`
- `src/api/handlers/chat_stream.py`

**Remove from**: `src/tools/constants.py` (keep TOOL_* constants, remove ASK_* constants)

## Dependencies

- `asyncio` (stdlib)

## Integration Notes

- Lock is instance-level, not class-level
- Each SupervisorFactory has its own lock
- Memory store initialization is now atomic
