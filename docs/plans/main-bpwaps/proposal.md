# Conversational Agent Implementation Plan

> "Building an AI that actually listens to tools instead of hallucinating - what a novel concept."
> - El Barto

## Overview

**Request**: Implement a conversational agent for VeraMoney Apply that can understand user intent, call weather and stock tools, handle multi-turn conversations with persistent memory, and stream responses via Server-Sent Events.

**Created**: 2026-02-18

## What

Build a production-ready conversational agent with the following capabilities:

1. **Conversational Agent** - LangChain v1 agent using `create_agent()` with middleware
2. **Tool Integration** - Register existing weather and stock tools for autonomous use
3. **Persistent Memory** - PostgreSQL-backed conversation storage with session_id threading
4. **Streaming Responses** - Server-Sent Events for real-time token delivery
5. **Error Handling** - Natural error messages with tool error handler middleware
6. **Hallucination Prevention** - Combined approach with prompt rules and output guardrails

## Why

This implementation fulfills **Task 3: Conversational Agent** from the code challenge requirements:

- User intent understanding and tool routing
- Multi-turn conversation with context management
- Proper tool output integration without hallucination
- Professional financial assistant persona (Vera AI)

## Impact

### Files Created
- `src/agent/core/conversational_agent.py` - Main agent factory
- `src/agent/core/prompts.py` - System prompt definitions
- `src/agent/memory/postgres_store.py` - PostgreSQL memory implementation
- `src/agent/memory/checkpointer.py` - LangGraph checkpointer adapter
- `src/agent/middleware/tool_error_handler.py` - Tool error middleware
- `src/agent/middleware/output_guardrails.py` - Output validation middleware
- `src/agent/middleware/logging_middleware.py` - Request/response logging
- `src/api/endpoints/chat_stream.py` - Streaming endpoint (SSE)
- `src/api/endpoints/chat_complete.py` - Batch endpoint

### Files Modified
- `docker-compose.yml` - Add postgres-memory service
- `src/api/core/dependencies.py` - Add AgentDep dependency
- `src/api/endpoints/__init__.py` - Update router exports
- `src/api/app.py` - Include new routers
- `src/config/settings.py` - Add PostgreSQL memory settings
- `pyproject.toml` - Add asyncpg, sse-starlette dependencies
- `.env.example` - Add PostgreSQL memory variables

### Infrastructure
- New PostgreSQL service for persistent memory
- New `/chat` streaming endpoint (SSE)
- New `/chat/complete` batch endpoint
