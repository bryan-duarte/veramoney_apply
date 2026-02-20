# Supervisor Implementation

## Overview

Create the supervisor agent that coordinates worker specialists. The supervisor receives user queries and delegates to the appropriate worker(s) based on intent.

## Files to Create/Modify

| File | Change Type | Purpose |
|------|-------------|---------|
| `src/agent/core/supervisor.py` | New | SupervisorFactory class |
| `src/agent/core/prompts.py` | Modify | Add SUPERVISOR_SYSTEM_PROMPT |
| `src/agent/core/factory.py` | Modify | Remove/refactor (supervisor replaces it) |

## Implementation Guidelines

### supervisor.py - SupervisorFactory

```
Purpose: Create and configure the supervisor agent

SupervisorFactory Class:
  AGENT_VERSION: str = "2.0"  # Major version bump

  __init__:
    - settings: Settings
    - memory_store: MemoryStore
    - langfuse_manager: LangfuseManager | None
    - prompt_manager: PromptManager | None
    - knowledge_retriever: KnowledgeRetriever | None

  async create_supervisor(session_id: str) -> tuple[Agent, dict, CallbackHandler | None]:
    1. Get compiled prompt from PromptManager
    2. Create ChatOpenAI model (gpt-5-mini)
    3. Build worker tools list (from workers module)
    4. Build middleware stack (full stack)
    5. Get checkpointer from MemoryStore
    6. Create agent via create_agent()
    7. Build config with session_id and callbacks
    8. Return (agent, config, langfuse_handler)

  _build_worker_tools() -> list[Tool]:
    - Import ask_weather_agent, ask_stock_agent, ask_knowledge_agent
    - Create knowledge tool with retriever injection
    - Return [ask_weather_agent, ask_stock_agent, ask_knowledge_agent]

  _build_middleware_stack() -> list:
    - Return [logging_middleware, tool_error_handler, output_guardrails, knowledge_guardrails]
    - Same middleware as current AgentFactory
```

### prompts.py - Supervisor Prompt

```
SUPERVISOR_SYSTEM_PROMPT:

You are VeraMoney's AI assistant supervisor.
You coordinate three specialists:

1. Weather Specialist - Current weather conditions, forecasts, temperature
2. Stock Specialist - Stock prices, market data, ticker quotes
3. Knowledge Specialist - VeraMoney history, fintech regulations, banking policies

Rules:
- Route requests to the appropriate specialist
- You may call multiple specialists if a query spans domains
- Synthesize results into a coherent, helpful response
- Never fabricate data - only report what specialists provide
- If unsure which specialist to use, explain the available options

Current date: {{current_date}}
```

### factory.py - Deprecation

```
Purpose: This file will be largely replaced by supervisor.py

Options:
1. Rename to factory.py.bak and create new supervisor.py
2. Refactor in place: AgentFactory -> SupervisorFactory
3. Keep minimal factory.py for any shared utilities

Recommendation: Refactor in place, rename class to SupervisorFactory
```

## Dependencies

```
src/agent/core/supervisor.py
├── imports → src/agent/workers/weather_worker (ask_weather_agent)
├── imports → src/agent/workers/stock_worker (ask_stock_agent)
├── imports → src/agent/workers/knowledge_worker (ask_knowledge_agent)
├── imports → src/agent/memory/store.py (MemoryStore)
├── imports → src/agent/middleware/* (all middleware)
├── imports → src/observability/manager.py (LangfuseManager)
├── imports → src/observability/prompts.py (PromptManager)
└── imports → langchain.agents.create_agent
```

## Integration Notes

1. SupervisorFactory replaces AgentFactory in API handlers
2. Supervisor has full middleware stack (logging, error handling, guardrails)
3. Supervisor has checkpointer (AsyncPostgresSaver)
4. Supervisor model is gpt-5-mini (same as current)
5. Worker tools are imported from workers module
6. Knowledge worker tool requires retriever injection at creation time
