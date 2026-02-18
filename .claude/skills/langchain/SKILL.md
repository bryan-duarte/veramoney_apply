---
name: langchain
description: LangChain framework expertise for building LLM applications. Use when working with LangChain, LangGraph, agents, chains, memory systems, streaming, tools, structured output, middleware, retrieval, or context engineering. Covers Python implementation patterns and best practices.
---

# LangChain Skill

Expert guidance for building production-ready LLM applications using LangChain and LangGraph frameworks. This skill provides comprehensive reference documentation organized by complexity level.

## Quick Start

When working with LangChain, always start by understanding the core components:

1. **Models** - LLM and chat model integrations
2. **Messages** - Conversation message formats and management
3. **Tools** - Function calling and tool integration
4. **Agents** - Autonomous agents with tool use

For these fundamentals, see [reference/basics/](reference/basics/).

## Reference Structure

### Basics

Core LangChain concepts every project needs:

| Topic | File | Description |
|-------|------|-------------|
| **Models** | [models.md](reference/basics/models.md) | LLM and chat model integrations, configuration, and usage |
| **Messages** | [messages.md](reference/basics/messages.md) | Message types (Human, AI, System, Tool) and conversation patterns |
| **Tools** | [tools.md](reference/basics/tools.md) | Defining and using tools for function calling |
| **Agents** | [agents.md](reference/basics/agents.md) | Building agents that use tools autonomously |
| **Structured Output** | [structured_output.md](reference/basics/structured_output.md) | Getting structured JSON/Pydantic responses from LLMs |
| **Streaming** | [streaming.md](reference/basics/streaming.md) | Streaming token responses for real-time output |
| **Streaming Frontend** | [streaming_frontend.md](reference/basics/streaming_frontend.md) | Frontend integration patterns for streaming responses |
| **Short-term Memory** | [short_term_memorie.md](reference/basics/short_term_memorie.md) | Conversation history and state management |
| **Memory Overview** | [memorie_overview.md](reference/basics/memorie_overview.md) | Comprehensive guide to memory types: short-term (thread-scoped) vs long-term (cross-session), semantic/episodic/procedural memory patterns, and memory storage with LangGraph stores |

### Middleware

Cross-cutting concerns and middleware patterns:

| Topic | File | Description |
|-------|------|-------------|
| **Overview** | [overview.md](reference/middleware/overview.md) | Middleware architecture and patterns in LangGraph |
| **Prebuilt Middleware** | [prebuilt_middleware.md](reference/middleware/prebuilt_middleware.md) | Ready-to-use middleware components |
| **Custom Middleware** | [custom_middleware.md](reference/middleware/custom_middleware.md) | Building custom middleware for specific needs |

### Advanced

Complex patterns and production features:

| Topic | File | Description |
|-------|------|-------------|
| **Context Engineering** | [context_engineering.md](reference/advanced/context_engineering.md) | Managing context windows and prompt optimization |
| **Retrieval** | [retrieval.md](reference/advanced/retrieval.md) | RAG patterns, vector stores, and retrieval strategies |
| **Long-term Memory** | [long_term_memorie.md](reference/advanced/long_term_memorie.md) | Persistent memory and cross-session state |
| **Guardrails** | [guardrails.md](reference/advanced/guardrails.md) | Input/output validation, safety, and compliance |
| **RAG Agent** | [rag_agent.md](reference/advanced/rag_agent.md) | Complete tutorial for building RAG applications with agents (retrieval tools) or chains (single LLM call). Covers indexing, document loading, text splitting, vector stores, and generation |
| **SQL Agent** | [sql_agent.md](reference/advanced/sql_agent.md) | Build an agent that answers questions about SQL databases. Covers database tools, query checking, human-in-the-loop review for query approval, and error recovery |
| **Subagents (Supervisor)** | [subagents.md](reference/advanced/subagents.md) | Supervisor pattern with specialized sub-agents. Calendar and email agent example showing tool wrapping, multi-domain coordination, and human-in-the-loop for action approval |

### Advanced Examples

Real-world multi-agent patterns and complete implementations:

| Topic | File | Description |
|-------|------|-------------|
| **Customer Support (State Machine)** | [customer_support.md](reference/advanced_examples/customer_support.md) | State machine pattern for customer support workflows. Shows how to use tool calls to dynamically change agent configuration (prompt + tools) based on workflow progress. Includes warranty verification, issue classification, and resolution steps |
| **Knowledge Router** | [router_knowleadge_agent.md](reference/advanced_examples/router_knowleadge_agent.md) | Router pattern for multi-source knowledge bases. Classifies queries and routes to specialized agents (GitHub, Notion, Slack) in parallel using LangGraph's Send API, then synthesizes results. Ideal for distinct knowledge verticals |

## Common Workflows

### Building a Simple Agent

```
1. Read [reference/basics/models.md] to configure your LLM
2. Read [reference/basics/tools.md] to define available tools
3. Read [reference/basics/agents.md] to create the agent
4. Read [reference/basics/messages.md] for conversation handling
```

### Adding Memory to an Agent

```
1. Read [reference/basics/memorie_overview.md] for memory concepts and types
2. Read [reference/basics/short_term_memorie.md] for conversation history
3. Read [reference/advanced/long_term_memorie.md] for persistent storage
4. Read [reference/advanced/context_engineering.md] for window management
```

### Building a RAG Application

```
1. Read [reference/advanced/rag_agent.md] for complete RAG implementation
2. Read [reference/advanced/retrieval.md] for vector store setup
3. Read [reference/basics/structured_output.md] for parsed responses
4. Read [reference/basics/streaming.md] for real-time answer generation
```

### Building Multi-Agent Systems

```
1. Read [reference/advanced/subagents.md] for supervisor pattern with specialized agents
2. Read [reference/advanced_examples/customer_support.md] for state machine workflows
3. Read [reference/advanced_examples/router_knowleadge_agent.md] for parallel routing
```

### Building a SQL Agent

```
1. Read [reference/advanced/sql_agent.md] for complete SQL agent tutorial
2. Read [reference/basics/tools.md] for database tool patterns
3. Read [reference/middleware/prebuilt_middleware.md] for human-in-the-loop review
```

### Production Deployment

```
1. Read [reference/middleware/overview.md] for request/response handling
2. Read [reference/advanced/guardrails.md] for safety validation
3. Read [reference/basics/streaming_frontend.md] for UI integration
```

## When to Use This Skill

Invoke this skill when:
- Building agents or chains with LangChain/LangGraph
- Implementing tool use or function calling
- Setting up streaming responses
- Adding memory or state management
- Building RAG or retrieval systems
- Implementing middleware patterns
- Structuring LLM outputs
- Managing conversation context
- Designing multi-agent architectures

## Architecture Notes

LangChain provides:
- **LangChain Core**: Base abstractions (messages, tools, output parsers)
- **LangChain Community**: Integrations (model providers, vector stores)
- **LangGraph**: Stateful agent orchestration with cycles

LangGraph is the recommended approach for building agents, offering:
- Explicit state management
- Cycle support for iterative workflows
- Built-in memory and persistence
- Middleware support for cross-cutting concerns

## Multi-Agent Patterns Summary

| Pattern | Use Case | Key File |
|---------|----------|----------|
| **Subagents/Supervisor** | Centralized orchestration of specialized agents | [subagents.md](reference/advanced/subagents.md) |
| **State Machine** | Sequential workflows with dynamic configuration | [customer_support.md](reference/advanced_examples/customer_support.md) |
| **Router** | Parallel queries to multiple knowledge sources | [router_knowleadge_agent.md](reference/advanced_examples/router_knowleadge_agent.md) |
