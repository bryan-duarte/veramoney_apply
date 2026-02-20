# Agent Factory Implementation

## Overview

The AgentFactory encapsulates agent creation logic, replacing the `create_conversational_agent()` function with a class that supports dependency injection.

## Files to Create

- `src/agent/core/factory.py` - AgentFactory class (NEW)

## Files to Modify

- `src/agent/__init__.py` - Export AgentFactory
- `src/agent/core/__init__.py` - Export AgentFactory

## Implementation Guidelines

### AgentFactory Class

```python
class AgentFactory:
    def __init__(
        self,
        settings: Settings,
        memory_store: MemoryStore | None = None,
        langfuse_manager: LangfuseManager | None = None,
        prompt_manager: PromptManager | None = None,
    ):
        self._settings = settings
        self._memory_store = memory_store
        self._langfuse_manager = langfuse_manager
        self._prompt_manager = prompt_manager

    @classmethod
    def from_settings(cls, settings: Settings) -> "AgentFactory":
        return cls(settings=settings)

    @classmethod
    def with_dependencies(
        cls,
        settings: Settings,
        memory_store: MemoryStore,
        langfuse_manager: LangfuseManager,
        prompt_manager: PromptManager,
    ) -> "AgentFactory":
        return cls(
            settings=settings,
            memory_store=memory_store,
            langfuse_manager=langfuse_manager,
            prompt_manager=prompt_manager,
        )

    @property
    def has_memory_store(self) -> bool:
        return self._memory_store is not None

    @property
    def has_langfuse(self) -> bool:
        return self._langfuse_manager is not None and self._langfuse_manager.is_enabled

    async def create_agent(
        self,
        session_id: str,
    ) -> tuple[Any, dict, CallbackHandler | None]:
        memory_store = await self._get_memory_store()
        langfuse_handler = self._get_langfuse_handler(session_id)
        compiled_prompt, prompt_metadata = self._get_compiled_prompt()

        model = self._create_model()
        tools = self._build_tools()
        middleware = self._build_middleware_stack()
        checkpointer = memory_store.get_checkpointer()

        agent = create_agent(
            model=model,
            tools=tools,
            system_prompt=compiled_prompt,
            middleware=middleware,
            checkpointer=checkpointer,
        )

        config = self._build_config(session_id, langfuse_handler)
        return agent, config, langfuse_handler

    async def _get_memory_store(self) -> MemoryStore:
        if self._memory_store is None:
            self._memory_store = MemoryStore.from_settings(self._settings)
            await self._memory_store.initialize()
        return self._memory_store

    def _get_langfuse_handler(self, session_id: str) -> CallbackHandler | None:
        if not self.has_langfuse:
            return None

        langfuse_prompt = self._get_langfuse_prompt()
        return self._langfuse_manager.get_handler(
            session_id=session_id,
            langfuse_prompt=langfuse_prompt,
        )

    def _get_langfuse_prompt(self) -> Any:
        if self._prompt_manager is None:
            return None
        return self._prompt_manager.get_langfuse_prompt()

    def _get_compiled_prompt(self) -> tuple[str, dict]:
        if self._prompt_manager is None:
            self._prompt_manager = PromptManager.from_settings(
                settings=self._settings,
                langfuse_manager=self._langfuse_manager,
            )
        return self._prompt_manager.get_compiled_system_prompt()

    def _create_model(self) -> ChatOpenAI:
        return ChatOpenAI(
            model=self._settings.agent_model,
            timeout=self._settings.agent_timeout_seconds,
            api_key=self._settings.openai_api_key,
        )

    @staticmethod
    def _build_tools() -> list:
        return [get_weather, get_stock_price, search_knowledge]

    @staticmethod
    def _build_middleware_stack() -> list:
        return [
            logging_middleware,
            tool_error_handler,
            output_guardrails,
            knowledge_guardrails,
        ]

    @staticmethod
    def _build_config(session_id: str, handler: CallbackHandler | None) -> dict:
        callbacks = [handler] if handler else []
        return {
            "configurable": {"thread_id": session_id},
            "callbacks": callbacks,
        }
```

### Migration from create_conversational_agent

Current function signature:
```python
async def create_conversational_agent(
    settings: Settings,
    memory_store: MemoryStore,
    session_id: str,
) -> tuple[Any, dict, CallbackHandler | None]:
```

New class method signature:
```python
factory = AgentFactory.from_settings(settings)
agent, config, handler = await factory.create_agent(session_id)

# Or with dependencies:
factory = AgentFactory.with_dependencies(
    settings=settings,
    memory_store=memory_store,
    langfuse_manager=langfuse_manager,
    prompt_manager=prompt_manager,
)
agent, config, handler = await factory.create_agent(session_id)
```

## OOP Patterns Applied

| Pattern | Usage |
|---------|-------|
| `@classmethod` | `from_settings()` - factory from settings |
| `@classmethod` | `with_dependencies()` - factory with all deps |
| `@property` | `has_memory_store` - boolean check |
| `@property` | `has_langfuse` - boolean availability check |
| `@staticmethod` | `_build_tools()` - pure function returning tool list |
| `@staticmethod` | `_build_middleware_stack()` - pure function |
| `@staticmethod` | `_build_config()` - pure function of inputs |
| Helper methods | `_get_memory_store()`, `_create_model()`, `_get_langfuse_handler()` |
| Named booleans | `has_langfuse`, `has_memory_store` |
| Constructor injection | All dependencies injectable via `__init__` |

## Dependencies

- Settings (required)
- MemoryStore (optional, defaults to creating new)
- LangfuseManager (optional, defaults to None)
- PromptManager (optional, defaults to creating new)

## Integration Notes

- Keep all middleware decorator functions unchanged
- Agent creation logic stays identical
- Only the wrapper changes from function to class
- Static methods for pure functions improve testability
- Backward compatibility via factory function wrapper if needed
