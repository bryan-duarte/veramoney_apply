# PostgreSQL Setup Implementation Spec

## Overview

This module defines the infrastructure changes needed to add a dedicated PostgreSQL service for agent memory storage.

## Files to Modify/Create

```
docker-compose.yml     # MODIFY - Add postgres-memory service
.env.example           # MODIFY - Add PostgreSQL memory variables
pyproject.toml         # MODIFY - Add asyncpg, sse-starlette dependencies
src/config/settings.py # MODIFY - Add PostgreSQL memory settings
```

---

## Implementation Guidelines

### docker-compose.yml (MODIFY)

**Purpose:** Add dedicated PostgreSQL service for memory storage

**Additions:**

1. Add `postgres-memory` service:

```yaml
  postgres-memory:
    image: postgres:17-alpine
    container_name: veramoney-memory
    environment:
      POSTGRES_USER: ${POSTGRES_MEMORY_USER:-veramoney}
      POSTGRES_PASSWORD: ${POSTGRES_MEMORY_PASSWORD:-veramoney_secret}
      POSTGRES_DB: ${POSTGRES_MEMORY_DB:-veramoney_memory}
    volumes:
      - postgres-memory-data:/var/lib/postgresql/data
    ports:
      - "${POSTGRES_MEMORY_PORT:-5433}:5432"
    networks:
      - vera-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_MEMORY_USER:-veramoney} -d ${POSTGRES_MEMORY_DB:-veramoney_memory}"]
      interval: 10s
      timeout: 5s
      retries: 5
```

2. Add volume:

```yaml
volumes:
  # ... existing volumes ...
  postgres-memory-data:
```

3. Update `app` service dependencies:

```yaml
  app:
    # ... existing config ...
    depends_on:
      chromadb:
        condition: service_healthy
      langfuse-web:
        condition: service_started
      postgres-memory:
        condition: service_healthy
```

**Complete service definition location:** After the existing `postgres` service

---

### .env.example (MODIFY)

**Purpose:** Add environment variables for PostgreSQL memory

**Additions:**

```bash
# PostgreSQL Memory Store (for agent conversation persistence)
POSTGRES_MEMORY_HOST=postgres-memory
POSTGRES_MEMORY_PORT=5433
POSTGRES_MEMORY_USER=veramoney
POSTGRES_MEMORY_PASSWORD=veramoney_secret
POSTGRES_MEMORY_DB=veramoney_memory

# Agent Configuration
AGENT_MODEL=gpt-5-mini
AGENT_TIMEOUT_SECONDS=30
AGENT_MAX_CONTEXT_MESSAGES=20
```

---

### pyproject.toml (MODIFY)

**Purpose:** Add required dependencies

**Additions to dependencies:**

```toml
dependencies = [
    # ... existing dependencies ...
    "asyncpg>=0.30.0",
    "sse-starlette>=2.1.0",
]
```

---

### src/config/settings.py (MODIFY)

**Purpose:** Add PostgreSQL memory configuration

**Additions:**

```python
class Settings(BaseSettings):
    # ... existing fields ...

    # PostgreSQL Memory Store
    postgres_memory_host: str = Field(
        default="localhost",
        description="PostgreSQL memory store host",
    )
    postgres_memory_port: int = Field(
        default=5433,
        description="PostgreSQL memory store port",
    )
    postgres_memory_user: str = Field(
        default="veramoney",
        description="PostgreSQL memory store user",
    )
    postgres_memory_password: str = Field(
        default="veramoney_secret",
        description="PostgreSQL memory store password",
    )
    postgres_memory_db: str = Field(
        default="veramoney_memory",
        description="PostgreSQL memory store database name",
    )

    # Agent Configuration
    agent_model: str = Field(
        default="gpt-5-mini",
        description="OpenAI model for conversational agent",
    )
    agent_timeout_seconds: float = Field(
        default=30.0,
        description="Timeout for LLM API calls in seconds",
    )
    agent_max_context_messages: int = Field(
        default=20,
        description="Maximum messages to keep in conversation context",
    )
```

---

## Database Schema

### conversations table

Created automatically by `PostgresMemoryStore.initialize()`

```sql
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID UNIQUE NOT NULL,
    messages JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversations_session_id
ON conversations(session_id);
```

---

## Network Configuration

The postgres-memory service connects to the existing `vera-network`:

```yaml
networks:
  vera-network:
    driver: bridge
```

---

## Volume Configuration

Persistent storage for memory data:

```yaml
volumes:
  postgres-memory-data:
    driver: local
```

---

## Health Check Configuration

Health check ensures PostgreSQL is ready before app starts:

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U veramoney -d veramoney_memory"]
  interval: 10s
  timeout: 5s
  retries: 5
```

---

## Integration Notes

1. PostgreSQL 17-alpine for minimal image size
2. Port 5433 mapped externally to avoid conflict with Langfuse PostgreSQL (5432)
3. Volume persists conversation data across container restarts
4. Health check ensures app waits for PostgreSQL to be ready
5. Connection pool in application handles concurrent requests

---

## Migration Notes

No migrations needed - schema is created on first startup via `initialize()` method.

For future schema changes:
1. Add migration scripts to `/migrations/` directory
2. Run migrations in lifespan or startup hook
3. Use version tracking in separate table if needed
