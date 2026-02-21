# Observability Implementation

## Overview

Fix sync blocking calls (H4) by wrapping in asyncio.to_thread() and extract prompts to break circular dependency (M1).

## Files to Modify

- `src/observability/prompts.py` - Async wrapping
- `src/prompts/__init__.py` - NEW
- `src/prompts/system.py` - NEW
- `src/prompts/workers.py` - NEW

## Implementation Guidelines

### Sync Blocking Fix (H4)

**Location**: `src/observability/prompts.py`

**Pattern for all sync Langfuse client calls**:

```python
import asyncio

async def sync_supervisor_prompt(self) -> None:
    ...

    existing_system_content = await asyncio.to_thread(
        self._fetch_existing_system_content, prompt_name
    )

    ...

    await asyncio.to_thread(
        self._client.create_prompt,
        name=prompt_name,
        type=self.PROMPT_TYPE,
        prompt=expected_messages,
        labels=["production"],
    )
```

**Methods to update**:
- `sync_supervisor_prompt()` - wrap `self._client.create_prompt()`
- `sync_worker_prompts()` - wrap `self._client.create_prompt()`
- `_fetch_existing_system_content()` - if it makes sync calls
- Any other methods that call `self._client.*` synchronously

### Circular Dependency Fix (M1)

**Create**: `src/prompts/__init__.py`

```python
from src.prompts.system import SUPERVISOR_SYSTEM_PROMPT_FALLBACK, VERA_FALLBACK_SYSTEM_PROMPT
from src.prompts.workers import KNOWLEDGE_WORKER_PROMPT, STOCK_WORKER_PROMPT, WEATHER_WORKER_PROMPT

__all__ = [
    "SUPERVISOR_SYSTEM_PROMPT_FALLBACK",
    "VERA_FALLBACK_SYSTEM_PROMPT",
    "WEATHER_WORKER_PROMPT",
    "STOCK_WORKER_PROMPT",
    "KNOWLEDGE_WORKER_PROMPT",
]
```

**Create**: `src/prompts/system.py`

```python
VERA_FALLBACK_SYSTEM_PROMPT = """..."""  # Move from src/agent/core/prompts.py

SUPERVISOR_SYSTEM_PROMPT_FALLBACK = """..."""  # Move from src/agent/core/prompts.py
```

**Create**: `src/prompts/workers.py`

```python
WEATHER_WORKER_PROMPT = """..."""  # Move from src/agent/workers/weather_worker.py

STOCK_WORKER_PROMPT = """..."""  # Move from src/agent/workers/stock_worker.py

KNOWLEDGE_WORKER_PROMPT = """..."""  # Move from src/agent/workers/knowledge_worker.py
```

### Update Imports

**In `src/observability/prompts.py`**:
```python
from src.prompts import (
    KNOWLEDGE_WORKER_PROMPT,
    STOCK_WORKER_PROMPT,
    SUPERVISOR_SYSTEM_PROMPT_FALLBACK,
    VERA_FALLBACK_SYSTEM_PROMPT,
    WEATHER_WORKER_PROMPT,
)
```

**In `src/agent/workers/weather_worker.py`**:
```python
from src.prompts import WEATHER_WORKER_PROMPT
```

**In `src/agent/workers/stock_worker.py`**:
```python
from src.prompts import STOCK_WORKER_PROMPT
```

**In `src/agent/workers/knowledge_worker.py`**:
```python
from src.prompts import KNOWLEDGE_WORKER_PROMPT
```

**In `src/agent/core/prompts.py`**:
- Remove prompt constants (move to src/prompts/system.py)
- May become empty and deletable

## Dependencies

- `asyncio` (stdlib)

## Integration Notes

- `asyncio.to_thread()` runs sync code in a thread pool
- Prompts module has NO imports from app code (pure constants)
- This breaks the circular dependency completely
