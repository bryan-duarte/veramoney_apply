# Langfuse Observability Integration

> "Observability is like a time machine for your bugs - you can see exactly when you broke everything."
> - El Barto

## Overview

**Request**: Add comprehensive Langfuse observability to the entire VeraMoney Apply project, using session_id as the primary trace key, capturing opening messages in a dataset, and enabling prompt versioning.

**Created**: 2026-02-20

## What

Implement full Langfuse SDK integration including:

1. **Trace Management**: All API requests traced with session_id as trace_id
2. **CallbackHandler Integration**: Standard LangChain pattern for automatic tracing
3. **Dataset Collection**: USER_OPENING_MESSAGES and STOCK_QUERIES datasets
4. **Chat-Type Prompt Management**: Migrate VERA_SYSTEM_PROMPT to Langfuse with:
   - `type="chat"` for proper LangChain integration
   - Dynamic variables: `{{current_date}}`, `{{model_name}}`, `{{version}}`
   - `chat_history` placeholder for conversation memory
   - Code fallback when Langfuse unavailable
5. **Full Operation Tracing**: LLM calls, tool executions, RAG retrieval, embeddings
6. **Trace Linking**: Prompt version metadata in traces for analysis

## Why

The project has Langfuse infrastructure running (Docker stack) but no actual Python integration. This implementation enables:

- **Session-level visibility**: See complete conversation flows per user session
- **Tool performance monitoring**: Track weather/stock/knowledge API calls
- **RAG quality analysis**: Monitor retrieval effectiveness
- **Evaluation readiness**: Collect test cases for automated testing
- **Prompt experimentation**: A/B test and version control system prompts

## Impact

### Files to Create

| File | Purpose |
|------|---------|
| `src/observability/__init__.py` | Public API exports |
| `src/observability/client.py` | Langfuse client singleton |
| `src/observability/handler.py` | CallbackHandler factory |
| `src/observability/datasets.py` | Dataset management service |
| `src/observability/prompts.py` | Prompt sync service |

### Files to Modify

| File | Changes |
|------|---------|
| `src/config/settings.py` | Add Langfuse-specific settings |
| `src/agent/core/conversational_agent.py` | Integrate CallbackHandler |
| `src/agent/core/prompts.py` | Add Langfuse prompt fetch logic |
| `src/api/app.py` | Initialize Langfuse at startup |
| `src/api/endpoints/chat_complete.py` | Trace management, dataset collection |
| `src/api/endpoints/chat_stream.py` | Trace management, dataset collection |

### Behavioral Changes

- All chat requests create/update Langfuse traces
- Opening messages per session added to USER_OPENING_MESSAGES dataset
- Stock tool queries added to STOCK_QUERIES dataset
- System prompt fetched from Langfuse with code fallback
- Graceful degradation if Langfuse unavailable
