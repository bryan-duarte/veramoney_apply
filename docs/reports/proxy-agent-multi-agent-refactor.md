# Proxy Agent Pattern Implementation Guide for LangChain v1 Multi-Agent Systems

> *"Three tools walk into a bar. The supervisor says: 'I'll decide who gets to talk.'"*
> — **El Barto**

---

## Executive Summary

Your VeraMoney Apply project currently uses a single LangChain v1 agent with three tools (weather, stock price, knowledge/RAG). To implement a proxy/router agent pattern, you have **four viable approaches** that align with LangChain v1's `create_agent` API:

1. **Supervisor Pattern (Tool-Wrapped Subagents)** - Recommended for your use case
2. **Router Pattern (StateGraph with Parallel Execution)** - Best for multi-source queries requiring low latency
3. **State Machine Pattern** - For sequential workflow progression
4. **Subagent Middleware (Deep Agents)** - For context isolation with minimal code changes

The **Supervisor Pattern** is recommended because it matches your domain structure (weather, stock, knowledge), requires minimal code changes, and maintains your existing async-first architecture.

---

## Current Architecture Analysis

### Existing Implementation

Your project at `/Users/bryanduarte/Documents/proyectos/personales/veramoney-apply` uses:

```
src/agent/core/factory.py
├── AgentFactory.create_agent()
│   ├── Model: ChatOpenAI (gpt-5-mini-2025-08-07)
│   ├── Tools: [get_weather, get_stock_price, search_knowledge]
│   ├── Middleware: [logging, tool_error_handler, output_guardrails, knowledge_guardrails]
│   └── Checkpointer: AsyncPostgresSaver
```

**Key characteristics:**
- Single agent handles all query types via function calling
- LLM decides tool selection based on user intent
- PostgreSQL checkpointer for conversation memory
- Langfuse integration for observability

**Refactoring goal:** Replace single agent with proxy/router that delegates to specialized agents.

---

## Approach 1: Supervisor Pattern (Recommended)

### Architecture

```
                    ┌─────────────────┐
                    │  Supervisor     │
                    │  (Proxy Agent)  │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
    ┌───────────┐     ┌───────────┐     ┌───────────┐
    │  Weather  │     │   Stock   │     │ Knowledge │
    │   Agent   │     │   Agent   │     │   Agent   │
    └───────────┘     └───────────┘     └───────────┘
          │                  │                  │
          ▼                  ▼                  ▼
    get_weather()    get_stock_price()  search_knowledge()
```

### Implementation

```python
# src/agent/workers/weather_worker.py
from langchain.agents import create_agent
from langchain.tools import tool

weather_agent = create_agent(
    model="openai:gpt-4.1",
    tools=[get_weather],
    system_prompt="""You are a weather specialist for VeraMoney.
Provide accurate weather information for requested locations.
Always include temperature in Celsius and conditions.""",
)

@tool
def ask_weather_agent(request: str) -> str:
    """Route weather-related questions to the weather specialist.

    Use this for questions about:
    - Current weather conditions
    - Temperature in specific cities
    - Weather forecasts
    """
    result = weather_agent.invoke({"messages": [{"role": "user", "content": request}]})
    return result["messages"][-1].content
```

```python
# src/agent/workers/stock_worker.py
stock_agent = create_agent(
    model="openai:gpt-4.1",
    tools=[get_stock_price],
    system_prompt="""You are a stock price specialist for VeraMoney.
Provide current stock prices and market data.
Include price, change percentage, and timestamp.""",
)

@tool
def ask_stock_agent(request: str) -> str:
    """Route stock price questions to the stock specialist.

    Use this for questions about:
    - Current stock prices
    - Market data for ticker symbols
    - Price changes and trends
    """
    result = stock_agent.invoke({"messages": [{"role": "user", "content": request}]})
    return result["messages"][-1].content
```

```python
# src/agent/workers/knowledge_worker.py
knowledge_agent = create_agent(
    model="openai:gpt-4.1",
    tools=[search_knowledge],
    system_prompt="""You are a knowledge base specialist for VeraMoney.
Search internal documents and provide cited answers.
Always include document references in your responses.""",
)

@tool
def ask_knowledge_agent(request: str) -> str:
    """Route knowledge base questions to the document specialist.

    Use this for questions about:
    - VeraMoney company history
    - Fintech regulations
    - Banking regulations
    - Internal policies
    """
    result = knowledge_agent.invoke({"messages": [{"role": "user", "content": request}]})
    return result["messages"][-1].content
```

```python
# src/agent/core/supervisor.py
from langchain.agents import create_agent
from langchain.checkpoint.postgres import AsyncPostgresSaver
from src.agent.workers.weather_worker import ask_weather_agent
from src.agent.workers.stock_worker import ask_stock_agent
from src.agent.workers.knowledge_worker import ask_knowledge_agent

SUPERVISOR_PROMPT = """You are VeraMoney's AI assistant supervisor.

You coordinate three specialists:
1. Weather Specialist - For weather conditions and forecasts
2. Stock Specialist - For stock prices and market data
3. Knowledge Specialist - For VeraMoney history, regulations, and policies

Rules:
- Route requests to the appropriate specialist
- You may call multiple specialists if needed
- Synthesize results into a coherent response
- Never fabricate data - only report what specialists provide
"""

class SupervisorFactory:
    def __init__(self, memory_store: MemoryStore):
        self.memory_store = memory_store

    async def create_supervisor(self, session_id: str):
        checkpointer = self.memory_store.get_checkpointer()

        supervisor = create_agent(
            model="openai:gpt-4.1",
            tools=[
                ask_weather_agent,
                ask_stock_agent,
                ask_knowledge_agent,
            ],
            system_prompt=SUPERVISOR_PROMPT,
            checkpointer=checkpointer,
        )

        return supervisor
```

### Pros and Cons

| Aspect | Assessment |
|--------|------------|
| **Code changes** | Minimal - wrap existing tools, add supervisor layer |
| **Debugging** | Easy - clear delegation chain |
| **Parallel execution** | Limited - sequential tool calls |
| **Context isolation** | High - each agent has focused tools |
| **Async compatibility** | Full - use `ainvoke()` on all agents |

---

## Approach 2: Router Pattern with StateGraph

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      StateGraph Workflow                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌──────────┐     ┌─────────────────────────────────┐      │
│   │  START   │────▶│         Classify Query          │      │
│   └──────────┘     └───────────────┬─────────────────┘      │
│                                     │                        │
│                    ┌────────────────┼────────────────┐      │
│                    │                │                │      │
│                    ▼                ▼                ▼      │
│              ┌──────────┐    ┌──────────┐    ┌──────────┐   │
│              │ Weather  │    │  Stock   │    │Knowledge │   │
│              │  Agent   │    │  Agent   │    │  Agent   │   │
│              └────┬─────┘    └────┬─────┘    └────┬─────┘   │
│                   │               │               │         │
│                   └───────────────┼───────────────┘         │
│                                   │                         │
│                                   ▼                         │
│                           ┌──────────────┐                  │
│                           │  Synthesize  │                  │
│                           │   Results    │                  │
│                           └──────┬───────┘                  │
│                                  │                          │
│                                  ▼                          │
│                           ┌──────────────┐                  │
│                           │     END      │                  │
│                           └──────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

### Implementation

```python
# src/agent/router/state.py
import operator
from typing import Annotated, Literal, TypedDict

class AgentInput(TypedDict):
    query: str

class AgentOutput(TypedDict):
    source: str
    result: str

class Classification(TypedDict):
    source: Literal["weather", "stock", "knowledge"]
    query: str

class RouterState(TypedDict):
    query: str
    classifications: list[Classification]
    results: Annotated[list[AgentOutput], operator.add]
    final_answer: str
```

```python
# src/agent/router/workflow.py
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from pydantic import BaseModel, Field

class ClassificationResult(BaseModel):
    classifications: list[Classification] = Field(
        description="List of agents to invoke with targeted sub-questions"
    )

def classify_query(state: RouterState) -> dict:
    structured_llm = router_llm.with_structured_output(ClassificationResult)

    result = structured_llm.invoke([
        {
            "role": "system",
            "content": """Analyze the query and determine which agents to invoke.

Available sources:
- weather: Current weather conditions
- stock: Stock prices and market data
- knowledge: VeraMoney docs, regulations, policies

Return ONLY relevant sources with targeted sub-questions."""
        },
        {"role": "user", "content": state["query"]}
    ])

    return {"classifications": result.classifications}

def route_to_agents(state: RouterState) -> list[Send]:
    return [
        Send(c["source"], {"query": c["query"]})
        for c in state["classifications"]
    ]

async def query_weather(state: AgentInput) -> dict:
    result = await weather_agent.ainvoke({
        "messages": [{"role": "user", "content": state["query"]}]
    })
    return {
        "results": [{
            "source": "weather",
            "result": result["messages"][-1].content
        }]
    }

async def query_stock(state: AgentInput) -> dict:
    result = await stock_agent.ainvoke({
        "messages": [{"role": "user", "content": state["query"]}]
    })
    return {
        "results": [{
            "source": "stock",
            "result": result["messages"][-1].content
        }]
    }

async def query_knowledge(state: AgentInput) -> dict:
    result = await knowledge_agent.ainvoke({
        "messages": [{"role": "user", "content": state["query"]}]
    })
    return {
        "results": [{
            "source": "knowledge",
            "result": result["messages"][-1].content
        }]
    }

def synthesize_results(state: RouterState) -> dict:
    if not state["results"]:
        return {"final_answer": "No results found."}

    formatted = [
        f"**From {r['source'].title()}:**\n{r['result']}"
        for r in state["results"]
    ]

    synthesis = router_llm.invoke([
        {
            "role": "system",
            "content": f"""Synthesize results to answer: "{state['query']}"
- Combine without redundancy
- Highlight most actionable information
- Keep response concise"""
        },
        {"role": "user", "content": "\n\n".join(formatted)}
    ])

    return {"final_answer": synthesis.content}

def build_router_workflow() -> StateGraph:
    workflow = (
        StateGraph(RouterState)
        .add_node("classify", classify_query)
        .add_node("weather", query_weather)
        .add_node("stock", query_stock)
        .add_node("knowledge", query_knowledge)
        .add_node("synthesize", synthesize_results)
        .add_edge(START, "classify")
        .add_conditional_edges(
            "classify",
            route_to_agents,
            ["weather", "stock", "knowledge"]
        )
        .add_edge("weather", "synthesize")
        .add_edge("stock", "synthesize")
        .add_edge("knowledge", "synthesize")
        .add_edge("synthesize", END)
    )
    return workflow.compile()
```

### Pros and Cons

| Aspect | Assessment |
|--------|------------|
| **Code changes** | Moderate - requires StateGraph setup |
| **Parallel execution** | Yes - multiple agents execute simultaneously |
| **Latency** | Low for multi-source queries |
| **Complexity** | Higher - explicit state management |
| **Flexibility** | High - fine-grained control over flow |

---

## Approach 3: State Machine Pattern

### Architecture

This pattern uses a single agent whose configuration changes based on workflow progress. Useful for sequential information collection.

```python
# src/agent/middleware/step_config.py
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Literal
from typing_extensions import NotRequired

SupportStep = Literal["initial", "weather_collected", "stock_collected", "complete"]

class CustomState(AgentState):
    current_step: NotRequired[SupportStep]
    weather_data: NotRequired[dict]
    stock_data: NotRequired[dict]

STEP_CONFIG = {
    "initial": {
        "prompt": "Greet the user. Ask what information they need.",
        "tools": [],
    },
    "weather_collected": {
        "prompt": "Weather data collected. Ask if they need stock prices.",
        "tools": [get_stock_price],
    },
    "stock_collected": {
        "prompt": "Stock data collected. Provide summary.",
        "tools": [],
    },
    "complete": {
        "prompt": "All data collected. Provide final summary.",
        "tools": [],
    },
}

@wrap_model_call
async def apply_step_config(request: ModelRequest, handler) -> ModelResponse:
    current_step = request.state.get("current_step", "initial")
    stage_config = STEP_CONFIG[current_step]

    request = request.override(
        system_prompt=stage_config["prompt"],
        tools=stage_config["tools"],
    )

    return await handler(request)
```

### When to Use

- Sequential information collection (form-like flows)
- Multi-turn conversations with clear progression
- When agent behavior must change based on collected state

---

## Approach 4: Subagent Middleware (Deep Agents)

### Implementation

```python
# src/agent/middleware/subagents.py
from deepagents.middleware.subagents import SubAgentMiddleware

agent = create_agent(
    model="openai:gpt-4.1",
    tools=[],
    middleware=[
        SubAgentMiddleware(
            default_model="openai:gpt-4.1",
            subagents=[
                {
                    "name": "weather",
                    "description": "Get weather information for cities",
                    "system_prompt": "Use get_weather tool to provide weather data.",
                    "tools": [get_weather],
                },
                {
                    "name": "stock",
                    "description": "Get stock prices for ticker symbols",
                    "system_prompt": "Use get_stock_price tool to provide market data.",
                    "tools": [get_stock_price],
                },
                {
                    "name": "knowledge",
                    "description": "Search VeraMoney knowledge base",
                    "system_prompt": "Use search_knowledge to find relevant documents.",
                    "tools": [search_knowledge],
                },
            ],
        )
    ],
)
```

### Pros and Cons

| Aspect | Assessment |
|--------|------------|
| **Code changes** | Minimal - single middleware addition |
| **Context isolation** | Highest - subagents don't pollute main context |
| **Dependency** | Requires `deepagents` package |
| **Flexibility** | Lower - pre-built patterns only |

---

## Comparison Matrix

| Criterion | Supervisor | Router | State Machine | Subagent MW |
|-----------|-----------|--------|---------------|-------------|
| **Implementation complexity** | Low | Medium | High | Very Low |
| **Parallel execution** | No | Yes | No | No |
| **Context isolation** | High | High | Low | Highest |
| **Debugging ease** | High | Medium | Low | Medium |
| **Async support** | Full | Full | Full | Full |
| **State persistence** | Easy | Manual | Easy | Easy |
| **Best for** | Domain routing | Multi-source queries | Sequential flows | Quick setup |

---

## Recommendation for VeraMoney Apply

### Primary Recommendation: Supervisor Pattern

**Rationale:**
1. **Aligns with your domain structure** - Three distinct verticals (weather, stock, knowledge)
2. **Minimal code changes** - Wrap existing tools, add supervisor layer
3. **Maintains existing architecture** - Keep PostgreSQL checkpointer, Langfuse observability
4. **Async-first** - All agents support `ainvoke()` and `astream()`
5. **Testable** - Each worker agent can be tested independently

### Implementation Roadmap

```
Phase 1: Create Worker Agents
├── src/agent/workers/weather_worker.py
├── src/agent/workers/stock_worker.py
└── src/agent/workers/knowledge_worker.py

Phase 2: Create Supervisor
├── src/agent/core/supervisor.py
└── src/agent/core/supervisor_prompts.py

Phase 3: Update Factory
├── src/agent/core/factory.py (modify)
└── Return supervisor instead of single agent

Phase 4: Update Middleware
├── Apply existing middleware to supervisor
└── Worker agents get minimal middleware (logging only)
```

### Required Dependencies

```toml
# pyproject.toml - Already have these
"langchain>=1.2.10",
"langchain-openai>=1.1.10",
"langgraph>=0.3.0",
"langgraph-checkpoint-postgres>=3.0.4",
```

---

## Key Findings

1. **`create_agent` is the unified API** - LangChain v1.0+ (Oct 2025) consolidated agent creation into this single function, which internally compiles to a LangGraph ReAct graph.

2. **Tool-wrapping is idiomatic** - Wrapping subagents as `@tool` decorated functions is the recommended pattern for supervisor architectures.

3. **Checkpointer on top-level only** - Apply PostgreSQL checkpointer to the supervisor only, not worker agents.

4. **Middleware stacks differ** - Supervisor gets full middleware stack; workers get minimal (logging + error handling).

5. **Parallel vs sequential trade-off** - Router pattern enables parallel execution but adds StateGraph complexity.

6. **Your existing code is well-structured** - The factory pattern, middleware architecture, and async-first design make refactoring straightforward.

---

## References

### Official Documentation
- [LangGraph Multi-Agent Concepts](https://langchain-ai.github.io/langgraph/concepts/multi_agent/)
- [LangGraph Agent Supervisor Tutorial](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/agent_supervisor)
- [LangChain Official Documentation](https://docs.langchain.com/oss/python/langchain/overview)

### Project Local References
- `.claude/skills/langchain/reference/advanced/subagents.md` - Supervisor pattern
- `.claude/skills/langchain/reference/advanced_examples/router_knowleadge_agent.md` - Router pattern
- `.claude/skills/langchain/reference/advanced_examples/customer_support.md` - State machine pattern
- `.claude/skills/langchain/reference/middleware/prebuilt_middleware.md` - Subagent middleware

---

*Report generated by: El Barto*
*Date: 2026-02-20*
