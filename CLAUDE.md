# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**VeraMoney Apply** is a technical assessment project for an AI Platform Engineer position. It implements a minimal AI-powered service with LLM-based agents, tool integration, and retrieval-augmented generation (RAG) capabilities in a regulated fintech environment.

---

## Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| **Language** | Python | 3.11+ |
| **API Framework** | FastAPI | >=0.129.0 |
| **ASGI Server** | Uvicorn | >=0.41.0 |
| **Agent Framework** | LangChain | >=1.2.10 |
| **LLM Integration** | langchain-openai | >=1.1.10 |
| **Community Tools** | langchain-community | >=0.4.1 |
| **Vector Database** | ChromaDB | >=1.5.0 |
| **Chroma Integration** | langchain-chroma | >=1.1.0 |
| **Data Validation** | Pydantic | >=2.12.5 |
| **Configuration** | pydantic-settings | >=2.13.0 |
| **Environment** | python-dotenv | >=1.2.1 |
| **Observability** | Langfuse | >=3.14.3 |
| **Containerization** | Docker | Multi-stage build |
| **Package Manager** | uv | Fast Python package installer |

---

## Project Structure

```
veramoney-apply/
├── main.py                    # Entry point for the application
├── pyproject.toml             # Project configuration and dependencies
├── Dockerfile                 # Multi-stage Docker build
├── docker-compose.yml         # Full observability stack (Langfuse, ChromaDB)
├── .env.example               # Environment variables template
│
├── src/
│   ├── api/                   # API layer (implemented)
│   │   ├── main.py            # FastAPI app factory with lifespan management
│   │   ├── dependencies.py    # Dependency injection (placeholder Settings)
│   │   └── endpoints/
│   │       └── chat.py        # /chat endpoint (placeholder response)
│   │
│   ├── agent/                 # Agent layer (to be implemented)
│   │   └── multi_agent/       # Multi-agent structure
│   │       └── workers/       # Specialized agent workers
│   │
│   ├── tools/                 # Tools layer (to be implemented)
│   │   ├── weather/           # Weather tool
│   │   └── stock/             # Stock price tool
│   │
│   ├── rag/                   # RAG pipeline (bonus, to be implemented)
│   │
│   ├── observability/         # Observability layer (bonus)
│   │
│   └── config/                # Configuration layer (to be implemented)
│
├── docs/
│   ├── challenge_tasks/       # Challenge requirements
│   │   ├── code_challenge.md  # Original assessment requirements
│   │   └── TASKS_BREAKDOWN.md # Task breakdown
│   │
│   ├── reports/               # Analysis reports
│   │   └── task-implementation-analysis.md
│   │
│   ├── plans/                 # Implementation plans
│   └── knowledge_base/        # RAG documents (to be populated)
│
└── .claude/
    └── skills/
        └── langchain/         # LangChain documentation and patterns
```

---

## Project Objectives

### Core Tasks (Mandatory)

1. **Weather Tool** - Create a tool that retrieves current weather information
   - Accept city name as input
   - Return structured JSON output
   - Integrate with agent via function calling

2. **Stock Price Tool** - Create a tool that retrieves current stock prices
   - Accept ticker symbol (e.g., `AAPL`) as input
   - Return structured JSON with price and timestamp
   - Handle argument validation

3. **Conversational Agent** - Build an agent capable of:
   - Understanding user intent
   - Deciding whether to respond directly or call tools
   - Multi-turn conversation with context management
   - Avoiding hallucination of tool results

### Bonus Tasks (Strongly Valued)

1. **RAG Pipeline** - Retrieval-Augmented Generation
   - Knowledge base with 3-10 documents
   - Embedding generation and vector storage
   - Context injection with citations

2. **Multi-Agent Pattern** - Specialized agents with routing
   - Router Agent for intent classification
   - Weather Agent, Stock Agent, Knowledge Agent
   - Supervisor/orchestration pattern

3. **Observability** - Production monitoring
   - Tool call logging
   - Latency and token usage metrics
   - Langfuse integration

---

## Critical Rules

### Async-First Architecture - MANDATORY

**This application is I/O bound. ALL code MUST be asynchronous. No synchronous code allowed.**

**Rules:**
- All functions must be `async def`
- All I/O operations must use `await`
- Use `asyncio` for all concurrency
- Use async libraries: `httpx` (not `requests`), `aiosqlite` (not `sqlite3`), async drivers for DBs
- FastAPI endpoints are naturally async - keep them that way
- LangChain agents support async - use `ainvoke()`, `astream()` instead of `invoke()`, `stream()`

**Wrong:**
```python
def get_weather(city: str) -> dict:
    response = requests.get(f"https://api.weather.com/{city}")
    return response.json()
```

**Correct:**
```python
async def fetch_weather_data(city_name: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.weather.com/{city_name}")
        return response.json()
```

### Codebase Changes - MANDATORY

**ALL code modifications MUST use the `codebase_changes` skill. No exceptions.**

Before making any code changes, invoke this skill:
```
skill: "codebase_changes"
```

This skill enforces the project's code quality standards:

1. **Async-First Architecture** - ALL code must be `async`/`await`. No synchronous code. Use `httpx`, async DB drivers, `ainvoke()`, `astream()`.
2. **Strict Data Contracts** - Define Pydantic schemas for all external data. No `Any` types.
3. **Validate at Entry Point** - Validate once at the boundary, trust internal objects.
4. **Error Management** - Return structured state (`status`, `data`, `errors`), never "log and forget".
5. **No Nested Functions** - Define functions at module scope only. No closures.
6. **Small, Single-Purpose Functions** - One thing per function. Guard clauses over nesting.
7. **Semantic Naming** - No single letters, no `data`, `item`, `x`, `temp`. Names reveal intent.
8. **Named Boolean Conditions** - Complex `if` conditions must use named boolean variables.
9. **Constants Over Magic Numbers** - Replace all magic numbers with named constants.
10. **No Comments** - Self-documenting code only. Comments only when strictly necessary.
11. **Tests on Request Only** - Do not write tests unless explicitly asked.
12. **Reliability Patterns** - Retries with backoff, idempotent writes, circuit breakers.
13. **Database Optimization** - Bulk operations, selective retrieval, eager loading.

See `.claude/skills/codebase_changes/SKILL.md` for complete guidelines.

### LangChain Agent Creation - MANDATORY

**ONLY use `create_agent` from LangChain v1. Do NOT use:**
- `AgentExecutor` (deprecated)
- `initialize_agent` (deprecated)
- Legacy LangChain patterns
- Pre-v1 agent APIs

The current and correct way to create agents is:

```python
from langchain.agents import create_agent

agent = create_agent(
    model="openai:gpt-4.1",  # or ChatOpenAI instance
    tools=[tool1, tool2],
    system_prompt="You are a helpful assistant."
)
```

### No Comments in Code - MANDATORY

**Do NOT add comments in the codebase. Comments are forbidden by default.**

- No inline comments (`# comment`)
- No block comments
- No docstrings on functions/classes (unless strictly necessary for external APIs)
- No TODO/FIXME comments

**The only acceptable use of comments is when:**
1. The code implements a non-obvious algorithm that cannot be made self-explanatory
2. External API documentation is required (e.g., FastAPI endpoint descriptions)
3. Workaround for a third-party bug that cannot be fixed

**Write self-documenting code instead:**
- Use descriptive variable and function names
- Extract complex logic into well-named functions
- Use type hints to convey intent

```python
# WRONG - Do not do this
def get_weather(city: str) -> dict:
    # Fetch weather data from API
    # Returns temperature in Celsius
    response = requests.get(f"https://api.weather.com/{city}")
    return response.json()

# CORRECT - Self-documenting code
def fetch_current_weather_in_celsius(city_name: str) -> WeatherData:
    weather_api_url = f"https://api.weather.com/{city_name}"
    response = requests.get(weather_api_url)
    return WeatherData.from_json(response.json())
```

### Code Quality Rules

1. **Separation of Concerns** - Keep agent orchestration, tool definitions, API layer, and configuration separate
2. **Modular Structure** - Each tool in its own module under `src/tools/`
3. **Environment Variables** - All API keys via environment variables (never hardcoded)
4. **Type Hints** - Use Python 3.11+ syntax (`dict[str, str]` not `Dict[str, str]`)
5. **Pydantic Models** - All request/response schemas with Field descriptions

---

## LangChain Documentation

### Agent Creation with `create_agent`

[`create_agent`](https://reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent) provides a production-ready agent implementation using LangGraph.

#### Basic Agent

```python
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

# Using model identifier string
agent = create_agent("openai:gpt-4.1", tools=tools)

# Or with full configuration
model = ChatOpenAI(
    model="gpt-4.1",
    temperature=0.1,
    max_tokens=1000,
    timeout=30
)
agent = create_agent(model, tools=tools)
```

#### Agent with System Prompt

```python
agent = create_agent(
    model,
    tools=tools,
    system_prompt="You are a helpful financial assistant. Be concise and accurate."
)
```

#### Invoking an Agent

```python
result = agent.invoke({
    "messages": [{"role": "user", "content": "What's the weather in San Francisco?"}]
})
```

#### Streaming Responses

```python
from langchain.messages import AIMessage, HumanMessage

for chunk in agent.stream({
    "messages": [{"role": "user", "content": "Search for AI news"}]
}, stream_mode="values"):
    latest_message = chunk["messages"][-1]
    if latest_message.content:
        if isinstance(latest_message, HumanMessage):
            print(f"User: {latest_message.content}")
        elif isinstance(latest_message, AIMessage):
            print(f"Agent: {latest_message.content}")
    elif latest_message.tool_calls:
        print(f"Calling tools: {[tc['name'] for tc in latest_message.tool_calls]}")
```

### Tools

Tools give agents the ability to take actions. Use the `@tool` decorator:

```python
from langchain.tools import tool

@tool
def get_weather(location: str) -> str:
    """Get weather information for a location."""
    return f"Weather in {location}: Sunny, 72°F"

@tool
def get_stock_price(ticker: str) -> str:
    """Get current stock price for a ticker symbol."""
    return f"Stock {ticker}: $178.52"

agent = create_agent(model, tools=[get_weather, get_stock_price])
```

### Structured Output

For structured responses, use Pydantic models:

```python
from pydantic import BaseModel
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy

class WeatherInfo(BaseModel):
    location: str
    temperature: float
    conditions: str

agent = create_agent(
    model="gpt-4.1",
    tools=[weather_tool],
    response_format=ToolStrategy(WeatherInfo)
)

result = agent.invoke({"messages": [...]})
weather = result["structured_response"]  # WeatherInfo instance
```

### Memory and State

Agents maintain conversation history automatically. For custom state:

```python
from langchain.agents import AgentState

class CustomState(AgentState):
    user_preferences: dict

agent = create_agent(
    model,
    tools=tools,
    state_schema=CustomState
)

result = agent.invoke({
    "messages": [...],
    "user_preferences": {"style": "technical"}
})
```

### Middleware

Middleware provides extensibility for customizing agent behavior:

```python
from langchain.agents.middleware import wrap_tool_call, wrap_model_call

@wrap_tool_call
def handle_tool_errors(request, handler):
    """Handle tool execution errors with custom messages."""
    try:
        return handler(request)
    except Exception as e:
        return ToolMessage(
            content=f"Tool error: {str(e)}",
            tool_call_id=request.tool_call["id"]
        )

agent = create_agent(
    model="gpt-4.1",
    tools=[search, get_weather],
    middleware=[handle_tool_errors]
)
```

### Dynamic Tools

Filter tools based on state or context:

```python
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse

@wrap_model_call
def state_based_tools(request: ModelRequest, handler) -> ModelResponse:
    """Filter tools based on conversation state."""
    is_authenticated = request.state.get("authenticated", False)

    if not is_authenticated:
        tools = [t for t in request.tools if t.name.startswith("public_")]
        request = request.override(tools=tools)

    return handler(request)

agent = create_agent(
    model="gpt-4.1",
    tools=[public_search, private_search],
    middleware=[state_based_tools]
)
```

### Multi-Agent Patterns

For multi-agent systems, see the detailed documentation in:
- `.claude/skills/langchain/reference/advanced/subagents.md` - Supervisor pattern
- `.claude/skills/langchain/reference/advanced_examples/customer_support.md` - State machine
- `.claude/skills/langchain/reference/advanced_examples/router_knowleadge_agent.md` - Router pattern

---

## Commands

### Run the Application

```bash
# Using Python directly
python main.py

# Using uvicorn with hot reload
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Run with Docker

```bash
# Start all services (API, ChromaDB, Langfuse stack)
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### Development Setup

```bash
# Install dependencies with uv
uv sync

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Copy environment template
cp .env.example .env
# Edit .env with your API keys
```

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for LLM | Yes |
| `LANGFUSE_PUBLIC_KEY` | Langfuse public key | Optional |
| `LANGFUSE_SECRET_KEY` | Langfuse secret key | Optional |
| `LANGFUSE_HOST` | Langfuse host URL | Optional |

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/chat` | POST | Send message to AI assistant |
| `/docs` | GET | OpenAPI documentation |
| `/redoc` | GET | ReDoc documentation |

### Chat Endpoint Example

```http
POST /chat
Content-Type: application/json

{
  "message": "What's the weather in Montevideo and the price of AAPL?",
  "session_id": "optional-session-id"
}
```

Expected response:
```json
{
  "response": "In Montevideo, it's currently 22°C and partly cloudy. Apple (AAPL) is trading at $178.52 USD.",
  "tool_calls": [
    {"tool": "weather", "input": {"city": "Montevideo"}},
    {"tool": "stock_price", "input": {"ticker": "AAPL"}}
  ]
}
```

---

## Reference Documentation

For comprehensive LangChain patterns, see the skills folder:

### Basics
- `.claude/skills/langchain/reference/basics/agents.md` - Agent creation
- `.claude/skills/langchain/reference/basics/models.md` - LLM configuration
- `.claude/skills/langchain/reference/basics/messages.md` - Message types
- `.claude/skills/langchain/reference/basics/tools.md` - Tool definition
- `.claude/skills/langchain/reference/basics/structured_output.md` - Structured responses
- `.claude/skills/langchain/reference/basics/streaming.md` - Streaming tokens
- `.claude/skills/langchain/reference/basics/memorie_overview.md` - Memory types

### Advanced
- `.claude/skills/langchain/reference/advanced/rag_agent.md` - RAG implementation
- `.claude/skills/langchain/reference/advanced/subagents.md` - Multi-agent patterns
- `.claude/skills/langchain/reference/advanced/retrieval.md` - Vector stores

### Middleware
- `.claude/skills/langchain/reference/middleware/overview.md` - Middleware architecture
- `.claude/skills/langchain/reference/middleware/custom_middleware.md` - Custom middleware

---

# currentDate
Today's date is 2026-02-18.
