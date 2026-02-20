# Chainlit + FastAPI Proxy Integration (Pattern B)

> *"Why build a chat UI when Chainlit already did it better than you would have?"*
> — El Barto

## Overview

**Request**: Integrate Chainlit with the FastAPI backend using Pattern B (Proxy Integration) where Chainlit acts as a frontend that forwards requests to the existing `/chat` SSE endpoint.

**Created**: 2026-02-19

## What

Implement a Chainlit-based chat UI that connects to the existing VeraMoney FastAPI backend via HTTP/SSE. The Chainlit application will:

- Act as a pure frontend layer with no direct LLM or tool access
- Forward all user messages to the FastAPI `/chat` endpoint
- Parse SSE events (token, tool_call, tool_result, done, error) from the backend
- Display streaming responses with minimal tool visualization
- Handle authentication, rate limiting, and error states gracefully

## Why

Pattern B provides:

1. **Production-Ready Security**: Preserves FastAPI authentication (X-API-Key) and rate limiting (60 req/min)
2. **Clean Separation**: Frontend and backend are independently deployable and scalable
3. **Existing Infrastructure**: Leverages the current docker-compose stack without modification
4. **No API Key Exposure**: LLM and tool API keys remain in the backend only

## Impact

### Files Created
- `src/chainlit/__init__.py` - Module exports
- `src/chainlit/app.py` - Main Chainlit application
- `src/chainlit/config.py` - Chainlit configuration settings
- `src/chainlit/handlers.py` - Event handlers (on_chat_start, on_message)
- `src/chainlit/sse_client.py` - SSE stream client for backend communication
- `.chainlit/config.toml` - Chainlit UI configuration
- `.chainlit/settings.json` - Chainlit settings

### Files Modified
- `docker-compose.yml` - Add Chainlit service
- `.env.example` - Add CHAINLIT_API_KEY, CHAINLIT_PORT, CORS_ORIGINS update
- `Dockerfile` - Add Chainlit to development stage (optional)

### Architecture Impact
```
[User Browser]
      |
      v
[Chainlit UI :8002] --httpx SSE--> [FastAPI /chat :8000] --> [Agent + Tools]
      |                                    |
      v                                    v
[cl.Message]                        [Rate Limiting]
[cl.Step (minimal)]                 [API Key Auth]
[Auto-retry]                        [SSE Events]
```

## Scope

### In Scope
- Chainlit application module in `src/chainlit/`
- SSE client for consuming FastAPI streaming endpoint
- Docker Compose service configuration
- Environment variable configuration
- Error handling with auto-retry
- Welcome message with suggested prompts
- Minimal tool visualization (name only)

### Out of Scope
- Direct LangChain integration (Pattern A)
- Multi-agent patterns
- RAG integration
- Tests (per user preference)
- Documentation updates (per user preference)
