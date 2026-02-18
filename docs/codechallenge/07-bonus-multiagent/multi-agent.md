# Bonus 2: Multi-Agent Pattern

> Status: TODO
> Priority: BONUS (Strongly Valued)

## Overview

Implement a multi-agent architecture with specialized agents and a router.

## Requirements

- Router Agent that decides which specialized agent to call
- Weather Agent - specialized for weather queries
- Stock Agent - specialized for stock queries
- Knowledge Agent - specialized for RAG queries
- Supervisor or router pattern

## Tasks

| ID | Task | Status | Notes |
|----|------|--------|-------|
| B2.1 | Create Router Agent | TODO | Decides which agent to use |
| B2.2 | Create Weather Agent | TODO | Specialized for weather |
| B2.3 | Create Stock Agent | TODO | Specialized for stocks |
| B2.4 | Create Knowledge Agent | TODO | Specialized for RAG |
| B2.5 | Implement orchestration | TODO | Router calls appropriate agent |

## Multi-Agent Flow

```
User Message
    │
    ▼
┌─────────────────┐
│  Router Agent   │
└────────┬────────┘
         │
    ┌────┼────┬────────────┐
    ▼    ▼    ▼            ▼
Weather Stock Knowledge General
Agent  Agent Agent       Agent
    │    │    │            │
    └────┼────┴────────────┘
         ▼
┌─────────────────┐
│ Final Response  │
└─────────────────┘
```

## Implementation Location

```
src/agent/
├── __init__.py
├── router.py                # Router agent
├── workers/
│   ├── __init__.py
│   ├── weather_agent.py     # Weather specialist
│   ├── stock_agent.py       # Stock specialist
│   ├── knowledge_agent.py   # RAG specialist
│   └── general_agent.py     # General responses
└── supervisor.py            # Orchestration logic
```

## LangChain Approach

**Reference:** `.claude/skills/langchain/reference/advanced/subagents.md`

### Router Pattern

```python
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

ROUTER_PROMPT = """You are a router. Classify the user's message into one of:
- WEATHER: Questions about weather
- STOCK: Questions about stock prices
- KNOWLEDGE: Questions about Vera, policies, regulations
- GENERAL: Everything else

Return ONLY the category name."""

router_agent = create_agent(
    model,
    tools=[],
    system_prompt=ROUTER_PROMPT
)
```

### Specialized Agents

```python
WEATHER_PROMPT = """You are a weather specialist.
Use the get_weather tool to answer weather questions.
Be concise and accurate."""

weather_agent = create_agent(
    model,
    tools=[get_weather],
    system_prompt=WEATHER_PROMPT
)
```

### Orchestration

```python
async def route_message(message: str) -> str:
    # Step 1: Classify intent
    category = await router_agent.ainvoke({
        "messages": [HumanMessage(content=message)]
    })

    # Step 2: Route to specialist
    agents = {
        "WEATHER": weather_agent,
        "STOCK": stock_agent,
        "KNOWLEDGE": knowledge_agent,
        "GENERAL": general_agent
    }

    specialist = agents.get(category, general_agent)

    # Step 3: Get response
    response = await specialist.ainvoke({
        "messages": [HumanMessage(content=message)]
    })

    return response
```

## Alternative: Supervisor Pattern

**Reference:** `.claude/skills/langchain/reference/advanced_examples/customer_support.md`

```python
from langchain.agents import create_agent

SUPERVISOR_PROMPT = """You are a supervisor managing a team of specialists:
- weather_agent: Handles weather queries
- stock_agent: Handles stock price queries
- knowledge_agent: Handles questions about Vera/policies

Decide which agent(s) to call and synthesize their responses."""

supervisor = create_agent(
    model,
    tools=[
        weather_agent.as_tool(),
        stock_agent.as_tool(),
        knowledge_agent.as_tool()
    ],
    system_prompt=SUPERVISOR_PROMPT
)
```

## Testing

```python
# Test routing
assert await route_message("Weather in NYC?") == "WEATHER"
assert await route_message("AAPL price?") == "STOCK"
assert await route_message("Tell me about Vera") == "KNOWLEDGE"
assert await route_message("Hello!") == "GENERAL"

# Test multi-tool query
response = await route_message("Weather in NYC and AAPL price?")
# Should call both weather and stock agents
```

## Dependencies

```toml
langchain>=1.2.10
langchain-openai>=1.1.10
```
