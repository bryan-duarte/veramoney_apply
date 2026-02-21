# Agent Middleware Implementation

## Overview

Update constants import after M2 move. No structural changes per user decision on H9 (LSP violation).

## Files to Modify

- `src/agent/middleware/tool_error_handler.py` - Update constants import

## Implementation Guidelines

### Update Constants Import

**Location**: `src/agent/middleware/tool_error_handler.py`

**Current**:
```python
from src.tools.constants import TOOL_SERVICE_NAMES
```

**Fix** (after M2 constants move):
```python
from src.agent.constants import ASK_WEATHER_AGENT, ASK_STOCK_AGENT, ASK_KNOWLEDGE_AGENT
from src.tools.constants import TOOL_SERVICE_NAMES

# TOOL_SERVICE_NAMES stays in tools/constants.py as it maps tool names to service names
```

### No Changes to Exception Handling

Per user decision (Control pleno):
- **H9 (LSP violation)**: Keep as-is - catching all exceptions is intentional for error resilience
- The middleware catches `Exception` broadly to prevent tool errors from crashing the agent

## Dependencies

- No new dependencies

## Integration Notes

- TOOL_SERVICE_NAMES remains in tools/constants.py (it maps tool names, not agent names)
- ASK_*_AGENT constants are the ones moving to agent layer
