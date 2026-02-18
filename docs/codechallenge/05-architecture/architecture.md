# Phase 5: Architecture & Quality

> Status: PARTIAL
> Priority: MEDIUM

## Overview

Ensure clean separation of concerns and production-ready code quality.

## Current Status

| ID | Task | Status | Notes |
|----|------|--------|-------|
| 5.1 | Separate agent orchestration | TODO | Agent logic in `src/agent/` |
| 5.2 | Separate tool definitions | TODO | Tools in `src/tools/` |
| 5.3 | Separate API layer | DONE | `src/api/` with core/ and endpoints/ |
| 5.4 | Separate configuration | DONE | `src/config/` with singleton |
| 5.5 | Add logging | PARTIAL | Basic logging exists |
| 5.6 | Add error handling | DONE | Global exception handler |

## Current Architecture

```
src/
├── api/
│   ├── app.py              # FastAPI factory
│   ├── core/               # Infrastructure
│   │   ├── dependencies.py
│   │   ├── exception_handlers.py
│   │   ├── middleware.py
│   │   └── rate_limiter.py
│   └── endpoints/
│       ├── chat.py
│       └── health.py
├── config/
│   ├── enums.py
│   └── settings.py
├── agent/                  # TODO
├── tools/                  # TODO
├── rag/                    # TODO (Bonus)
└── observability/          # TODO (Bonus)
```

## Target Architecture

```
src/
├── api/
│   ├── app.py
│   ├── core/
│   │   ├── dependencies.py
│   │   ├── exception_handlers.py
│   │   ├── middleware.py
│   │   └── rate_limiter.py
│   └── endpoints/
│       ├── chat.py
│       └── health.py
├── config/
│   ├── enums.py
│   └── settings.py
├── agent/
│   ├── __init__.py
│   ├── conversational_agent.py
│   ├── prompts.py
│   └── memory.py
├── tools/
│   ├── __init__.py
│   ├── weather/
│   │   ├── tool.py
│   │   ├── schemas.py
│   │   └── client.py
│   └── stock/
│       ├── tool.py
│       ├── schemas.py
│       └── client.py
├── rag/                    # Bonus
│   ├── __init__.py
│   ├── embeddings.py
│   ├── retriever.py
│   └── knowledge_base/
└── observability/          # Bonus
    ├── __init__.py
    └── langfuse_client.py
```

## Separation of Concerns

### API Layer (`src/api/`)
- HTTP request/response handling
- Authentication and authorization
- Rate limiting
- Error handling

### Agent Layer (`src/agent/`)
- LLM orchestration
- Tool routing
- Memory management
- Conversation flow

### Tools Layer (`src/tools/`)
- External API clients
- Tool schema definitions
- Response parsing
- Error handling

### Configuration Layer (`src/config/`)
- Environment variables
- Feature flags
- Secrets management
- Application settings

## Logging Standards

```python
import logging

logger = logging.getLogger(__name__)

# Log levels
logger.debug("Detailed debugging information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred", extra={"error": str(e)})
logger.exception("Exception with traceback")
```

## Code Quality Checklist

- [ ] All functions are async
- [ ] Pydantic schemas for all inputs/outputs
- [ ] No magic numbers - use constants
- [ ] Named boolean conditions
- [ ] No nested functions
- [ ] Self-documenting code (no comments)
- [ ] Type hints on all functions
- [ ] Error handling at boundaries
