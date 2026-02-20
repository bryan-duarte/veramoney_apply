# Multi-Agent System Implementation Guide for VeraMoney

> *"Choosing the right architecture is like choosing the right tool for the job—use a hammer for nails, not for screws."*
> — **El Barto**

## Executive Summary

This report provides a comprehensive guide for implementing a multi-agent system in the VeraMoney Apply project. Based on analysis of the project requirements, existing codebase, and LangChain v1 documentation, the **Supervisor Pattern** is recommended as the optimal approach. This pattern provides clean separation of concerns, LLM-driven dynamic routing, and seamless integration with the existing `create_agent` implementation.

---

## 1. Task Requirements Analysis

### 1.1 Bonus Task 2: Multi-Agent Pattern (from TASKS_BREAKDOWN.md)

| ID   | Task                              | Description                                          |
|------|-----------------------------------|------------------------------------------------------|
| B2.1 | Create Router Agent               | Decides which specialized agent to use               |
| B2.2 | Create Weather Agent              | Specialized for weather queries                      |
| B2.3 | Create Stock Agent                | Specialized for stock queries                        |
| B2.4 | Create Knowledge Agent            | Specialized for RAG queries                          |
| B2.5 | Implement orchestration           | Router calls appropriate agent                       |

### 1.2 Required Multi-Agent Flow

```
User Message
    |
    v
+-----------------+
|  Router Agent   |
+--------+--------+
         |
    +----+----+------------+------------+
    |         |            |            |
    v         v            v            v
Weather   Stock      Knowledge      General
Agent     Agent      Agent          Response
    |         |            |            |
    +----+----+------------+------------+
         |
         v
+-----------------+
| Final Response  |
+-----------------+
```

---

## 2. Current Project Analysis

### 2.1 Existing Agent Implementation

The project already has a conversational agent in `src/agent/core/conversational_agent.py`:

```python
async def create_conversational_agent(
    settings: Settings,
    memory_store: MemoryStore,
    session_id: str,
) -> Any:
    model = ChatOpenAI(
        model=settings.agent_model,
        timeout=settings.agent_timeout_seconds,
        api_key=settings.openai_api_key,
    )

    tools = [get_weather, get_stock_price, search_knowledge]

    middleware_stack = [
        logging_middleware,
        tool_error_handler,
        output_guardrails,
        knowledge_guardrails,
    ]

    checkpointer = memory_store.get_checkpointer()

    config = {
        "configurable": {
            "thread_id": session_id,
        },
    }

    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=_build_system_prompt(),
        middleware=middleware_stack,
        checkpointer=checkpointer,
    )

    return agent, config
```

**Key Observations:**
- Already uses `create_agent` (LangChain v1 compliant)
- Has three tools: weather, stock, knowledge
- Middleware stack is well-structured
- Memory/checkpointer support is implemented
- Async-first architecture is in place

### 2.2 Current Project Structure

```
src/agent/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── conversational_agent.py    # Current single-agent implementation
│   └── prompts.py
├── memory/
│   ├── __init__.py
│   └── store.py
├── middleware/
│   ├── __init__.py
│   ├── knowledge_guardrails.py
│   ├── logging_middleware.py
│   ├── output_guardrails.py
│   └── tool_error_handler.py
└── multi_agent/
    └── __init__.py                # Placeholder for multi-agent
```

---

## 3. Available Documentation in Project

### 3.1 LangChain Reference Files

| File | Pattern | Relevance |
|------|---------|-----------|
| `advanced/subagents.md` | Supervisor Pattern with tool wrapping | HIGH |
| `advanced_examples/router_knowledge_agent.md` | Router Pattern with StateGraph | HIGH |
| `advanced_examples/customer_support.md` | State Machine Pattern | MEDIUM |
| `middleware/overview.md` | Middleware architecture | HIGH |
| `middleware/custom_middleware.md` | Custom middleware patterns | HIGH |
| `middleware/prebuilt_middleware.md` | Built-in middleware options | MEDIUM |
| `basics/agents.md` | Agent creation basics | REFERENCE |
| `basics/tools.md` | Tool definition patterns | REFERENCE |

### 3.2 Key Documentation Insights

#### From subagents.md (Supervisor Pattern):
- Sub-agents are wrapped as tools using `@tool` decorator
- Supervisor only sees high-level tools (not individual API tools)
- Clear separation: supervisor routes, specialists execute
- Supports parallel tool calls for multi-part queries

#### From router_knowledge_agent.md (Router Pattern):
- Uses LangGraph StateGraph for explicit workflow control
- `Send` API enables parallel agent execution
- Structured output for classification (Pydantic models)
- Reducer pattern (`Annotated[list, operator.add]`) collects parallel results

#### From customer_support.md (State Machine Pattern):
- Single agent with dynamic configuration changes
- Tools update `current_step` via `Command` objects
- Middleware reads state and applies appropriate config
- Good for sequential workflows with clear transitions

---

## 4. Multi-Agent Pattern Options

### 4.1 Pattern Comparison Matrix

| Pattern | Complexity | Flexibility | Parallel Execution | Best For |
|---------|------------|-------------|-------------------|----------|
| **Supervisor** | LOW | HIGH | YES (LLM-driven) | Domain-separated specialists |
| **Router (StateGraph)** | MEDIUM | MEDIUM | YES (explicit) | Multi-source parallel queries |
| **State Machine** | HIGH | LOW | NO | Sequential workflow steps |

### 4.2 Detailed Pattern Analysis

#### Option A: Supervisor Pattern (RECOMMENDED)

**Architecture:**
```
+------------------+
| Supervisor Agent |
+--------+---------+
         |
    +----+----+------------+
    |         |            |
    v         v            v
+-------+ +-------+ +------------+
|Weather| | Stock | | Knowledge  |
| Agent | | Agent | |   Agent    |
+-------+ +-------+ +------------+
```

**Pros:**
- Simpler implementation
- LLM-driven dynamic routing
- Natural language tool descriptions guide routing
- Integrates seamlessly with existing `create_agent` pattern
- Supports parallel tool calls for multi-part queries

**Cons:**
- Routing is non-deterministic (LLM-based)
- Slightly higher latency for routing decisions

**Code Structure:**
```python
# 1. Create specialized agents
weather_agent = create_agent(model, tools=[get_weather], system_prompt=...)
stock_agent = create_agent(model, tools=[get_stock_price], system_prompt=...)
knowledge_agent = create_agent(model, tools=[search_knowledge], system_prompt=...)

# 2. Wrap as tools
@tool
def query_weather(request: str) -> str:
    """Query weather information. Use for weather-related questions."""
    result = weather_agent.invoke({"messages": [{"role": "user", "content": request}]})
    return result["messages"][-1].content

# 3. Create supervisor
supervisor = create_agent(
    model,
    tools=[query_weather, query_stock, query_knowledge],
    system_prompt="Route to appropriate specialist..."
)
```

#### Option B: Router Pattern (StateGraph)

**Architecture:**
```
+--------+     +----------+     +-----------+
| START  |---->| Classify |--->| Route     |
+--------+     +----------+     +-----------+
                                    |
                    +---------------+---------------+
                    |               |               |
                    v               v               v
               +--------+     +--------+     +------------+
               | Weather|     | Stock  |     | Knowledge  |
               +--------+     +--------+     +------------+
                    |               |               |
                    +---------------+---------------+
                                    |
                                    v
                            +-------------+
                            |  Synthesize |
                            +-------------+
```

**Pros:**
- Explicit workflow control
- Structured classification output
- True parallel execution with `Send` API
- Deterministic routing logic

**Cons:**
- More boilerplate code
- Static routing (changes require code updates)
- Requires LangGraph StateGraph setup

**Code Structure:**
```python
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

class RouterState(TypedDict):
    query: str
    classifications: list[Classification]
    results: Annotated[list[AgentOutput], operator.add]
    final_answer: str

workflow = (
    StateGraph(RouterState)
    .add_node("classify", classify_query)
    .add_node("weather", query_weather)
    .add_node("stock", query_stock)
    .add_node("knowledge", query_knowledge)
    .add_node("synthesize", synthesize_results)
    .add_edge(START, "classify")
    .add_conditional_edges("classify", route_to_agents, ["weather", "stock", "knowledge"])
    .add_edge("weather", "synthesize")
    .add_edge("stock", "synthesize")
    .add_edge("knowledge", "synthesize")
    .add_edge("synthesize", END)
    .compile()
)
```

#### Option C: State Machine Pattern

**Architecture:**
```
+------------------+
|   Single Agent   |
+--------+---------+
         |
    +----+----+
    | Middleware|
    +----+----+
         |
    +----+----+------------+
    |         |            |
    v         v            v
intent_   specialist   response
collector  router      generator
```

**Pros:**
- Single agent instance
- Clear sequential transitions
- Good for workflow with dependencies

**Cons:**
- Complex middleware setup
- Not ideal for parallel execution
- State management overhead

---

## 5. Recommended Approach

### 5.1 Primary Recommendation: Supervisor Pattern

**Rationale:**

1. **Alignment with Current Implementation**: The project already uses `create_agent` with tools and middleware. The Supervisor Pattern extends this naturally.

2. **Simplicity**: Least complex to implement while meeting all requirements.

3. **Flexibility**: LLM-driven routing adapts to query variations without code changes.

4. **Parallel Support**: Multi-part queries (e.g., "weather in Montevideo and AAPL price") can invoke multiple specialists simultaneously.

5. **Maintainability**: Each specialist is isolated and can be modified independently.

### 5.2 Implementation Strategy

#### Phase 1: Create Specialized Agents

Location: `src/agent/multi_agent/workers/`

```
src/agent/multi_agent/
├── __init__.py
├── workers/
│   ├── __init__.py
│   ├── weather_agent.py
│   ├── stock_agent.py
│   └── knowledge_agent.py
├── supervisor/
│   ├── __init__.py
│   └── supervisor_agent.py
└── tools/
    ├── __init__.py
    └── agent_tools.py      # Wrapped agent tools
```

#### Phase 2: Implementation Details

**weather_agent.py:**
```python
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from src.tools.weather import get_weather

WEATHER_AGENT_PROMPT = """You are a weather information specialist.

Your only responsibility is to provide accurate weather information.

Guidelines:
- Always confirm the location in your response
- Provide temperature, conditions, and humidity when available
- If the location is ambiguous, ask for clarification
- Be concise and factual

Use the get_weather tool to fetch current weather data."""

def create_weather_agent(model: ChatOpenAI):
    return create_agent(
        model,
        tools=[get_weather],
        system_prompt=WEATHER_AGENT_PROMPT,
        name="weather_specialist",
    )
```

**agent_tools.py (Supervisor Tools):**
```python
from langchain.tools import tool

@tool
def query_weather(request: str) -> str:
    """Query weather information for a specific location.

    Use this tool when the user asks about:
    - Current weather conditions
    - Temperature in a city
    - Weather forecasts

    Input: Natural language weather request (e.g., 'weather in Montevideo')
    """
    result = weather_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].content

@tool
def query_stock(request: str) -> str:
    """Query stock price information for a specific ticker.

    Use this tool when the user asks about:
    - Stock prices
    - Market data
    - Ticker symbol lookups

    Input: Natural language stock request (e.g., 'price of AAPL')
    """
    result = stock_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].content

@tool
def query_knowledge(request: str) -> str:
    """Search the knowledge base for company information.

    Use this tool when the user asks about:
    - Company policies
    - Product information
    - General knowledge questions

    Input: Natural language knowledge request
    """
    result = knowledge_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].content
```

**supervisor_agent.py:**
```python
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.agents.middleware import SummarizationMiddleware

from src.agent.multi_agent.tools.agent_tools import (
    query_weather,
    query_stock,
    query_knowledge,
)

SUPERVISOR_PROMPT = """You are Vera, a helpful financial assistant.

You coordinate specialized agents to answer user questions:

1. **Weather Queries** -> Use query_weather
   - Questions about weather, temperature, forecasts
   - Example: "What's the weather in Montevideo?"

2. **Stock Queries** -> Use query_stock
   - Questions about stock prices, market data
   - Example: "What's the price of AAPL?"

3. **Knowledge Queries** -> Use query_knowledge
   - Questions about company policies, products, general info
   - Example: "What are Vera's services?"

For multi-part queries, use multiple tools in the same response.
Always synthesize the results into a coherent, helpful answer.

Current date: {current_date}"""

async def create_supervisor_agent(
    model: ChatOpenAI,
    memory_store: MemoryStore,
    session_id: str,
    current_date: str,
):
    tools = [query_weather, query_stock, query_knowledge]

    middleware_stack = [
        logging_middleware,
        tool_error_handler,
        SummarizationMiddleware(
            model="gpt-4.1-mini",
            trigger=("tokens", 4000),
            keep=("messages", 10),
        ),
    ]

    checkpointer = memory_store.get_checkpointer()

    config = {
        "configurable": {
            "thread_id": session_id,
        },
    }

    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=SUPERVISOR_PROMPT.format(current_date=current_date),
        middleware=middleware_stack,
        checkpointer=checkpointer,
    )

    return agent, config
```

### 5.3 Integration with Existing Code

The multi-agent system can be integrated by modifying `src/agent/core/conversational_agent.py` to optionally use the supervisor pattern:

```python
async def create_conversational_agent(
    settings: Settings,
    memory_store: MemoryStore,
    session_id: str,
    use_multi_agent: bool = False,
) -> Any:
    if use_multi_agent:
        from src.agent.multi_agent.supervisor.supervisor_agent import create_supervisor_agent
        return await create_supervisor_agent(
            model=model,
            memory_store=memory_store,
            session_id=session_id,
            current_date=datetime.now().strftime("%Y-%m-%d"),
        )

    # Existing single-agent implementation...
```

---

## 6. Middleware Recommendations

### 6.1 Prebuilt Middleware to Add

| Middleware | Purpose | Priority |
|------------|---------|----------|
| `SummarizationMiddleware` | Compress long conversations | HIGH |
| `ToolRetryMiddleware` | Retry failed API calls | HIGH |
| `ToolCallLimitMiddleware` | Prevent excessive API usage | MEDIUM |
| `HumanInTheLoopMiddleware` | Approve sensitive actions | OPTIONAL |

### 6.2 Custom Middleware to Implement

The project already has good custom middleware. For multi-agent:

1. **AgentRoutingMiddleware**: Log which specialist was selected
2. **AgentPerformanceMiddleware**: Track latency per specialist

---

## 7. Testing Strategy

### 7.1 Unit Tests for Specialists

```python
import pytest
from src.agent.multi_agent.workers.weather_agent import create_weather_agent

@pytest.mark.asyncio
async def test_weather_agent_responds_to_query():
    agent = create_weather_agent(model)
    result = await agent.ainvoke({
        "messages": [{"role": "user", "content": "weather in Montevideo"}]
    })
    assert "Montevideo" in result["messages"][-1].content
```

### 7.2 Integration Tests for Supervisor

```python
@pytest.mark.asyncio
async def test_supervisor_routes_weather_query():
    supervisor = await create_supervisor_agent(...)
    result = await supervisor.ainvoke({
        "messages": [{"role": "user", "content": "What's the weather in San Francisco?"}]
    })
    assert "weather" in result["messages"][-1].content.lower()
    assert "san francisco" in result["messages"][-1].content.lower()
```

### 7.3 Multi-Part Query Tests

```python
@pytest.mark.asyncio
async def test_supervisor_handles_multi_part_query():
    supervisor = await create_supervisor_agent(...)
    result = await supervisor.ainvoke({
        "messages": [{
            "role": "user",
            "content": "What's the weather in Montevideo and the price of AAPL?"
        }]
    })
    response = result["messages"][-1].content.lower()
    assert "montevideo" in response
    assert "aapl" in response
```

---

## 8. Migration Path

### 8.1 Phase 1: Preparation (No Breaking Changes)

1. Create `src/agent/multi_agent/` directory structure
2. Implement specialized agents as separate modules
3. Create tool wrappers for specialists
4. Add configuration flag `use_multi_agent` in Settings

### 8.2 Phase 2: Integration

1. Implement supervisor agent
2. Update `create_conversational_agent` to support multi-agent mode
3. Add feature flag to API endpoints
4. Deploy with flag disabled

### 8.3 Phase 3: Validation

1. Enable multi-agent for test users
2. Compare latency and accuracy vs single-agent
3. Gather feedback and iterate
4. Roll out to production

---

## Key Findings

1. **Supervisor Pattern is optimal** for VeraMoney's 4-agent architecture (Router + 3 Specialists)
2. **Current codebase is well-prepared** - already uses `create_agent`, has middleware stack, and async architecture
3. **Minimal code changes required** - primarily additive, no major refactoring
4. **Existing tools can be reused** - weather, stock, and knowledge tools are already implemented
5. **Middleware integration is straightforward** - add `SummarizationMiddleware` for long conversations

---

## Recommendations

| Priority | Action |
|----------|--------|
| P0 | Implement Supervisor Pattern with 3 specialized agents |
| P1 | Add `SummarizationMiddleware` to handle long conversations |
| P1 | Create feature flag for gradual rollout |
| P2 | Add `ToolRetryMiddleware` for API resilience |
| P2 | Implement agent routing metrics for observability |
| P3 | Consider StateGraph Router Pattern for explicit parallel execution if needed |

---

*Report generated by: El Barto*
*Date: 2026-02-19*
*Version: 1.0*
