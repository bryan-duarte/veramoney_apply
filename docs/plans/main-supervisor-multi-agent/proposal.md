# Multi-Agent Supervisor Pattern Implementation

> *"Three agents walk into a bar. The supervisor says: 'I'll decide who gets to talk.'"*
> - El Barto

## Overview

**Request**: Refactor the current single-agent architecture to implement a multi-agent Supervisor Pattern using the "agent as a tool" approach, where a supervisor agent coordinates specialized worker agents for weather, stock, and knowledge domains.

**Created**: 2026-02-20

## What

Replace the existing single LangChain v1 agent with a hierarchical multi-agent system:

1. **Supervisor Agent** - Central coordinator that receives user requests and delegates to specialized workers
2. **Weather Worker Agent** - Specialist for weather-related queries
3. **Stock Worker Agent** - Specialist for stock price queries
4. **Knowledge Worker Agent** - Specialist for RAG/knowledge base queries

Each worker agent is wrapped as a LangChain tool, allowing the supervisor to invoke them via function calling.

## Why

### Current Limitations

- Single agent manages all three domains, potentially causing confusion
- No domain-specific optimization or specialization
- Complex system prompt trying to cover all use cases
- Limited ability to add domain-specific guardrails

### Benefits of Supervisor Pattern

1. **Domain Specialization** - Each worker has focused tools and prompts
2. **Context Isolation** - Workers don't pollute each other's context
3. **Independent Testing** - Each worker can be tested in isolation
4. **Cost Optimization** - Workers use smaller model (gpt-5-nano)
5. **Clear Delegation** - Supervisor makes routing decisions at domain level
6. **Scalability** - Easy to add new specialist workers

## Impact

### Files to Modify

| File | Change Type |
|------|-------------|
| `src/agent/core/factory.py` | Major refactor |
| `src/agent/core/prompts.py` | Add worker prompts |
| `src/api/handlers/chat_stream.py` | Update for progress events |
| `src/api/handlers/chat_complete.py` | Update response structure |
| `src/api/schemas.py` | Add worker call details |
| `src/observability/prompts.py` | Add worker prompt management |

### Files to Create

| File | Purpose |
|------|---------|
| `src/agent/workers/__init__.py` | Worker module initialization |
| `src/agent/workers/weather_worker.py` | Weather specialist agent |
| `src/agent/workers/stock_worker.py` | Stock specialist agent |
| `src/agent/workers/knowledge_worker.py` | Knowledge specialist agent |
| `src/agent/workers/base.py` | Base worker factory class |
| `src/agent/core/supervisor.py` | Supervisor agent factory |

### Files to Remove

| File | Reason |
|------|--------|
| None | All existing files will be refactored, not removed |

### Dependencies

No new dependencies required. Existing LangChain v1 stack supports this pattern natively.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         API Layer                                │
│  ┌──────────────────┐    ┌──────────────────────────────────┐   │
│  │ /chat/complete   │    │ /chat (streaming)                 │   │
│  └────────┬─────────┘    └────────────────┬─────────────────┘   │
│           │                               │                      │
│           ▼                               ▼                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Chat Handlers                            │ │
│  │  • Create supervisor via SupervisorFactory                  │ │
│  │  • Extract worker call details for response                 │ │
│  │  • Stream progress events (tool calls, results)            │ │
│  └────────────────────────────┬───────────────────────────────┘ │
└───────────────────────────────┼─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Supervisor Layer                            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                  Supervisor Agent                           │ │
│  │  • Model: gpt-5-mini-2025-08-07                            │ │
│  │  • Tools: [ask_weather_agent, ask_stock_agent,             │ │
│  │            ask_knowledge_agent]                             │ │
│  │  • Middleware: [logging, error_handler, guardrails]        │ │
│  │  • Checkpointer: AsyncPostgresSaver                        │ │
│  └────────────────────────────┬───────────────────────────────┘ │
│                               │                                  │
│          ┌────────────────────┼────────────────────┐            │
│          │                    │                    │            │
│          ▼                    ▼                    ▼            │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Weather Tool │    │  Stock Tool  │    │Knowledge Tool│      │
│  │ (wrapper)    │    │ (wrapper)    │    │ (wrapper)    │      │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘      │
└─────────┼───────────────────┼───────────────────┼──────────────┘
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Worker Layer                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │Weather Worker│    │Stock Worker  │    │Knowledge Wkr│       │
│  │              │    │              │    │              │       │
│  │ Model: nano  │    │ Model: nano  │    │ Model: nano  │       │
│  │ Tool: weather│    │ Tool: stock  │    │ Tool: search │       │
│  │ Memory: None │    │ Memory: None │    │ Memory: None │       │
│  │ MW: logging  │    │ MW: logging  │    │ MW: logging  │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

---

## References

- `.claude/skills/langchain/reference/advanced/subagents.md` - Supervisor pattern guide
- `docs/reports/proxy-agent-multi-agent-refactor.md` - Original analysis report
- `CLAUDE.md` - Project coding standards
