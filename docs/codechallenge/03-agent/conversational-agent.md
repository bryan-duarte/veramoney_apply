# Task 3: Conversational Agent

> Status: TODO
> Priority: HIGH (Core Requirement)

## Overview

Build a conversational agent capable of understanding user intent, deciding when to call tools, and handling multi-turn conversation.

## Requirements

- Understand user intent
- Decide whether to respond directly or call tools
- Handle multi-turn conversation
- Avoid hallucinating tool results
- Properly integrate tool outputs into responses

## Tasks

| ID | Task | Status | Notes |
|----|------|--------|-------|
| 3.1 | Design system prompt | TODO | Define behavior, capabilities, constraints |
| 3.2 | Implement intent recognition | TODO | Agent understands what user wants |
| 3.3 | Implement tool routing logic | TODO | Decide: respond directly OR call tool |
| 3.4 | Register tools with agent | TODO | Connect Weather and Stock tools |
| 3.5 | Implement tool execution | TODO | Call tools and capture results |
| 3.6 | Integrate tool outputs | TODO | Inject tool results into final response |
| 3.7 | Implement context management | TODO | Maintain conversation history |
| 3.8 | Prevent hallucination | TODO | Ensure agent only uses real tool results |

## Agent Decision Flow

```
User Message
    │
    ▼
┌─────────────────┐
│ Intent Analysis │
└────────┬────────┘
         │
    ┌────┴────┬────────────┐
    ▼         ▼            ▼
 Weather   Stock      General
  Tool     Tool      Response
    │         │            │
    └────┬────┴────────────┘
         ▼
┌─────────────────┐
│ Final Response  │
└─────────────────┘
```

## Implementation Location

```
src/agent/
├── __init__.py
├── conversational_agent.py   # Main agent implementation
├── prompts.py                # System prompts
└── memory.py                 # Conversation memory
```

## LangChain Approach

**Reference:** `.claude/skills/langchain/reference/basics/agents.md`

Use `create_agent` from LangChain v1:

```python
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from src.tools.weather import get_weather
from src.tools.stock import get_stock_price

model = ChatOpenAI(model="gpt-4o-mini")

agent = create_agent(
    model,
    tools=[get_weather, get_stock_price],
    system_prompt="""You are a helpful financial assistant.
    You can answer questions about weather and stock prices.
    When asked about weather, use the get_weather tool.
    When asked about stock prices, use the get_stock_price tool.
    For general questions, respond directly without using tools.
    Always be accurate and cite your sources."""
)
```

## Memory Management

**Reference:** `.claude/skills/langchain/reference/basics/memorie_overview.md`

```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)
```

## System Prompt Design

```python
SYSTEM_PROMPT = """
You are Vera, a helpful AI assistant for VeraMoney.

Capabilities:
- Answer general questions
- Get weather information for any city
- Get stock prices for any ticker symbol

Rules:
- Only use tools when necessary
- Never make up tool results
- Be concise and accurate
- Cite sources when using tools
"""
```

## Hallucination Prevention

1. **Explicit instructions** - Tell agent not to invent data
2. **Tool result validation** - Check tool outputs before using
3. **Fallback responses** - Handle tool failures gracefully
4. **Structured output** - Use Pydantic for response validation

## Testing

```bash
# Unit test
pytest tests/agents/test_conversational.py

# Integration tests
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"message": "Hello, who are you?"}'

curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"message": "What is the weather in Montevideo and AAPL price?"}'
```

## Dependencies

```toml
langchain>=1.2.10
langchain-openai>=1.1.10
```
