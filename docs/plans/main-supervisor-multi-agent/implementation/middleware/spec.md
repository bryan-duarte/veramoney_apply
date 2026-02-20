# Middleware Implementation

## Overview

Add worker-level logging middleware for minimal observability on worker agents. The supervisor retains the full middleware stack.

## Files to Create/Modify

| File | Change Type | Purpose |
|------|-------------|---------|
| `src/agent/middleware/worker_logging.py` | New | Minimal logging for workers |
| `src/agent/workers/base.py` | Modify | Import and use worker logging |

## Implementation Guidelines

### worker_logging.py - Worker Logging Middleware

```
Purpose: Provide minimal logging for worker agent execution

Design Principles:
- Minimal overhead (workers should be fast)
- No guardrails (those are at supervisor level)
- Simple request/response logging
- Include worker name and trace correlation

@wrap_model_call
async def worker_logging_middleware(request: ModelRequest, handler) -> ModelResponse:
    1. Extract worker context from request state
    2. Log worker request with tool name
    3. Time the handler execution
    4. Log worker response with duration
    5. Return response

Log Format:
  worker_request worker={name} tool={tool_name}
  worker_response worker={name} duration={ms}ms content_len={len}
```

### Middleware Distribution

```
Supervisor Middleware Stack (Full):
├── logging_middleware         # Request/response timing
├── tool_error_handler         # Graceful error messages
├── output_guardrails          # Hallucination detection
└── knowledge_guardrails       # Citation validation

Worker Middleware Stack (Minimal):
└── worker_logging_middleware  # Basic logging only
```

### Guardrails Consideration

```
Why No Guardrails on Workers:

1. Workers use a single tool - limited hallucination surface
2. Output guardrails at supervisor level catch any issues
3. Knowledge guardrails only relevant for knowledge worker
4. Error handling in tool wrapper provides safety net

Future Enhancement:
- Add worker-specific guardrails if needed
- Per-worker middleware configuration
```

## Dependencies

```
src/agent/middleware/worker_logging.py
├── imports → langchain.agents.middleware (wrap_model_call, ModelRequest, ModelResponse)
├── imports → logging (standard library)
└── imports → time (for perf_counter)
```

## Integration Notes

1. Worker logging middleware is imported by `BaseWorkerFactory`
2. Added to worker's middleware list during creation
3. No changes to existing supervisor middleware
4. Logs are correlated via session_id in request state
