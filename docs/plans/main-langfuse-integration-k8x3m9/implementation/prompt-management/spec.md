# Prompt Management Implementation

## Overview

Implement Langfuse prompt synchronization for the VERA_SYSTEM_PROMPT with code fallback.

## Files to Modify

| File | Changes |
|------|---------|
| `src/api/app.py` | Add prompt sync at startup |
| `src/config/settings.py` | Add Langfuse computed fields |

---

## Settings Changes (settings.py)

### Add Computed Fields

```
@computed_field
@property
def langfuse_enabled(self) -> bool:
    has_public_key = self.langfuse_public_key is not None
    has_secret_key = self.langfuse_secret_key is not None
    return has_public_key and has_secret_key

@computed_field
@property
def langfuse_environment(self) -> str:
    return self.app_stage.value  # development, qa, production
```

### These Enable

- `settings.langfuse_enabled` - Quick check if Langfuse should be used
- `settings.langfuse_environment` - Tag traces with environment

---

## App Lifespan Changes (app.py)

### Current Lifespan

```
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Configure logging
    configure_logging(settings.log_level)
    logger.info("Starting VeraMoney API...")

    # Initialize RAG pipeline
    await initialize_rag_pipeline()

    yield

    # Cleanup
    logger.info("Shutting down VeraMoney API...")
```

### Changes Required

1. **Import observability modules:**

```
from src.observability import (
    get_langfuse_client,
    sync_prompt_to_langfuse,
    PROMPT_NAME_VERA_SYSTEM,
)
from src.agent.core.prompts import VERA_SYSTEM_PROMPT
```

2. **Initialize Langfuse client:**

```
# Initialize Langfuse client (if configured)
langfuse_client = get_langfuse_client()
if langfuse_client:
    logger.info("Langfuse client initialized successfully")
else:
    logger.debug("Langfuse not configured - observability disabled")
```

3. **Sync prompts to Langfuse:**

```
# Sync system prompt to Langfuse
if langfuse_client:
    sync_prompt_to_langfuse(
        client=langfuse_client,
        prompt_name=PROMPT_NAME_VERA_SYSTEM,
        prompt_content=VERA_SYSTEM_PROMPT,
    )
    logger.info("System prompt synced to Langfuse")
```

4. **Flush on shutdown:**

```
# Flush pending traces
if langfuse_client:
    langfuse_client.flush()
    logger.info("Langfuse traces flushed")
```

### Full Updated Lifespan

```
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Configure logging
    configure_logging(settings.log_level)
    logger.info("Starting VeraMoney API...")

    # Initialize Langfuse client
    langfuse_client = get_langfuse_client()
    if langfuse_client:
        logger.info("Langfuse client initialized")
        sync_prompt_to_langfuse(
            client=langfuse_client,
            prompt_name=PROMPT_NAME_VERA_SYSTEM,
            prompt_content=VERA_SYSTEM_PROMPT,
        )
    else:
        logger.debug("Langfuse not configured")

    # Initialize RAG pipeline
    await initialize_rag_pipeline()

    yield

    # Shutdown
    logger.info("Shutting down VeraMoney API...")

    # Flush Langfuse traces
    if langfuse_client:
        langfuse_client.flush()
```

---

## Prompt Sync Behavior

### At Startup

1. `sync_prompt_to_langfuse()` is called
2. Checks if prompt exists in Langfuse
3. If missing: creates prompt with current code version
4. If exists: does nothing (no updates)

### At Agent Creation

1. `get_system_prompt()` is called
2. Fetches prompt from Langfuse
3. If unavailable: returns code-based fallback
4. Agent uses whichever version was returned

### Version Control

- Langfuse UI can manage versions
- Code version is the source of truth for creation
- Langfuse can have newer versions via UI edits
- Agent uses latest Langfuse version if available

---

## Graceful Degradation

### If Langfuse Keys Missing

- `get_langfuse_client()` returns None
- Sync is skipped
- Agent uses code-based prompt
- No errors, just debug log

### If Langfuse Connection Fails

- `get_langfuse_client()` returns None (after logging warning)
- Same behavior as missing keys
- App continues normally

### If Prompt Fetch Fails

- `get_system_prompt()` returns fallback
- Warning logged
- Agent uses fallback prompt

---

## No Database Changes

This implementation does NOT require:

- Schema migrations
- New tables
- Data seeding

All prompt data is stored in Langfuse, not in the application database.
