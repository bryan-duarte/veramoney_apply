# Configuration Implementation

## Overview

Add configuration settings for worker agents and update environment templates.

## Files to Modify

| File | Changes |
|------|---------|
| `src/config/settings.py` | Add worker model and timeout settings |
| `src/tools/constants.py` | Add worker tool name constants |
| `.env.example` | Add WORKER_MODEL and WORKER_TIMEOUT |

## Implementation Guidelines

### settings.py - New Fields

```
Settings Class Additions:

Worker Model Configuration:
  worker_model: str = Field(
      default="gpt-5-nano-2025-08-07",
      description="OpenAI model for worker agents (specialists)",
  )

  worker_timeout_seconds: float = Field(
      default=15.0,
      description="Timeout for worker agent API calls in seconds",
  )

Computed Fields (optional):
  @computed_field
  def worker_enabled(self) -> bool:
      return True  # Workers always enabled in v2
```

### constants.py - Worker Tool Names

```
Tool Constants Additions:

Worker Tool Names:
  ASK_WEATHER_AGENT = "ask_weather_agent"
  ASK_STOCK_AGENT = "ask_stock_agent"
  ASK_KNOWLEDGE_AGENT = "ask_knowledge_agent"

  ALL_WORKER_TOOLS = [
      ASK_WEATHER_AGENT,
      ASK_STOCK_AGENT,
      ASK_KNOWLEDGE_AGENT,
  ]

Worker Service Names (for error messages):
  WORKER_SERVICE_NAMES: dict[str, str] = {
      ASK_WEATHER_AGENT: "weather specialist",
      ASK_STOCK_AGENT: "stock specialist",
      ASK_KNOWLEDGE_AGENT: "knowledge specialist",
  }
```

### .env.example - New Variables

```
Additions to .env.example:

# Worker Agent Configuration
WORKER_MODEL=gpt-5-nano-2025-08-07
WORKER_TIMEOUT_SECONDS=15
```

## Dependencies

```
src/config/settings.py
└── No new dependencies

src/tools/constants.py
└── No new dependencies
```

## Integration Notes

1. Worker model is separate from supervisor model for cost optimization
2. Timeout is shorter for workers (15s vs 30s for supervisor)
3. Constants used in error messages and logging
4. Settings accessible via dependency injection (existing pattern)
