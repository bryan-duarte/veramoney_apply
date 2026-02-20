# Implementation Tasks

## Task Breakdown

### 1. RAG Pipeline (src/rag/)

- [x] Create `src/rag/schemas.py` - Pydantic models for DocumentConfig, chunk metadata, and RAG configuration
- [x] Create `src/rag/document_configs.py` - Hardcoded configuration for the 3 PDF documents (URLs, types, chunk sizes)
- [x] Create `src/rag/loader.py` - Async PDF downloader + PDFPlumberLoader processor. Downloads from R2 URLs, extracts pages with tables
- [x] Create `src/rag/splitter.py` - Document-type-specific RecursiveCharacterTextSplitter. Applies correct chunk_size/overlap per document type
- [x] Create `src/rag/vectorstore.py` - ChromaDB client manager. Creates/connects to collection, handles check-and-load logic, batch embedding insertion
- [x] Create `src/rag/retriever.py` - Async similarity search with optional metadata filtering by document_type. Returns top-k results with scores
- [x] Create `src/rag/__init__.py` - Export public API (initialize_rag_pipeline, KnowledgeRetriever)

### 2. Knowledge Tool (src/tools/knowledge/)

- [x] Create `src/tools/knowledge/schemas.py` - KnowledgeInput and KnowledgeOutput Pydantic models
- [x] Create `src/tools/knowledge/client.py` - KnowledgeRetriever class wrapping src/rag/retriever
- [x] Create `src/tools/knowledge/tool.py` - @tool decorated async `search_knowledge` function
- [x] Create `src/tools/knowledge/__init__.py` - Export search_knowledge and schemas

### 3. Agent Integration

- [x] Update `src/tools/__init__.py` - Add search_knowledge export
- [x] Update `src/agent/core/conversational_agent.py` - Register search_knowledge in tools list
- [x] Update `src/agent/core/prompts.py` - Add knowledge tool capability, citation instructions, usage guidance
- [x] Update `src/agent/middleware/tool_error_handler.py` - Add search_knowledge to TOOL_SERVICE_NAMES mapping
- [x] Create `src/agent/middleware/knowledge_guardrails.py` - Citation verification middleware (@after_model)
- [x] Update agent middleware stack to include knowledge_guardrails

### 4. Startup & Configuration

- [x] Update `src/config/settings.py` - Add chroma_host, chroma_port, rag_collection_name, rag_retrieval_k fields
- [x] Update `src/api/app.py` lifespan - Initialize RAG pipeline (check-and-load) on startup, cleanup on shutdown
- [x] Update `src/chainlit/handlers.py` - Add TOOL_KNOWLEDGE constant and context extraction

### 5. Dependencies

- [x] Update `pyproject.toml` - Add pdfplumber dependency (installed via uv add)
