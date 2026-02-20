# Observability Implementation

## Overview

Create manager classes for Langfuse client, prompts, and datasets, replacing module-level functions and globals.

## Files to Create

- `src/observability/manager.py` - LangfuseManager class (NEW)

## Files to Modify

- `src/observability/client.py` - Remove globals, keep helper functions
- `src/observability/prompts.py` - Convert to PromptManager class
- `src/observability/datasets.py` - Convert to DatasetManager class
- `src/observability/__init__.py` - Export classes

## Implementation Guidelines

### LangfuseManager Class

```python
class LangfuseManager:
    def __init__(
        self,
        settings: Settings,
        http_client: httpx.AsyncClient | None = None,
    ):
        self._settings = settings
        self._http_client = http_client
        self._client: Langfuse | None = None
        self._initialized = False
        self._prompt_synced = False

    @classmethod
    def from_settings(cls, settings: Settings) -> "LangfuseManager":
        return cls(settings=settings)

    @property
    def is_enabled(self) -> bool:
        return self._initialized and self._client is not None

    @property
    def is_prompt_synced(self) -> bool:
        return self._prompt_synced

    @property
    def client(self) -> Langfuse | None:
        return self._client if self._initialized else None

    async def initialize(self) -> Langfuse | None:
        if not self._settings.langfuse_enabled:
            return None

        for attempt in range(1, _MAX_INIT_RETRIES + 1):
            try:
                is_authenticated = await self._check_auth()
                if not is_authenticated:
                    return None

                self._configure_client()
                self._initialized = True
                return self._client
            except Exception:
                is_last_attempt = attempt >= _MAX_INIT_RETRIES
                if not is_last_attempt:
                    await asyncio.sleep(_INIT_RETRY_DELAY_SECONDS)

        return None

    async def _check_auth(self) -> bool:
        url = f"{self._settings.langfuse_host}/api/public/projects"
        http_client = self._http_client or httpx.AsyncClient(timeout=10.0)

        async with http_client as client:
            response = await client.get(
                url,
                auth=(self._settings.langfuse_public_key, self._settings.langfuse_secret_key),
            )
        return response.status_code == 200

    def _configure_client(self) -> None:
        self._set_environment_variables()
        self._client = Langfuse(
            public_key=self._settings.langfuse_public_key,
            secret_key=self._settings.langfuse_secret_key,
            host=self._settings.langfuse_host,
        )

    def _set_environment_variables(self) -> None:
        if self._settings.langfuse_public_key:
            os.environ["LANGFUSE_PUBLIC_KEY"] = self._settings.langfuse_public_key
        if self._settings.langfuse_secret_key:
            os.environ["LANGFUSE_SECRET_KEY"] = self._settings.langfuse_secret_key
        if self._settings.langfuse_host:
            os.environ["LANGFUSE_HOST"] = self._settings.langfuse_host

    def mark_prompt_synced(self) -> None:
        self._prompt_synced = True

    def get_handler(
        self,
        session_id: str,
        langfuse_prompt: Any = None,
    ) -> CallbackHandler | None:
        if not self.is_enabled:
            return None
        return get_langfuse_handler(
            enabled=True,
            session_id=session_id,
            langfuse_prompt=langfuse_prompt,
        )

    def flush(self) -> None:
        if self._client:
            self._client.flush()
```

### PromptManager Class

```python
class PromptManager:
    def __init__(
        self,
        settings: Settings,
        langfuse_manager: LangfuseManager | None = None,
    ):
        self._settings = settings
        self._langfuse_manager = langfuse_manager

    @classmethod
    def from_settings(
        cls,
        settings: Settings,
        langfuse_manager: LangfuseManager | None = None,
    ) -> "PromptManager":
        return cls(settings=settings, langfuse_manager=langfuse_manager)

    @property
    def langfuse_available(self) -> bool:
        return self._langfuse_manager is not None and self._langfuse_manager.is_enabled

    async def sync_to_langfuse(self) -> None:
        if not self.langfuse_available:
            return
        # ... sync logic

    def get_compiled_system_prompt(
        self,
        langfuse_prompt: Any = None,
    ) -> tuple[str, dict]:
        # ... compilation logic

    def get_langchain_template(self) -> ChatPromptTemplate:
        # ... template creation

    @staticmethod
    def format_current_date() -> str:
        now = datetime.now()
        return now.strftime("%A, %B %d, %Y at %I:%M %p")

    @staticmethod
    def extract_system_content(prompt: Any) -> str:
        # Pure function - no self access
        pass
```

### DatasetManager Class

```python
class DatasetManager:
    DATASET_USER_OPENING_MESSAGES = "USER_OPENING_MESSAGES"
    DATASET_STOCK_QUERIES = "STOCK_QUERIES"

    def __init__(self, langfuse_manager: LangfuseManager | None = None):
        self._langfuse_manager = langfuse_manager

    @classmethod
    def from_langfuse_manager(cls, langfuse_manager: LangfuseManager) -> "DatasetManager":
        return cls(langfuse_manager=langfuse_manager)

    @property
    def is_available(self) -> bool:
        return self._langfuse_manager is not None and self._langfuse_manager.is_enabled

    @property
    def client(self) -> Langfuse | None:
        if self._langfuse_manager is None:
            return None
        return self._langfuse_manager.client

    def add_opening_message(
        self,
        user_message: str,
        session_id: str,
        expected_tools: list[str],
    ) -> None:
        if not self.is_available:
            return

        self.client.trace(
            name="user_opening_message",
            session_id=session_id,
            input={"message": user_message, "expected_tools": expected_tools},
        ).update()

    def add_stock_query(
        self,
        ticker: str,
        user_message: str,
        session_id: str,
    ) -> None:
        if not self.is_available:
            return

        self.client.trace(
            name="stock_query",
            session_id=session_id,
            input={"ticker": ticker, "user_message": user_message},
        ).update()

    @staticmethod
    def build_trace_metadata(session_id: str, tool_name: str) -> dict[str, str]:
        return {
            "session_id": session_id,
            "tool": tool_name,
            "timestamp": datetime.now().isoformat(),
        }
```

## OOP Patterns Applied

| Pattern | Usage |
|---------|-------|
| `@property` | `is_enabled` - boolean check for client availability |
| `@property` | `is_prompt_synced` - boolean state check |
| `@property` | `client` - lazy access to Langfuse client |
| `@property` | `langfuse_available` - computed availability check |
| `@property` | `is_available` - dataset manager availability |
| `@classmethod` | `from_settings()` - alternative constructor |
| `@classmethod` | `from_langfuse_manager()` - factory method |
| `@staticmethod` | `format_current_date()` - pure function |
| `@staticmethod` | `extract_system_content()` - pure function |
| `@staticmethod` | `build_trace_metadata()` - pure function |
| Helper methods | `_check_auth()`, `_configure_client()`, `_set_environment_variables()` |
| Named booleans | `is_last_attempt`, `is_authenticated` |

## Globals to Remove

From `src/observability/client.py`:
- `_langfuse_initialized`
- `_langfuse_prompt_synced`

## Backward Compatibility

Keep wrapper functions that delegate to manager:

```python
async def initialize_langfuse_client() -> Langfuse | None:
    manager = LangfuseManager.from_settings(settings)
    return await manager.initialize()

def get_langfuse_client() -> Langfuse | None:
    return manager.client  # manager from container

def is_langfuse_enabled() -> bool:
    return manager.is_enabled  # Using @property
```

## Integration Notes

- LangfuseManager holds all Langfuse state
- PromptManager and DatasetManager depend on LangfuseManager via constructor
- ServiceContainer creates and owns all manager instances
- Handler classes receive managers via constructor injection
- All boolean checks use `@property` for cleaner API
