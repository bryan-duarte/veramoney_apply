# LangFuse Implementation Guide for VeraMoney Apply

> *"Observability is not just about seeing what happened - it's about understanding why it happened."*
> — **El Barto**

## Executive Summary

This report synthesizes LangFuse implementation patterns from the `clickbait` project to guide integration in VeraMoney Apply. The clickbait project demonstrates a production-grade observability implementation with hierarchical tracing, LangChain integration, and structured metrics collection.

---

## 1. Configuration and Setup

### 1.1 Required Dependencies

```toml
# pyproject.toml
"langfuse>=3.0.0,<4",
```

### 1.2 Environment Variables

```bash
# .env.example
# Langfuse Observability Configuration
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
LANGFUSE_BASE_URL=https://cloud.langfuse.com
LANGFUSE_TRACING_ENVIRONMENT=production
LANGFUSE_RELEASE=v1.0.0
LANGFUSE_DEBUG=false
LANGFUSE_SAMPLE_RATE=1.0

# Optional tracing control
ENABLE_NEWS_ENRICH_TRACE=true
NEWS_ENRICH_TRACE_SAMPLE_RATE=100
SCRAPED_CONTENT_SAMPLE_RATE=5
```

### 1.3 Settings Configuration

```python
# src/config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Langfuse Observability Configuration
    LANGFUSE_PUBLIC_KEY: str = os.getenv("LANGFUSE_PUBLIC_KEY")
    LANGFUSE_SECRET_KEY: str = os.getenv("LANGFUSE_SECRET_KEY")
    LANGFUSE_BASE_URL: str = os.getenv(
        "LANGFUSE_BASE_URL",
        "https://cloud.langfuse.com",
    )
    LANGFUSE_TRACING_ENVIRONMENT: str = os.getenv(
        "LANGFUSE_TRACING_ENVIRONMENT",
        APP_ENV,
    )
    LANGFUSE_RELEASE: str = os.getenv("LANGFUSE_RELEASE", "v1.0.0")
    LANGFUSE_DEBUG: bool = str_to_bool(os.getenv("LANGFUSE_DEBUG", "false"))
    LANGFUSE_SAMPLE_RATE: float = float(os.getenv("LANGFUSE_SAMPLE_RATE", "1.0"))
```

### 1.4 Docker Compose Setup

```yaml
# docker-compose.yml
services:
  app:
    environment:
      # Observability
      - LANGFUSE_PUBLIC_KEY
      - LANGFUSE_SECRET_KEY
      - LANGFUSE_BASE_URL
      - LANGFUSE_TRACING_ENVIRONMENT
      - LANGFUSE_RELEASE
      - LANGFUSE_DEBUG
      - LANGFUSE_SAMPLE_RATE
```

---

## 2. Core Integration Patterns

### 2.1 LangChain Callback Handler Integration

The primary integration pattern uses LangFuse's `CallbackHandler` with LangChain:

```python
from langfuse import get_client, observe
from langfuse.langchain import CallbackHandler

@observe(name="conversational_agent_invoke")
async def process_user_message(
    message: str,
    session_id: str | None = None,
) -> dict:
    langfuse = get_client()
    langfuse.update_current_trace(
        name=f"chat-{session_id or 'anonymous'}",
        tags=["api", "chat", settings.APP_ENV],
        metadata={
            "session_id": session_id,
            "message_length": len(message),
        },
    )

    langfuse_handler = CallbackHandler()
    run_id = get_run_id_from_langfuse(langfuse)

    try:
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": message}]},
            config={"callbacks": [langfuse_handler]},
        )

        langfuse.update_current_trace(output={"status": "success"})
        return result
    finally:
        get_client().flush()
```

### 2.2 The `@observe` Decorator Pattern

Use `@observe` at every layer for hierarchical tracing:

```python
from langfuse import observe

# API Layer
@observe(name="api_chat_endpoint")
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    ...

# Agent Layer
@observe(name="conversational_agent")
async def run_agent(message: str, callbacks: list | None = None) -> AgentResponse:
    ...

# Tool Layer
@observe(name="weather_tool")
async def get_weather(location: str, callbacks: list | None = None) -> WeatherData:
    ...

# RAG Layer
@observe(name="rag_retrieval")
async def retrieve_context(query: str, callbacks: list | None = None) -> list[Document]:
    ...
```

### 2.3 Callback Propagation

Pass callbacks through the entire call stack:

```python
async def process_chat(
    message: str,
    callbacks: list[BaseCallbackHandler] | None = None,
) -> ChatResponse:
    # Agent invocation
    agent_response = await agent.arun(
        message=message,
        callbacks=callbacks,  # Propagates tracing
    )

    # Tool calls (if any)
    if agent_response.tool_calls:
        for tool_call in agent_response.tool_calls:
            tool_result = await execute_tool(
                tool_call,
                callbacks=callbacks,  # Propagates tracing
            )

    return ChatResponse(response=agent_response.content)
```

---

## 3. Trace Management

### 3.1 Run ID Helper

Create a helper for consistent trace ID extraction:

```python
# src/observability/langfuse_helpers.py
import logging
import uuid
from langfuse import Langfuse

def get_run_id_from_langfuse(langfuse: Langfuse) -> str:
    """Extract run ID from LangFuse trace or generate fallback UUID."""
    try:
        trace_id = langfuse.get_current_trace_id()
        if trace_id:
            return trace_id

        logging.warning("Could not get trace_id from LangFuse, using fallback UUID")
        return uuid.uuid4().hex

    except Exception as e:
        logging.warning(f"Error getting trace_id from LangFuse: {e}")
        return uuid.uuid4().hex
```

### 3.2 Trace Update Pattern

Update traces with meaningful context throughout execution:

```python
# Initialize trace
langfuse = get_client()
langfuse.update_current_trace(
    name=f"operation-{entity_id}",
    tags=["category", "subcategory", settings.APP_ENV],
    metadata={
        "entity_id": entity_id,
        "operation": "enrich",
        "user_input_length": len(user_input),
    },
)

# Update with output before return
langfuse.update_current_trace(
    output={
        "status": "success",
        "tokens_used": total_tokens,
        "duration_ms": elapsed_ms,
    }
)

# Always flush in finally block
finally:
    get_client().flush()
```

---

## 4. Structured Metrics Schemas

### 4.1 Base Metrics Schema

Define structured schemas for processing history:

```python
# src/observability/schemas.py
from typing import Literal
from pydantic import BaseModel, Field

class DetailedErrorSchema(BaseModel):
    """Structured error details for failed operations."""
    error_code: str = Field(..., description="Exception class name or error code")
    error_message: str = Field(..., description="Human-readable error message")
    error_stage: str | None = Field(None, description="Stage where error occurred")
    recoverable: bool | None = Field(None, description="Whether error is recoverable")

class BaseMetricsSchema(BaseModel):
    """Base schema for all processing history records."""
    entity_type: str = Field(..., description="Type of entity being processed")
    entity_id: int | str = Field(..., description="ID of the entity")
    status: Literal["success", "failure", "partial", "error"] = Field(
        ..., description="Operation status"
    )

    session_id: str | None = Field(None, description="Chat session ID")
    task_id: str | None = Field(None, description="Background task ID")
    run_id: str | None = Field(None, description="LangFuse run ID")
    langfuse_trace_id: str | None = Field(None, description="LangFuse trace ID")

    retry_count: int = Field(0, description="Number of retry attempts")
    duration_ms: int | None = Field(None, description="Execution time in milliseconds")

    error: DetailedErrorSchema | None = Field(
        None, description="Error details if status is failure"
    )

class ChatAttemptSchema(BaseMetricsSchema):
    """Schema for chat attempt records."""
    entity_type: str = Field(default="chat_message")
    message_length: int | None = None
    response_length: int | None = None
    tools_called: list[str] | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
```

---

## 5. Error Handling with Trace Context

### 5.1 Structured Error Capture

```python
from langfuse import get_client, observe

@observe(name="tool_execution")
async def execute_tool_safely(
    tool_name: str,
    tool_input: dict,
    callbacks: list | None = None,
) -> ToolResult:
    try:
        result = await tool_registry[tool_name].ainvoke(tool_input)
        return ToolResult(status="success", data=result)
    except ValidationError as e:
        error_schema = DetailedErrorSchema(
            error_code="ValidationError",
            error_message=str(e),
            error_stage="input_validation",
            recoverable=True,
        )
        return ToolResult(status="error", error=error_schema)
    except ExternalAPIError as e:
        error_schema = DetailedErrorSchema(
            error_code="ExternalAPIError",
            error_message=str(e),
            error_stage="api_call",
            recoverable=True,
        )
        return ToolResult(status="error", error=error_schema)
    except Exception as e:
        error_schema = DetailedErrorSchema(
            error_code=type(e).__name__,
            error_message=str(e),
            error_stage="unknown",
            recoverable=False,
        )
        return ToolResult(status="error", error=error_schema)
```

### 5.2 Error Stage Tracking

Define error stages for granular tracking:

```python
# src/observability/error_stages.py
from enum import Enum

class ErrorStage(str, Enum):
    INPUT_VALIDATION = "input_validation"
    TOOL_EXECUTION = "tool_execution"
    RAG_RETRIEVAL = "rag_retrieval"
    LLM_GENERATION = "llm_generation"
    RESPONSE_FORMATTING = "response_formatting"
    UNKNOWN = "unknown"
```

---

## 6. Token Usage Tracking

### 6.1 Extract from LangChain Messages

```python
def extract_tokens_from_messages(
    messages: list[BaseMessage],
) -> dict[str, int]:
    """Extract token usage from LangChain message metadata."""
    total_input_tokens = 0
    total_output_tokens = 0
    total_tokens = 0

    for message in messages:
        usage_metadata = getattr(message, "usage_metadata", None)
        if not usage_metadata:
            continue

        total_input_tokens += usage_metadata.get("input_tokens", 0)
        total_output_tokens += usage_metadata.get("output_tokens", 0)
        total_tokens += usage_metadata.get("total_tokens", 0)

    return {
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "total_tokens": total_tokens,
    }
```

### 6.2 Log Token Usage

```python
@observe(name="agent_response_generator")
async def generate_response(
    generation_config: GenerationConfig,
    callbacks: list | None = None,
) -> AgentResponse:
    start_time = time.monotonic()

    agent_response = await agent.ainvoke(
        {"messages": [HumanMessage(content=generation_config.user_prompt)]},
        config={"callbacks": callbacks},
    )

    elapsed_ms = int((time.monotonic() - start_time) * 1000)
    token_summary = extract_tokens_from_messages(
        agent_response.get("messages", [])
    )

    logging.info(
        f"Agent response generated | "
        f"Tokens: {token_summary['total_tokens']} "
        f"(in: {token_summary['input_tokens']}, out: {token_summary['output_tokens']}) | "
        f"Latency: {elapsed_ms}ms"
    )

    return AgentResponse(
        content=agent_response,
        input_tokens=token_summary["input_tokens"],
        output_tokens=token_summary["output_tokens"],
        total_tokens=token_summary["total_tokens"],
        latency_ms=elapsed_ms,
    )
```

---

## 7. Implementation for VeraMoney Apply

### 7.1 Conversational Agent Integration

```python
# src/agent/core/conversational_agent.py
from langfuse import get_client, observe
from langfuse.langchain import CallbackHandler

class ConversationalAgent:
    @observe(name="conversational_agent_invoke")
    async def invoke(
        self,
        message: str,
        session_id: str | None = None,
        callbacks: list[BaseCallbackHandler] | None = None,
    ) -> AgentResponse:
        langfuse = get_client()
        langfuse.update_current_trace(
            name=f"chat-{session_id or 'anonymous'}",
            tags=["agent", "chat", settings.APP_ENV],
            metadata={
                "session_id": session_id,
                "message_length": len(message),
            },
        )

        langfuse_handler = CallbackHandler()
        combined_callbacks = [langfuse_handler]
        if callbacks:
            combined_callbacks.extend(callbacks)

        try:
            response = await self._agent.ainvoke(
                {"messages": [HumanMessage(content=message)]},
                config={
                    "callbacks": combined_callbacks,
                    "configurable": {"session_id": session_id},
                },
            )

            token_summary = self._extract_tokens(response.get("messages", []))

            return AgentResponse(
                content=response["messages"][-1].content,
                tool_calls=self._extract_tool_calls(response),
                input_tokens=token_summary["input_tokens"],
                output_tokens=token_summary["output_tokens"],
                total_tokens=token_summary["total_tokens"],
            )

        finally:
            get_client().flush()
```

### 7.2 Tool Tracing

```python
# src/tools/weather/tool.py
from langfuse import observe

@observe(name="weather_tool")
async def get_weather(
    location: str,
    callbacks: list[BaseCallbackHandler] | None = None,
) -> WeatherData:
    """Get current weather for a location."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.WEATHER_API_URL}/current",
            params={"q": location, "key": settings.WEATHER_API_KEY},
        )
        response.raise_for_status()
        data = response.json()

    return WeatherData(
        location=location,
        temperature_celsius=data["current"]["temp_c"],
        condition=data["current"]["condition"]["text"],
        humidity=data["current"]["humidity"],
        wind_kph=data["current"]["wind_kph"],
    )
```

### 7.3 RAG Pipeline Tracing

```python
# src/rag/pipeline.py
from langfuse import observe

class RAGPipeline:
    @observe(name="rag_retrieval")
    async def retrieve(
        self,
        query: str,
        k: int = 5,
        callbacks: list[BaseCallbackHandler] | None = None,
    ) -> list[Document]:
        """Retrieve relevant documents for the query."""
        results = await self.retriever.aretrieve(query, k=k)
        return results

    @observe(name="rag_augment")
    async def augment(
        self,
        query: str,
        documents: list[Document],
        callbacks: list[BaseCallbackHandler] | None = None,
    ) -> str:
        """Build augmented context from retrieved documents."""
        context = self._build_context(documents)
        return self.prompt_template.format(query=query, context=context)

    @observe(name="rag_generate")
    async def generate(
        self,
        augmented_prompt: str,
        callbacks: list[BaseCallbackHandler] | None = None,
    ) -> str:
        """Generate response using the augmented prompt."""
        response = await self.llm.ainvoke(
            augmented_prompt,
            config={"callbacks": callbacks},
        )
        return response.content

    @observe(name="rag_pipeline")
    async def run(
        self,
        query: str,
        callbacks: list[BaseCallbackHandler] | None = None,
    ) -> RAGResponse:
        """Execute the full RAG pipeline."""
        documents = await self.retrieve(query, callbacks=callbacks)
        augmented = await self.augment(query, documents, callbacks=callbacks)
        response = await self.generate(augmented, callbacks=callbacks)

        return RAGResponse(
            answer=response,
            sources=[doc.metadata for doc in documents],
            query=query,
        )
```

### 7.4 API Endpoint Integration

```python
# src/api/endpoints/chat.py
from langfuse import get_client, observe
from langfuse.langchain import CallbackHandler

@router.post("/chat")
@observe(name="api_chat_endpoint")
async def chat(
    request: ChatRequest,
    agent: ConversationalAgent = Depends(get_agent),
) -> ChatResponse:
    langfuse = get_client()
    langfuse.update_current_trace(
        name=f"chat-{request.session_id or 'anonymous'}",
        tags=["api", "chat", settings.APP_ENV],
        metadata={
            "session_id": request.session_id,
            "message_length": len(request.message),
        },
    )

    langfuse_handler = CallbackHandler()

    try:
        agent_response = await agent.invoke(
            message=request.message,
            session_id=request.session_id,
            callbacks=[langfuse_handler],
        )

        langfuse.update_current_trace(
            output={
                "status": "success",
                "response_length": len(agent_response.content),
                "tool_calls": [tc.name for tc in agent_response.tool_calls],
                "total_tokens": agent_response.total_tokens,
            }
        )

        return ChatResponse(
            response=agent_response.content,
            tool_calls=[tc.dict() for tc in agent_response.tool_calls],
            session_id=request.session_id,
        )

    except Exception as e:
        langfuse.update_current_trace(
            output={
                "status": "error",
                "error": str(e),
            }
        )
        raise

    finally:
        get_client().flush()
```

---

## 8. Key Takeaways

### Architecture Benefits

1. **Hierarchical Tracing** - Multi-level `@observe` decorators create nested spans automatically
2. **Automatic LangChain Integration** - `CallbackHandler` captures LLM calls, token usage, and latency
3. **Manual Trace Control** - `update_current_trace()` for custom metadata at any point
4. **Correlation IDs** - Trace IDs used across database, logs, and monitoring
5. **Non-Intrusive** - Decorator-based approach requires minimal code changes

### Implementation Checklist

- [ ] Add `langfuse>=3.0.0,<4` to `pyproject.toml`
- [ ] Configure environment variables in `.env` and `docker-compose.yml`
- [ ] Create `src/observability/` module with helpers and schemas
- [ ] Add `@observe` decorators to agents, tools, and RAG components
- [ ] Implement callback propagation through all layers
- [ ] Add `finally: get_client().flush()` to all traced entry points
- [ ] Track token usage and latency in all LLM operations
- [ ] Create structured error schemas with stage tracking
- [ ] Test tracing in LangFuse dashboard

### Best Practices

1. **Always Flush** - Use `finally` blocks to ensure traces are sent
2. **Descriptive Names** - Use trace names like `operation-{entity_id}` for easy searching
3. **Consistent Tags** - Include environment, operation type, and category
4. **Metadata Structure** - Include entity IDs, configuration names, and performance metrics
5. **Error Context** - Capture error stage, code, and recoverability
6. **Token Tracking** - Log input/output tokens for cost monitoring
7. **Graceful Degradation** - Fallback to UUID if LangFuse trace ID unavailable

---

## 9. Reference Files from Clickbait Project

| File | Purpose |
|------|---------|
| `app/core/config.py` | LangFuse configuration variables |
| `app/tasks/task_helpers.py` | `get_run_id_from_langfuse()` helper |
| `app/tasks/scraped_news/process_scraped_news.py` | Task-level tracing pattern |
| `app/services/ai/agent/agent_response_generator.py` | Agent tracing with tokens |
| `app/services/ai/response/response_generator.py` | Response generator tracing |
| `app/services/metrics/schemas/base_schema.py` | Base metrics schema |
| `app/services/metrics/schemas/attempt_schemas.py` | Attempt-specific schemas |
| `app/services/grouped_news/services/enrichment_orchestrator.py` | Orchestrator tracing |

---

*Report generated by: El Barto*
*Date: 2026-02-19*
*Source: Clickbait project analysis*
