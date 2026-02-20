# Chainlit Integration with VeraMoney Streaming API

> *"Why build a frontend when Chainlit already did it better than you would have anyway?"*
> — **El Barto**

## Executive Summary

Chainlit provides a production-ready chat UI that can connect to your existing FastAPI streaming endpoint (`/chat`) via Server-Sent Events (SSE). The integration requires minimal code changes and leverages your current `langchain.agents.create_agent` implementation with streaming support. Two primary integration patterns exist: **direct LangChain integration** (Chainlit runs the agent) and **proxy integration** (Chainlit connects to your FastAPI backend).

---

## Current Architecture Analysis

### Your Streaming API (`src/api/endpoints/chat_stream.py`)

Your existing `/chat` endpoint emits SSE events with the following structure:

| Event | Payload | Description |
|-------|---------|-------------|
| `token` | `{"content": "..."}` | AI response chunks |
| `tool_call` | `{"tool": "...", "args": {...}}` | Tool invocation with arguments |
| `tool_result` | `{"tool": "...", "result": "..."}` | Tool execution result |
| `done` | `{}` | Stream completion |
| `error` | `{"message": "..."}` | Error occurred |

### Agent Configuration (`src/agent/core/conversational_agent.py`)

Your agent uses:
- `langchain.agents.create_agent` (correct v1 API)
- `ChatOpenAI` with configurable model
- Tools: `get_weather`, `get_stock_price`
- Middleware stack: logging, error handling, guardrails
- Memory: `MemoryStore` with checkpointer

---

## Integration Patterns

### Pattern A: Direct LangChain Integration (Recommended)

Chainlit runs the agent directly, importing your existing tools and configuration. This provides the richest UI experience with automatic tool visualization via `cl.LangchainCallbackHandler()`.

**Architecture:**
```
[Chainlit UI] --> [Chainlit App] --> [Your Agent] --> [Tools/LLM]
                      |
                      v
              [cl.LangchainCallbackHandler]
                      |
                      v
              [Automatic Tool Visualization]
```

**Implementation:**

```python
# File: src/chainlit_app/app.py

import chainlit as cl
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage

from src.agent import create_conversational_agent, get_memory_store
from src.config import settings


@cl.on_chat_start
async def on_chat_start():
    memory_store = await get_memory_store(settings)
    agent, config_template = await create_conversational_agent(
        settings=settings,
        memory_store=memory_store,
        session_id=cl.context.session.thread_id,
    )
    cl.user_session.set("agent", agent)
    cl.user_session.set("config_template", config_template)
    await cl.Message(content="Hello! I'm Vera, your financial assistant. Ask me about weather or stock prices.").send()


@cl.on_message
async def on_message(message: cl.Message):
    agent = cl.user_session.get("agent")
    config_template = cl.user_session.get("config_template")

    config = {
        **config_template,
        "configurable": {
            **config_template["configurable"],
            "thread_id": cl.context.session.thread_id,
        },
        "callbacks": [cl.LangchainCallbackHandler()],
    }

    msg = cl.Message(content="")
    await msg.send()

    async for stream_mode, data in agent.astream(
        {"messages": [HumanMessage(content=message.content)]},
        config=config,
        stream_mode=["messages"],
    ):
        if stream_mode == "messages":
            token, _metadata = data
            if hasattr(token, "content") and token.content:
                await msg.stream_token(token.content)

    await msg.update()
```

**Pros:**
- Automatic tool call visualization in UI
- Full access to agent middleware stack
- Direct session management with LangGraph checkpointer

**Cons:**
- Requires API keys in Chainlit process
- Bypasses FastAPI rate limiting and authentication

---

### Pattern B: Proxy Integration (Connect to FastAPI Backend)

Chainlit acts as a pure frontend, forwarding all requests to your existing FastAPI `/chat` endpoint via SSE streaming.

**Architecture:**
```
[Chainlit UI] --> [Chainlit App] --httpx--> [FastAPI /chat] --> [Agent] --> [Tools/LLM]
                      |                              |
                      v                              v
              [SSE Parsing]                  [Rate Limiting]
                      |                              |
                      v                              v
              [msg.stream_token()]          [API Key Auth]
```

**Implementation:**

```python
# File: src/chainlit_app/app.py

import json
import uuid
import httpx
import chainlit as cl

BACKEND_URL = "http://localhost:8000"
API_KEY = "your-api-key"  # From environment


@cl.on_chat_start
async def on_chat_start():
    session_id = str(uuid.uuid4())
    cl.user_session.set("session_id", session_id)
    await cl.Message(content="Connected to VeraMoney Assistant! Ask about weather or stock prices.").send()


@cl.on_message
async def on_message(message: cl.Message):
    session_id = cl.user_session.get("session_id")

    msg = cl.Message(content="")
    await msg.send()

    current_tool_step = None

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            f"{BACKEND_URL}/chat",
            json={
                "message": message.content,
                "session_id": session_id,
            },
            headers={
                "Content-Type": "application/json",
                "X-API-Key": API_KEY,
                "Accept": "text/event-stream",
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.strip():
                    continue

                if line.startswith("event:"):
                    event_type = line[6:].strip()
                    continue

                if line.startswith("data:"):
                    payload = line[5:].strip()
                    if not payload:
                        continue

                    try:
                        data = json.loads(payload)
                    except json.JSONDecodeError:
                        continue

                    if event_type == "token":
                        content = data.get("content", "")
                        if content:
                            await msg.stream_token(content)

                    elif event_type == "tool_call":
                        tool_name = data.get("tool", "unknown")
                        tool_args = data.get("args", {})
                        current_tool_step = cl.Step(name=tool_name, type="tool")
                        current_tool_step.input = tool_args
                        await current_tool_step.__aenter__()

                    elif event_type == "tool_result":
                        tool_result = data.get("result", "")
                        if current_tool_step:
                            current_tool_step.output = tool_result
                            await current_tool_step.__aexit__(None, None, None)
                            current_tool_step = None

                    elif event_type == "error":
                        error_msg = data.get("message", "Unknown error")
                        await msg.stream_token(f"\n\n[Error: {error_msg}]")

                    elif event_type == "done":
                        break

    await msg.update()
```

**Pros:**
- Preserves FastAPI authentication and rate limiting
- Clean separation of concerns
- Can run Chainlit on different host/port

**Cons:**
- No native LangChain callback integration
- Manual SSE parsing required
- Additional network hop adds latency

---

### Pattern C: Mount Chainlit on FastAPI (Single Server)

Mount Chainlit as a sub-application on your existing FastAPI server using `mount_chainlit()`.

**Implementation:**

```python
# File: src/api/app.py (modified)

from chainlit.utils import mount_chainlit

# ... existing app creation code ...

app = create_app()

# Mount Chainlit at /chat-ui path
mount_chainlit(app=app, target="src/chainlit_app/app.py", path="/chat-ui")
```

**Run:**
```bash
# Single server serves both API and Chainlit UI
uvicorn src.api.app:app --host 0.0.0.0 --port 8000

# Access API at /chat
# Access Chainlit UI at /chat-ui
```

---

## Configuration

### Chainlit Config File (`src/chainlit_app/.chainlit/config.toml`)

```toml
[project]
enable_telemetry = false
user_env = []
session_timeout = 3600
user_session_timeout = 1296000
cache = false
allow_origins = ["*"]

[features]
unsafe_allow_html = false
latex = false
user_message_autoscroll = true
auto_tag_thread = true
edit_message = true

[features.spontaneous_file_upload]
enabled = false

[UI]
name = "VeraMoney Assistant"
layout = "wide"
cot = "full"

[meta]
generated_by = "2.4.1"
```

### Dependencies (`pyproject.toml`)

```toml
[project.optional-dependencies]
chainlit = [
    "chainlit>=2.4.0",
]
```

Install:
```bash
uv add chainlit
```

---

## Session Management Patterns

### Thread Resumption with `@cl.on_chat_resume`

For Pattern A (Direct Integration), implement chat resume to restore conversation history:

```python
from chainlit.types import ThreadDict
from langchain_core.messages import HumanMessage, AIMessage


@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    memory_store = await get_memory_store(settings)

    messages = []
    for step in thread["steps"]:
        if step["type"] == "user_message":
            messages.append(HumanMessage(content=step["output"]))
        elif step["type"] == "assistant_message":
            messages.append(AIMessage(content=step["output"]))

    session_id = thread["id"]
    agent, config_template = await create_conversational_agent(
        settings=settings,
        memory_store=memory_store,
        session_id=session_id,
    )

    cl.user_session.set("agent", agent)
    cl.user_session.set("config_template", config_template)
```

### Chat Profiles for Multi-Mode Selection

```python
@cl.set_chat_profiles
async def chat_profiles():
    return [
        cl.ChatProfile(
            name="default",
            markdown_description="Full assistant with weather and stock tools",
            icon="/public/assistant.png",
            default=True,
        ),
        cl.ChatProfile(
            name="weather-only",
            markdown_description="Weather-focused assistant",
            icon="/public/weather.png",
        ),
        cl.ChatProfile(
            name="stocks-only",
            markdown_description="Stock price assistant",
            icon="/public/stocks.png",
        ),
    ]


@cl.on_chat_start
async def on_chat_start():
    profile = cl.user_session.get("chat_profile")

    if profile == "weather-only":
        tools = [get_weather]
    elif profile == "stocks-only":
        tools = [get_stock_price]
    else:
        tools = [get_weather, get_stock_price]

    # ... rest of agent setup
```

---

## Tool Visualization

### Automatic via `cl.LangchainCallbackHandler()`

When using Pattern A, the callback handler automatically visualizes tool calls:

```python
config = {
    "callbacks": [
        cl.LangchainCallbackHandler(
            to_ignore=["ChannelRead", "RunnableLambda", "ChannelWrite"],
        )
    ]
}
```

### Manual via `@cl.step(type="tool")`

For Pattern B or custom visualization:

```python
@cl.step(type="tool")
async def execute_tool(tool_name: str, tool_args: dict) -> str:
    current_step = cl.context.current_step
    current_step.name = tool_name
    current_step.input = tool_args
    current_step.language = "json"

    result = await call_tool_via_api(tool_name, tool_args)

    current_step.output = result
    return result
```

---

## Streaming Patterns from Local Examples

### Pattern 1: Token Streaming with `stream_token()`

From `examples/openai-functions-streaming/app.py`:

```python
async def stream_response(message_history):
    final_answer = cl.Message(content="", author="Answer")

    stream = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=message_history,
        stream=True,
    )

    async for part in stream:
        if content := part.choices[0].delta.content:
            if not final_answer.content:
                await final_answer.send()
            await final_answer.stream_token(content)

    if final_answer.content:
        await final_answer.update()
```

### Pattern 2: LangGraph with `stream_mode="messages"`

From `examples/langgraph-memory/app.py`:

```python
@cl.on_message
async def main(message: cl.Message):
    answer = cl.Message(content="")
    await answer.send()

    config = {"configurable": {"thread_id": cl.context.session.thread_id}}

    for msg, _ in app.stream(
        {"messages": [HumanMessage(content=message.content)]},
        config,
        stream_mode="messages",
    ):
        if isinstance(msg, AIMessageChunk):
            answer.content += msg.content
            await answer.update()
```

### Pattern 3: Dual Callback Handler (RAG + Streaming)

From `examples/chroma-qa-chat/app.py`:

```python
class SourceTrackerHandler(BaseCallbackHandler):
    def __init__(self, msg: cl.Message):
        self.msg = msg
        self.sources = set()

    def on_retriever_end(self, documents, *, run_id, parent_run_id, **kwargs):
        for doc in documents:
            source = doc.metadata.get("source", "unknown")
            self.sources.add(source)

    def on_llm_end(self, response, *, run_id, parent_run_id, **kwargs):
        if self.sources:
            sources_text = "\n".join(self.sources)
            self.msg.elements.append(
                cl.Text(name="Sources", content=sources_text, display="inline")
            )


async for chunk in runnable.astream(
    message.content,
    config=RunnableConfig(
        callbacks=[cl.LangchainCallbackHandler(), SourceTrackerHandler(msg)]
    ),
):
    await msg.stream_token(chunk)
```

---

## Running Chainlit

### Development

```bash
# Run Chainlit directly (Pattern A)
chainlit run src/chainlit_app/app.py -w

# Run with custom host/port
chainlit run src/chainlit_app/app.py --host 0.0.0.0 --port 8080

# Run with FastAPI mount (Pattern C)
uvicorn src.api.app:app --reload
```

### Docker

```dockerfile
# Add to existing Dockerfile
RUN pip install chainlit

# Or create separate Chainlit service in docker-compose.yml
services:
  chainlit:
    build: .
    command: chainlit run src/chainlit_app/app.py --host 0.0.0.0 --port 8001
    ports:
      - "8001:8001"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
```

---

## Comparison Matrix

| Feature | Pattern A (Direct) | Pattern B (Proxy) | Pattern C (Mount) |
|---------|-------------------|-------------------|-------------------|
| Tool Visualization | Automatic | Manual | Automatic |
| Auth/Rate Limiting | None | Full | Partial |
| Latency | Lowest | Higher | Lowest |
| Deployment | Separate process | Separate process | Single server |
| Code Complexity | Low | Medium | Low |
| Recommended For | Development/POC | Production | Simple deployment |

---

## Key Findings

1. **Your API is SSE-ready**: The `/chat` endpoint already emits properly formatted SSE events that Chainlit can consume with minimal parsing.

2. **Pattern A is fastest to implement**: Import your existing `create_conversational_agent` directly into Chainlit app.

3. **`cl.LangchainCallbackHandler()` is the key**: This single callback provides automatic tool visualization without manual step management.

4. **Thread ID mapping**: Use `cl.context.session.thread_id` as the session identifier to map Chainlit threads to your LangGraph checkpointer.

5. **Middleware preserved**: Your existing middleware stack (logging, error handling, guardrails) works unchanged in Pattern A.

6. **Concurrent streaming supported**: For multi-agent scenarios, use `asyncio.gather()` with separate `cl.Message` instances per agent.

---

## Recommendations

1. **Start with Pattern A** for development and testing - it provides the richest UX with minimal code.

2. **Add Pattern B** for production if you need API key authentication and rate limiting enforcement at the edge.

3. **Use Pattern C** if deployment simplicity is paramount and you want a single server process.

4. **Implement `@cl.on_chat_resume`** to enable conversation continuity across browser sessions.

5. **Configure `allow_origins`** in Chainlit config to match your production domain.

---

## Next Steps

1. Install Chainlit: `uv add chainlit`
2. Create `src/chainlit_app/app.py` using Pattern A
3. Run: `chainlit run src/chainlit_app/app.py -w`
4. Test with weather and stock queries
5. Add chat profiles if needed
6. Configure production settings in `.chainlit/config.toml`

---
*Report generated by: El Barto*
*Date: 2026-02-19*
