# Agent Memory Implementation Spec

## Overview

This module implements PostgreSQL-backed persistent memory for conversation storage, providing session isolation and FIFO message management.

## Files to Create

```
src/agent/memory/
├── __init__.py           # Re-exports
├── postgres_store.py     # PostgreSQL memory implementation
└── checkpointer.py       # LangGraph checkpointer adapter
```

---

## Implementation Guidelines

### src/agent/memory/__init__.py

**Purpose:** Module-level exports

**Exports:**
- `PostgresMemoryStore` from `.postgres_store`
- `create_checkpointer` from `.checkpointer`

---

### src/agent/memory/postgres_store.py

**Purpose:** PostgreSQL-backed memory store for conversations

**Guidelines:**

1. Define `PostgresMemoryStore` class

2. Class initialization:
   - Accept connection settings (host, port, user, password, database)
   - Create async connection pool on initialization
   - Pool configuration: min_size=5, max_size=20

3. Implement `async def initialize()`:
   - Create conversations table if not exists
   - Create index on session_id

4. Implement `async def get_conversation(session_id: str)`:
   - Query conversations table by session_id
   - Return list of messages (empty list if not found)
   - Messages are stored as JSONB array

5. Implement `async def save_message(session_id: str, message: dict)`:
   - Append message to JSONB array
   - Update updated_at timestamp
   - Use UPSERT (insert on conflict update)

6. Implement `async def trim_messages(session_id: str, max_count: int)`:
   - Keep only most recent `max_count` messages
   - Use JSONB array slicing
   - FIFO: remove oldest messages first

7. Implement `async def close()`:
   - Close connection pool gracefully

8. All methods must be async

9. Use asyncpg for PostgreSQL connections

10. Use parameterized queries only (prevent SQL injection)

11. No comments - code should be self-documenting

**Pseudocode:**
```
class PostgresMemoryStore:
    def __init__(self, settings: Settings):
        self._pool: asyncpg.Pool | None = None
        self._settings = settings

    async def initialize(self) -> None:
        self._pool = await asyncpg.create_pool(
            host=self._settings.postgres_memory_host,
            port=self._settings.postgres_memory_port,
            user=self._settings.postgres_memory_user,
            password=self._settings.postgres_memory_password,
            database=self._settings.postgres_memory_db,
            min_size=5,
            max_size=20
        )
        await self._create_schema()

    async def _create_schema(self) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    session_id UUID UNIQUE NOT NULL,
                    messages JSONB DEFAULT '[]'::jsonb,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_session_id
                ON conversations(session_id)
            """)

    async def get_conversation(self, session_id: str) -> list[dict]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT messages FROM conversations WHERE session_id = $1",
                session_id
            )
            return row["messages"] if row else []

    async def save_message(self, session_id: str, message: dict) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO conversations (session_id, messages, updated_at)
                VALUES ($1, jsonb_build_array($2::jsonb), NOW())
                ON CONFLICT (session_id)
                DO UPDATE SET
                    messages = conversations.messages || $2::jsonb,
                    updated_at = NOW()
            """, session_id, json.dumps(message))

    async def trim_messages(self, session_id: str, max_count: int) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute("""
                UPDATE conversations
                SET messages = messages -$1
                WHERE session_id = $2
                AND jsonb_array_length(messages) > $3
            """, -max_count, session_id, max_count)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
```

---

### src/agent/memory/checkpointer.py

**Purpose:** Adapt PostgresMemoryStore to LangGraph checkpointer interface

**Guidelines:**

1. Define `create_checkpointer()` function

2. Function signature:
   - Parameters: `store: PostgresMemoryStore`, `session_id: str`
   - Returns: LangGraph checkpointer instance

3. The checkpointer should:
   - Use session_id as thread_id
   - Load messages from store on get
   - Save messages to store on put
   - Handle message trimming automatically

4. Use LangGraph's `MemorySaver` as base if custom implementation not needed

5. If custom implementation needed, implement:
   - `aget(thread_id)` - load conversation
   - `aput(thread_id, checkpoint)` - save conversation

**Pseudocode:**
```
def create_checkpointer(
    store: PostgresMemoryStore,
    session_id: str,
    max_messages: int = 20
) -> BaseCheckpointSaver:

    class PostgresCheckpointer(BaseCheckpointSaver):
        def __init__(self, store, session_id, max_messages):
            self._store = store
            self._session_id = session_id
            self._max_messages = max_messages

        async def aget(self, thread_id: str) -> Checkpoint:
            messages = await self._store.get_conversation(thread_id)
            return Checkpoint(messages=messages)

        async def aput(self, thread_id: str, checkpoint: Checkpoint) -> None:
            for message in checkpoint.messages:
                await self._store.save_message(thread_id, message)
            await self._store.trim_messages(thread_id, self._max_messages)

    return PostgresCheckpointer(store, session_id, max_messages)
```

---

## Database Schema

### conversations table

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key, auto-generated |
| session_id | UUID | Unique, indexed - conversation identifier |
| messages | JSONB | Array of message objects |
| created_at | TIMESTAMP | Session creation time |
| updated_at | TIMESTAMP | Last message time |

### Message Object (JSONB element)

```json
{
  "role": "user|assistant|tool",
  "content": "string",
  "tool_calls": null | [...],
  "tool_call_id": null | "string",
  "timestamp": 1234567890
}
```

---

## Dependencies

- `asyncpg` - PostgreSQL async driver
- `langgraph.checkpoint` - Checkpointer base classes
- `src.config.settings` - Configuration

---

## Integration Notes

1. Store should be initialized at application startup (lifespan)
2. Connection pool is shared across requests
3. Session_id validation should happen at API layer
4. Message trimming happens automatically after save
5. No TTL/cleanup - sessions persist indefinitely
