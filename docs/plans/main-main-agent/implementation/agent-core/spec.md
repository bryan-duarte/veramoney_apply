# Agent Core Implementation Spec

## Overview

This module implements the core conversational agent using LangChain v1's `create_agent()` function with a configured middleware stack.

## Files to Create

```
src/agent/
├── __init__.py                    # Re-exports
└── core/
    ├── __init__.py                # Re-exports
    ├── conversational_agent.py    # Agent factory
    └── prompts.py                 # System prompt definitions
```

---

## Implementation Guidelines

### src/agent/__init__.py

**Purpose:** Module-level exports

**Exports:**
- `create_conversational_agent` from `.core.conversational_agent`
- `AgentDep` type alias (or import from dependencies)

---

### src/agent/core/__init__.py

**Purpose:** Core submodule exports

**Exports:**
- `create_conversational_agent` from `.conversational_agent`
- `VERA_SYSTEM_PROMPT` from `.prompts`

---

### src/agent/core/prompts.py

**Purpose:** Define system prompts for the agent

**Guidelines:**

1. Define `VERA_SYSTEM_PROMPT` constant

2. Prompt should include:
   - Agent identity: "Vera AI, a financial assistant"
   - Capabilities: weather data, stock prices, general knowledge
   - Tone: professional, clear, efficient
   - Rules:
     - Only use information from tool results
     - Never invent or hallucinate data
     - Use tools when user asks about weather or stocks
     - Answer general questions using your knowledge
   - Citation style: Natural in-text references like "According to weather data..." or "Based on current stock information..."

3. Structure with clear sections:
   - Identity
   - Capabilities
   - Rules (numbered list)
   - Communication style

4. No comments in code - prompt content should be self-documenting

**Pseudocode:**
```
VERA_SYSTEM_PROMPT = """
You are Vera AI, a professional financial assistant.

CAPABILITIES:
- Retrieve current weather for any city
- Get real-time stock prices for any ticker symbol
- Answer general questions using your knowledge

RULES:
1. Only use information from tool results - never invent data
2. Use weather tool when asked about weather conditions
3. Use stock tool when asked about stock prices
4. For general questions, answer directly without tools
5. If a tool fails, explain the issue naturally

COMMUNICATION STYLE:
- Professional and concise
- Include natural references to data sources
- Example: "According to weather data, Montevideo is currently 22°C..."
"""
```

---

### src/agent/core/conversational_agent.py

**Purpose:** Factory function to create configured agent

**Guidelines:**

1. Define `create_conversational_agent()` async function

2. Function signature:
   - Parameters: `session_id: str`, `memory_store: PostgresMemoryStore`
   - Returns: Configured agent instance

3. Implementation steps:
   a. Initialize ChatOpenAI model:
      - model: from settings (default gpt-5-mini)
      - timeout: from settings (default 30s)
      - Do NOT set temperature (use default)

   b. Import tools:
      - `get_weather` from `src.tools.weather`
      - `get_stock_price` from `src.tools.stock`

   c. Import middleware:
      - `tool_error_handler` from `src.agent.middleware.tool_error_handler`
      - `output_guardrails` from `src.agent.middleware.output_guardrails`
      - `logging_middleware` from `src.agent.middleware.logging_middleware`

   d. Get conversation history from memory_store

   e. Create agent with `create_agent()`:
      - model: ChatOpenAI instance
      - tools: [get_weather, get_stock_price]
      - system_prompt: VERA_SYSTEM_PROMPT
      - middleware: [logging_middleware, tool_error_handler, output_guardrails]
      - checkpointer: memory_store checkpointer (for persistence)

4. All functions must be async

5. Use dependency injection for settings (SettingsDep)

6. No comments - code should be self-documenting

**Pseudocode:**
```
async def create_conversational_agent(
    session_id: str,
    memory_store: PostgresMemoryStore
) -> Agent:
    settings = get_settings()

    model = ChatOpenAI(
        model=settings.agent_model,
        timeout=settings.agent_timeout_seconds
    )

    tools = [get_weather, get_stock_price]

    middleware_stack = [
        logging_middleware,
        tool_error_handler,
        output_guardrails
    ]

    checkpointer = memory_store.get_checkpointer(session_id)

    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=VERA_SYSTEM_PROMPT,
        middleware=middleware_stack,
        checkpointer=checkpointer
    )

    return agent
```

---

## Dependencies

- `langchain.agents.create_agent`
- `langchain_openai.ChatOpenAI`
- `src.tools.weather.get_weather`
- `src.tools.stock.get_stock_price`
- `src.agent.middleware.*`
- `src.agent.memory.PostgresMemoryStore`
- `src.config.settings`

---

## Integration Notes

1. Agent is created per-request with session context
2. Middleware order matters: logging → error handling → guardrails
3. Checkpointer handles persistence automatically
4. Session_id is used as thread_id for conversation isolation
