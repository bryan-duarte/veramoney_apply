# Implementation Tasks

## Task Breakdown

### Phase 1: DI Container Foundation

- [x] Create `src/di/__init__.py` module
- [x] Create `ServiceContainer` class with settings injection
- [x] Add `initialize()` async method for service setup
- [x] Add `shutdown()` async method for cleanup
- [x] Add lazy getter methods for each service
- [x] Integrate ServiceContainer into FastAPI lifespan
- [x] Add `get_container` dependency for endpoints

### Phase 2: Observability Layer Classes

- [x] Create `LangfuseManager` class in `src/observability/manager.py`
  - Migrate functions: initialize_langfuse_client, get_langfuse_client, is_langfuse_enabled
  - Add sync_prompt, is_prompt_synced, mark_prompt_synced methods
- [x] Create `PromptManager` class in `src/observability/prompts.py`
  - Migrate: sync_prompt_to_langfuse, get_compiled_system_prompt, get_langchain_prompt
  - Keep format_current_date as utility
- [x] Create `DatasetManager` class in `src/observability/datasets.py`
  - Migrate: add_opening_message_to_dataset, add_stock_query_to_dataset
- [x] Update `src/observability/__init__.py` with class exports
- [x] Update ServiceContainer to instantiate LangfuseManager

### Phase 3: RAG Pipeline Class

- [x] Create `RAGPipeline` class in `src/rag/pipeline.py`
  - `__init__` with settings and optional dependencies
  - `initialize()` - connects to ChromaDB, checks existing data
  - `_load_documents_if_needed()` - downloads and indexes documents
  - `get_retriever()` - returns KnowledgeRetriever
  - `get_status()` - returns RAGPipelineStatus
- [x] Create `DocumentLoader` class in `src/rag/loader.py`
  - Migrate: download_pdf_to_temp_file, load_pdf_with_plumber
  - Migrate: enrich_document_metadata, download_and_load_document
- [x] Keep `DocumentSplitter` as function module (split_documents)
- [x] Update `src/rag/__init__.py` with class exports
- [x] Update ServiceContainer to instantiate RAGPipeline

### Phase 4: API Handler Classes

- [x] Create `ChatHandlerBase` class in `src/api/handlers/base.py`
  - `__init__` with container injection
  - `get_memory_store()` - lazy memory store access
  - `get_langfuse_client()` - lazy langfuse access
  - `is_opening_message(session_id)` - check if first message
  - `_infer_expected_tools(message)` - detect tool intent
  - `_collect_stock_queries(...)` - dataset collection
- [x] Create `ChatCompleteHandler` in `src/api/handlers/chat_complete.py`
  - Inherit from ChatHandlerBase
  - `handle(request)` - main handler method
  - `_extract_tool_calls(messages)` - extract tool call info
- [x] Create `ChatStreamHandler` in `src/api/handlers/chat_stream.py`
  - Inherit from ChatHandlerBase
  - `handle(request)` - returns AsyncGenerator
  - `_generate_stream(...)` - SSE generation
- [x] Create `HealthHandler` in `src/api/handlers/health.py`
  - `handle()` - returns health response
- [x] Update endpoint files to use handlers
- [x] Update `src/api/__init__.py` with handler exports

### Phase 5: Agent Factory Class

- [x] Create `AgentFactory` class in `src/agent/core/factory.py`
  - `__init__` with settings, memory_store, langfuse_manager injection
  - `create_agent(session_id)` - returns agent, config, handler
  - `_build_middleware_stack()` - creates middleware list
  - `_compile_system_prompt()` - gets compiled prompt
- [x] Keep middleware as decorator functions (no changes)
- [x] Update `src/agent/__init__.py` with AgentFactory export

### Phase 6: Chainlit Handler Classes

- [x] Create `ChainlitHandlers` class in `src/chainlit/handlers.py`
  - `__init__` with settings injection
  - `on_chat_start()` - chat start handler
  - `on_message()` - message handler
  - `set_starters()` - starter prompts
- [x] Keep `SSEClient` class as-is (already OOP)
- [x] Update `src/chainlit/app.py` to use ChainlitHandlers

### Phase 7: Cleanup & Migration

- [x] Remove global singleton variables from:
  - `src/agent/memory/store.py` (_memory_store_instance, get_memory_store)
  - `src/observability/client.py` (globals noted for future removal)
  - `src/tools/knowledge/client.py` (kept - needed for @tool decorator pattern)
- [x] Update all imports to use new class-based API
- [x] Verify all endpoints work with new handler classes
- [x] Verify agent creation works with AgentFactory
- [x] Verify RAG pipeline works with RAGPipeline class
- [x] All imports verified via uv run

## Migration Order

1. **DI Container** (no dependencies) - Foundation for everything else
2. **Observability** (depends on: DI Container) - LangfuseManager, PromptManager, DatasetManager
3. **RAG Pipeline** (depends on: DI Container, Observability) - RAGPipeline, DocumentLoader
4. **Agent Factory** (depends on: DI Container, Observability, RAG) - AgentFactory
5. **API Handlers** (depends on: All above) - ChatHandlerBase, endpoint handlers
6. **Chainlit** (depends on: All above) - ChainlitHandlers
7. **Cleanup** - Remove globals, update imports

## Files to Create

| File | Purpose |
|------|---------|
| `src/di/__init__.py` | DI module exports |
| `src/di/container.py` | ServiceContainer class |
| `src/observability/manager.py` | LangfuseManager class |
| `src/rag/pipeline.py` | RAGPipeline class (rename) |
| `src/rag/loader.py` | DocumentLoader class (rename) |
| `src/agent/core/factory.py` | AgentFactory class |
| `src/api/handlers/__init__.py` | Handler exports |
| `src/api/handlers/base.py` | ChatHandlerBase class |
| `src/api/handlers/chat_complete.py` | ChatCompleteHandler |
| `src/api/handlers/chat_stream.py` | ChatStreamHandler |
| `src/api/handlers/health.py` | HealthHandler |

## Files to Modify

| File | Changes |
|------|---------|
| `src/api/app.py` | Use ServiceContainer in lifespan |
| `src/api/endpoints/chat_complete.py` | Use ChatCompleteHandler |
| `src/api/endpoints/chat_stream.py` | Use ChatStreamHandler |
| `src/api/endpoints/health.py` | Use HealthHandler |
| `src/agent/memory/store.py` | Remove singleton, keep class |
| `src/observability/client.py` | Remove globals, keep helper functions |
| `src/observability/prompts.py` | Convert to PromptManager |
| `src/observability/datasets.py` | Convert to DatasetManager |
| `src/rag/pipeline.py` | Convert to RAGPipeline class |
| `src/rag/loader.py` | Convert to DocumentLoader class |
| `src/agent/core/conversational_agent.py` | Convert to AgentFactory |
| `src/chainlit/handlers.py` | Convert to ChainlitHandlers class |
| `src/tools/knowledge/client.py` | Remove globals, functions become helpers |

## Files Unchanged

| File | Reason |
|------|--------|
| `src/tools/weather/client.py` | Already a class |
| `src/tools/weather/tool.py` | Keep @tool decorator |
| `src/tools/stock/client.py` | Already a class |
| `src/tools/stock/tool.py` | Keep @tool decorator |
| `src/tools/knowledge/tool.py` | Keep @tool decorator |
| `src/agent/middleware/*.py` | Keep decorator functions |
| `src/config/*.py` | Already classes/enums |
| `src/rag/vectorstore.py` | Already a class |
| `src/rag/retriever.py` | Already a class |
| `src/chainlit/sse_client.py` | Already a class |
