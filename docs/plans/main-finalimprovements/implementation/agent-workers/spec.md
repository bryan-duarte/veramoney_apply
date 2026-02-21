# Agent Workers Implementation

## Overview

Update imports after prompts extraction (M1) - no structural changes per user decision on DRY (M3).

## Files to Modify

- `src/agent/workers/weather_worker.py` - Update prompt import
- `src/agent/workers/stock_worker.py` - Update prompt import
- `src/agent/workers/knowledge_worker.py` - Update prompt import

## Implementation Guidelines

### Update Prompt Imports

**In each worker file**, replace the local prompt constant with an import:

**weather_worker.py**:
```python
# Remove local WEATHER_WORKER_PROMPT definition
# Add import at top
from src.prompts import WEATHER_WORKER_PROMPT
```

**stock_worker.py**:
```python
# Remove local STOCK_WORKER_PROMPT definition
# Add import at top
from src.prompts import STOCK_WORKER_PROMPT
```

**knowledge_worker.py**:
```python
# Remove local KNOWLEDGE_WORKER_PROMPT definition
# Add import at top
from src.prompts import KNOWLEDGE_WORKER_PROMPT
```

### No Other Changes

Per user decision (Control pleno):
- **M3 (DRY violation)**: Keep as-is - each worker has specific variations
- **build_ask_X_agent_tool()**: Keep duplicated pattern

## Dependencies

- `src.prompts` module (created in M1 fix)

## Integration Notes

- Prompts are now centralized in `src/prompts/`
- Workers import prompts instead of defining them locally
- TYPE_CHECKING imports for PromptManager remain unchanged
