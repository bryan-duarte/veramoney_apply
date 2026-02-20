# Observability Implementation

## Overview

Extend Langfuse integration to support worker agents with nested traces and worker prompt management.

## Files to Modify

| File | Changes |
|------|---------|
| `src/observability/prompts.py` | Add worker prompt management |
| `src/agent/core/prompts.py` | Add worker prompt definitions |
| `src/agent/workers/*.py` | Use PromptManager for prompts |

## Implementation Guidelines

### prompts.py - Worker Prompt Management

```
PromptManager Changes:

New Prompt Names:
  - vera-weather-worker
  - vera-stock-worker
  - vera-knowledge-worker

New Methods:
  async sync_worker_prompts() -> None:
    - Sync all three worker prompts to Langfuse
    - Create if not exists, skip if exists
    - Label as "production"

  get_worker_prompt(worker_name: str) -> tuple[str, dict]:
    - Fetch prompt from Langfuse by name
    - Apply template variables (current_date)
    - Return (compiled_prompt, metadata)
    - Fallback to local constant if Langfuse unavailable

  _apply_worker_template_vars(prompt: str, current_date: str) -> str:
    - Replace {{current_date}} placeholder
    - Worker prompts don't need model_name/version
```

### Worker Prompt Definitions

```
Location: src/agent/core/prompts.py

WEATHER_WORKER_PROMPT:
  You are a weather information specialist for VeraMoney.

  Your only tool is get_weather. Use it to:
  - Get current weather for any city
  - Handle country code disambiguation when needed
  - Report temperature in Celsius

  Always:
  - Parse location from natural language
  - Include temperature and conditions
  - Be concise and accurate

  Current date: {{current_date}}

STOCK_WORKER_PROMPT:
  You are a stock price specialist for VeraMoney.

  Your only tool is get_stock_price. Use it to:
  - Get current stock prices by ticker symbol
  - Handle company name to ticker resolution

  Always:
  - Parse ticker symbols from company names
  - Include price, change, and percentage
  - Be concise and accurate

  Current date: {{current_date}}

KNOWLEDGE_WORKER_PROMPT:
  You are a knowledge base specialist for VeraMoney.

  Your only tool is search_knowledge. Use it to:
  - Search internal documents
  - Find relevant information about VeraMoney, fintech, banking

  Always:
  - Cite document titles in your response
  - Indicate if information is not in the knowledge base
  - Be accurate and don't fabricate citations

  Current date: {{current_date}}
```

### Nested Langfuse Traces

```
Trace ID Convention:
  Supervisor: {session_id}
  Weather Worker: {session_id}-weather
  Stock Worker: {session_id}-stock
  Knowledge Worker: {session_id}-knowledge

Trace Hierarchy:
  supervisor_trace
    ├── metadata: {parent_trace: null}
    └── worker_trace (weather)
          ├── metadata: {parent_trace: {session_id}}
          └── spans: [model_call, tool_call, tool_result]

Implementation in Workers:
  def create_worker_trace(session_id: str, worker_name: str, langfuse_client):
      return langfuse_client.trace(
          id=f"{session_id}-{worker_name}",
          name=f"{worker_name}-worker",
          metadata={"parent_trace": session_id}
      )
```

## Dependencies

```
src/observability/prompts.py
├── imports → src/agent/core/prompts.py (worker prompt constants)
└── imports → langfuse (Langfuse client)

src/agent/workers/*.py
├── imports → src/observability/prompts.py (PromptManager)
└── imports → langfuse (for trace creation)
```

## Integration Notes

1. Worker prompts synced to Langfuse on startup (via lifespan)
2. Workers fetch prompts from Langfuse with fallback to local constants
3. Nested traces use session_id as parent for correlation
4. Trace hierarchy visible in Langfuse UI
