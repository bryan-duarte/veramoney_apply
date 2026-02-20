# Workers Implementation

## Overview

Create specialized worker agents for weather, stock, and knowledge domains. Each worker is a LangChain agent wrapped as a tool that the supervisor can invoke.

## Files to Create

| File | Purpose |
|------|---------|
| `src/agent/workers/__init__.py` | Module exports |
| `src/agent/workers/base.py` | BaseWorkerFactory and shared types |
| `src/agent/workers/weather_worker.py` | Weather specialist |
| `src/agent/workers/stock_worker.py` | Stock specialist |
| `src/agent/workers/knowledge_worker.py` | Knowledge specialist |

## Implementation Guidelines

### base.py - Shared Infrastructure

```
Purpose: Provide common functionality for all workers

Components:
- WorkerConfig: Pydantic model for worker configuration
- BaseWorkerFactory: Abstract base class with shared logic
- worker_logging_middleware: Minimal logging for worker agents

WorkerConfig Schema:
  name: str                    # "weather", "stock", "knowledge"
  model: str                   # Default: gpt-5-nano-2025-08-07
  tool: Callable               # The tool this worker uses
  prompt: str                  # System prompt
  description: str             # Tool description for supervisor

BaseWorkerFactory Methods:
  create_worker() -> Agent     # Creates configured worker
  _build_model() -> ChatOpenAI # Creates model instance
  _build_middleware() -> list  # Returns [worker_logging_middleware]
```

### weather_worker.py - Weather Specialist

```
Purpose: Handle weather-related queries

Dependencies:
- get_weather tool from src/tools/weather/tool.py

Prompt Guidelines:
- Parse natural language location requests
- Handle city name variations and disambiguation
- Format weather data clearly with temperature in Celsius

Tool Wrapper:
@tool
def ask_weather_agent(request: str) -> str:
    '''Route weather-related questions to the weather specialist.
    Use for: current weather, temperature, conditions, forecasts'''
    # Error handling with user-friendly message

Worker Agent Config:
  model: gpt-5-nano-2025-08-07
  tools: [get_weather]
  middleware: [worker_logging_middleware]
  checkpointer: None
```

### stock_worker.py - Stock Specialist

```
Purpose: Handle stock price queries

Dependencies:
- get_stock_price tool from src/tools/stock/tool.py

Prompt Guidelines:
- Parse ticker symbols from natural language
- Handle company name to ticker resolution (AAPL = Apple)
- Format price data with change and percentage

Tool Wrapper:
@tool
def ask_stock_agent(request: str) -> str:
    '''Route stock price questions to the stock specialist.
    Use for: stock prices, market data, ticker quotes'''
    # Error handling with user-friendly message

Worker Agent Config:
  model: gpt-5-nano-2025-08-07
  tools: [get_stock_price]
  middleware: [worker_logging_middleware]
  checkpointer: None
```

### knowledge_worker.py - Knowledge Specialist

```
Purpose: Handle RAG/knowledge base queries

Dependencies:
- search_knowledge tool from src/tools/knowledge/tool.py
- KnowledgeRetriever from src/rag/retriever.py

Prompt Guidelines:
- Search knowledge base with appropriate queries
- Always cite document titles in responses
- Indicate when information is not in knowledge base

Tool Wrapper:
@tool
def ask_knowledge_agent(request: str) -> str:
    '''Route knowledge base questions to the document specialist.
    Use for: VeraMoney history, fintech regulations, banking policies'''
    # Error handling with user-friendly message

Worker Agent Config:
  model: gpt-5-nano-2025-08-07
  tools: [search_knowledge]  # Created with retriever injection
  middleware: [worker_logging_middleware]
  checkpointer: None

Special Considerations:
- Requires KnowledgeRetriever injection
- Tool created via factory function with retriever parameter
```

## Dependencies

```
src/agent/workers/
├── depends on → src/tools/weather/tool.py
├── depends on → src/tools/stock/tool.py
├── depends on → src/tools/knowledge/tool.py
├── depends on → src/rag/retriever.py (knowledge worker only)
└── depends on → langchain.agents.create_agent
```

## Integration Notes

1. Workers are imported by `src/agent/core/supervisor.py`
2. Tool wrappers (`ask_*_agent`) are passed to supervisor's tools list
3. Workers have NO checkpointer - stateless execution
4. Workers have minimal middleware - only logging
5. Error handling in tool wrapper ensures graceful degradation
