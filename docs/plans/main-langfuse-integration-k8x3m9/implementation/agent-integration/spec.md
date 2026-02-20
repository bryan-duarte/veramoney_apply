# Agent Integration Implementation

## Overview

Integrate Langfuse CallbackHandler and chat-type prompts into the agent creation flow.

## Files to Modify

| File | Changes |
|------|---------|
| `src/agent/core/conversational_agent.py` | Add CallbackHandler, use compiled prompt |
| `src/agent/core/prompts.py` | Add variable placeholders to VERA_FALLBACK_SYSTEM_PROMPT |

---

## File: prompts.py

### Add Variable Placeholders

Modify the VERA_FALLBACK_SYSTEM_PROMPT to include variable placeholders:

**Add temporal context at the beginning:**

```
<temporal_context>
Today's date: {{current_date}}

Note: Stock prices and weather data are retrieved in real-time via tools, so the information I provide is always current.
</temporal_context>
```

**Modify identity section:**

```
<identity>
You are Vera AI v{{version}}, a specialized financial assistant...
Built on: {{model_name}}
...
</identity>
```

### Full Variable List

| Placeholder | Location | Value Source |
|-------------|----------|--------------|
| `{{current_date}}` | `<temporal_context>` | `datetime.now().strftime("%d %B, %y")` |
| `{{version}}` | `<identity>` | Constant "1.0" |
| `{{model_name}}` | `<identity>` | `settings.agent_model` |

### Remove Hardcoded Temporal Context

**Current:**
```
<temporal_context>
Note: Stock prices and weather data are retrieved in real-time via tools...
</temporal_context>
```

**New:**
```
<temporal_context>
Today's date: {{current_date}}

Note: Stock prices and weather data are retrieved in real-time via tools, so the information I provide is always current.
</temporal_context>
```

---

## File: conversational_agent.py

### Current State

Agent is created with:

```
agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=VERA_FALLBACK_SYSTEM_PROMPT,
    middleware=middleware_stack,
    checkpointer=checkpointer,
)
```

### Changes Required

#### 1. Import Langfuse and LangChain Components

```
from src.observability import (
    get_langfuse_client,
    get_langfuse_handler,
    get_compiled_prompt,
    format_current_date,
)
from langchain_core.prompts import ChatPromptTemplate
```

#### 2. Get Langfuse Client and Handler

```
langfuse_client = get_langfuse_client()
langfuse_handler = get_langfuse_handler(
    client=langfuse_client,
    session_id=session_id,
    trace_name="veramoney-chat"
)
```

#### 3. Get Compiled Prompt Template

```
current_date = format_current_date()
prompt_template, prompt_metadata = get_compiled_prompt(
    client=langfuse_client,
    fallback_system=VERA_FALLBACK_SYSTEM_PROMPT,
    current_date=current_date,
    model_name=settings.agent_model,
    version="1.0",
    user_message=...,  # Will be set at invocation
    chat_history=None  # Will be set at invocation
)
```

#### 4. Build Config with Callbacks and Metadata

```
config = {
    "configurable": {
        "thread_id": session_id,
    },
    "callbacks": [langfuse_handler] if langfuse_handler else [],
    "metadata": prompt_metadata,  # Links prompt version to trace
}
```

#### 5. Create Agent with Template

For LangChain `create_agent()`, pass the compiled prompt:

```
agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=prompt_template,  # ChatPromptTemplate with variables
    middleware=middleware_stack,
    checkpointer=checkpointer,
)
```

### Key Considerations

- CallbackHandler goes in `config["callbacks"]`
- Prompt metadata goes in `config["metadata"]` for trace linking
- Handler is None if Langfuse not configured (graceful degradation)
- Template is always valid (fallback if Langfuse fails)

---

## Integration Flow

```
chat_complete.py / chat_stream.py
       │
       ├── get_memory_store()
       │
       ├── create_conversational_agent()
       │       │
       │       ├── get_langfuse_client()
       │       │
       │       ├── format_current_date()
       │       │       │
       │       │       └── datetime.now().strftime("%d %B, %y")
       │       │
       │       ├── get_compiled_prompt(
       │       │     client,
       │       │     fallback=VERA_FALLBACK_SYSTEM_PROMPT,
       │       │     current_date,
       │       │     model_name,
       │       │     version
       │       │   )
       │       │       │
       │       │       ├── Try Langfuse fetch
       │       │       ├── Compile with variables
       │       │       └── Return (ChatPromptTemplate, metadata)
       │       │
       │       ├── get_langfuse_handler(client, session_id)
       │       │
       │       ├── create_agent(
       │       │     model,
       │       │     tools,
       │       │     system_prompt=compiled_template,
       │       │     middleware,
       │       │     checkpointer
       │       │   )
       │       │
       │       └── Build config with callbacks + metadata
       │
       ├── agent.ainvoke(
       │     {"messages": [user_message]},
       │     config=config
       │   )
       │       │
       │       └── CallbackHandler auto-traces to Langfuse
       │           with prompt version in metadata
       │
       └── Return response
```

---

## Prompt Variable Injection

### At Request Time

Each request injects the current date:

```
# In create_conversational_agent()
current_date = format_current_date()  # "20 February, 26"

# The prompt template has {{current_date}} placeholder
# LangChain will substitute when rendering
```

### Result in System Prompt

```
<temporal_context>
Today's date: 20 February, 26

Note: Stock prices and weather data are retrieved in real-time via tools...
</temporal_context>
```

### Why This Matters

- Agent knows the current date for context
- No confusion about "today" vs training data
- Stock/weather data can be contextualized
- User queries about dates are accurate

---

## Trace Linking

### Metadata Structure

```
config["metadata"] = {
    "langfuse_prompt": prompt_object,  # Langfuse prompt reference
    "prompt_version": 3,               # Version number
    "prompt_name": "vera-system-prompt"
}
```

### Benefits

- See which prompt version was used per trace
- Compare performance across prompt versions
- Rollback analysis in Langfuse UI
- A/B test different prompt variants

---

## No Changes Required

The following files do NOT need modification:

- `src/agent/middleware/*.py` - Middleware remains unchanged
- `src/agent/memory/store.py` - Memory store remains unchanged

CallbackHandler is additive and does not interfere with existing middleware.

---

## Fallback Behavior

### When Langfuse Unavailable

```
get_compiled_prompt(client=None, ...)
    └── Creates ChatPromptTemplate from VERA_FALLBACK_SYSTEM_PROMPT
    └── No date injection (uses hardcoded prompt)
    └── Returns (template, {"prompt_source": "fallback"})
```

### User Impact

- Agent still works
- Prompt is the hardcoded version
- No dynamic date (agent won't know today's date)
- Log warning about Langfuse unavailability
