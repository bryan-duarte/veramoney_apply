# Implementation Tasks

## Task Breakdown

### Observability Module (src/observability/)

- [x] Create `src/observability/__init__.py` with public API exports
- [x] Create `src/observability/client.py` - Langfuse client singleton with graceful degradation
- [x] Create `src/observability/handler.py` - CallbackHandler factory
- [x] Create `src/observability/datasets.py` - Dataset management service
- [x] Create `src/observability/prompts.py` - Prompt sync service with:
  - [x] `format_current_date()` function
  - [x] `sync_prompt_to_langfuse()` for chat-type prompts
  - [x] `get_compiled_system_prompt()` with variable injection
  - [x] `get_langchain_prompt()` for ChatPromptTemplate
  - [x] Fallback template creation

### Configuration (src/config/)

- [x] Add Langfuse-specific settings to `src/config/settings.py`
  - Add `langfuse_enabled` computed field
  - Add `langfuse_environment` computed field
  - Add validation for key presence

### Prompt Template (src/agent/core/)

- [x] Modify `src/agent/core/prompts.py`
  - [x] Add `{{current_date}}` variable to `<temporal_context>`
  - [x] Add `{{version}}` variable to `<identity>`
  - [x] Add `{{model_name}}` variable to `<identity>`
  - [x] Update temporal_context section with date placeholder

### Agent Integration (src/agent/)

- [x] Modify `src/agent/core/conversational_agent.py`
  - Import Langfuse observability functions
  - Add `format_current_date()` call
  - Get compiled prompt with variables
  - Integrate CallbackHandler in config
  - Add prompt metadata for trace linking

### API Integration (src/api/)

- [x] Modify `src/api/app.py` lifespan
  - Initialize Langfuse client at startup
  - Sync chat-type prompt to Langfuse
  - Add flush on shutdown

- [x] Modify `src/api/endpoints/chat_complete.py`
  - Get/create trace with session_id
  - Collect opening messages for dataset
  - Collect stock queries for dataset
  - Set trace metadata and tags

- [x] Modify `src/api/endpoints/chat_stream.py`
  - Get/create trace with session_id
  - Collect opening messages for dataset
  - Collect stock queries for dataset
  - Set trace metadata and tags

### Testing & Validation

- [ ] Manual testing: Verify prompt created as `type="chat"` in Langfuse UI
- [ ] Manual testing: Verify variables compile (date, model, version)
- [ ] Manual testing: Verify date shows as "DD Month, YY" format
- [ ] Manual testing: Verify traces appear in Langfuse UI
- [ ] Manual testing: Verify datasets receive items
- [ ] Manual testing: Verify graceful degradation when keys missing
- [ ] Manual testing: Verify trace metadata includes prompt version

---

## Task Dependencies

```
observability/client.py
    └── observability/handler.py (depends on client)
    └── observability/datasets.py (depends on client)
    └── observability/prompts.py (depends on client)

config/settings.py (no dependencies)

agent/core/prompts.py (add variables)
    └── observability/prompts.py (uses VERA_FALLBACK_SYSTEM_PROMPT as fallback)
    └── agent/core/conversational_agent.py (uses prompts)

api/app.py
    └── observability/client.py
    └── observability/prompts.py

api/endpoints/chat_*.py
    └── observability/handler.py
    └── observability/datasets.py
    └── agent/core/conversational_agent.py
```

---

## Implementation Order

1. **Phase 1: Foundation** (observability module)
   - client.py
   - handler.py
   - __init__.py exports

2. **Phase 2: Configuration** (settings)
   - Add computed fields to settings.py

3. **Phase 3: Prompt Variables** (prompts.py)
   - Add {{current_date}}, {{version}}, {{model_name}} to VERA_FALLBACK_SYSTEM_PROMPT

4. **Phase 4: Dataset & Prompts Service** (observability)
   - datasets.py
   - prompts.py (with chat-type support and variables)

5. **Phase 5: Agent Integration**
   - Modify conversational_agent.py (use compiled prompts)

6. **Phase 6: API Integration**
   - Modify app.py (lifespan)
   - Modify chat_complete.py
   - Modify chat_stream.py

7. **Phase 7: Validation**
   - Manual testing all features

---

## Key Improvements Added

| Improvement | Description |
|------------|-------------|
| Chat-type prompts | Use `type="chat"` instead of `type="text"` |
| Dynamic date | `{{current_date}}` injected per request |
| Model versioning | `{{model_name}}` and `{{version}}` variables |
| Chat history placeholder | `MessagesPlaceholder` for conversation memory |
| LangChain integration | `get_langchain_prompt()` method |
| Trace linking | Prompt metadata in traces for version tracking |
| Proper fallback | Fallback template when Langfuse unavailable |

---

## Variable Injection Summary

| Variable | Placeholder | Source | Format |
|----------|-------------|--------|--------|
| Current date | `{{current_date}}` | `datetime.now()` | "20 February, 26" |
| Model name | `{{model_name}}` | `settings.agent_model` | "GPT-5-mini" |
| Version | `{{version}}` | Constant | "1.0" |
| User message | `{{user_message}}` | Request | User input |
| Chat history | `chat_history` | Checkpointer | List of messages |
