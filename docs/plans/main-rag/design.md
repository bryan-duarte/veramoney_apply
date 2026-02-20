# Technical Design

## Architecture Decisions

### RAG Pattern: Agentic RAG
The agent decides when to use the knowledge retrieval tool based on user intent. This is not a fixed 2-step retrieve-then-generate pipeline. The agent autonomously calls `search_knowledge` when it determines the query requires knowledge base information.

### Document Source: Remote PDFs (R2 CDN)
PDFs are not stored in the repository. They are downloaded from controlled R2 CDN URLs at startup. This keeps the repo lightweight and allows document updates without code changes.

### Three Fixed Documents with Known Metadata

| Key | URL | Document Type | Language |
|-----|-----|---------------|----------|
| `vera_history` | `https://pub-739843c5b2e64a7881e1fa442a3d9075.r2.dev/veramoney-history.pdf` | `vera_history` | es |
| `fintec_regulation` | `https://pub-739843c5b2e64a7881e1fa442a3d9075.r2.dev/Regulacio%CC%81n%20fintec.pdf` | `fintec_regulation` | es |
| `bank_regulation` | `https://pub-739843c5b2e64a7881e1fa442a3d9075.r2.dev/Regulacio%CC%81n%20Bancaria%20Uruguaya_%20Investigacio%CC%81n%20Profunda.pdf` | `bank_regulation` | es |

Since URLs are controlled, metadata is hardcoded per document (no filename-based classification needed).

### Processing: PDFPlumberLoader
Chosen specifically for table extraction capabilities. Financial regulations contain tables that standard PyPDF loaders destroy.

### Single Collection with Metadata Filtering
One ChromaDB collection `veramoney_knowledge` with metadata fields:
- `document_type`: vera_history | fintec_regulation | bank_regulation
- `source_url`: Original PDF URL
- `document_title`: Human-readable title
- `language`: "es"
- `page_number`: Original page in PDF
- `chunk_index`: Position within document

## Patterns & Conventions

### Follow Existing Tool Pattern (Three Layers)
```
src/tools/knowledge/
├── client.py    -> KnowledgeRetriever (wraps ChromaDB retrieval)
├── schemas.py   -> KnowledgeInput, KnowledgeOutput, RetrievedChunk
└── tool.py      -> @tool search_knowledge()
```

### Follow Existing Client Pattern
- Async httpx for PDF download
- Tenacity retry with exponential backoff for downloads
- Named constants for all configuration values
- Custom exceptions (DocumentDownloadError, IndexingError)
- Guard clauses, named booleans, no comments

### Follow Existing Middleware Pattern
- `@after_model` decorator for citation verification guardrail
- Non-blocking: logs warnings but doesn't reject responses
- Extracts tool results from ToolMessage objects (same as output_guardrails.py)

## Dependencies

### New
- `pdfplumber` (via `langchain-community` PDFPlumberLoader, may need explicit install)

### Existing (already in pyproject.toml)
- `chromadb>=1.5.0`
- `langchain-chroma>=1.1.0`
- `langchain-openai>=1.1.10` (OpenAIEmbeddings)
- `langchain-community>=0.4.1` (PDFPlumberLoader)
- `httpx>=0.25.0` (PDF download)
- `tenacity>=8.0.0` (retry logic)

## Integration Points

### 1. Agent Creation (src/agent/core/conversational_agent.py)
- Import and add `search_knowledge` to the tools list
- Tool registered alongside `get_weather` and `get_stock_price`

### 2. System Prompt (src/agent/core/prompts.py)
- Add `search_knowledge` tool capability disclosure
- Add citation requirement instructions
- Add guidance on when to use knowledge tool vs general knowledge

### 3. Middleware (src/agent/middleware/)
- New file: `knowledge_guardrails.py` with citation verification
- Update `tool_error_handler.py`: add `"search_knowledge": "knowledge base"` to service mapping
- Add to middleware stack in agent creation

### 4. Settings (src/config/settings.py)
- Add ChromaDB connection settings (`chroma_host`, `chroma_port`)
- Add RAG configuration (`rag_collection_name`, `rag_retrieval_k`)

### 5. App Lifespan (src/api/app.py)
- Initialize RAG pipeline in lifespan startup
- Check-and-load documents into ChromaDB
- Cleanup on shutdown

### 6. Chainlit Handlers (src/chainlit/handlers.py)
- Add `TOOL_KNOWLEDGE` constant
- Add context extraction for knowledge tool results

### 7. Tools __init__.py (src/tools/__init__.py)
- Export `search_knowledge`

## Data Structures

### KnowledgeInput (Pydantic)
- `query`: str (the search query)
- `document_type`: str | None (optional filter: vera_history, fintec_regulation, bank_regulation)

### KnowledgeOutput (Pydantic)
- `chunks`: list[RetrievedChunk]
- `query`: str

### RetrievedChunk (Pydantic)
- `content`: str
- `document_type`: str
- `document_title`: str
- `page_number`: int
- `relevance_score`: float

### DocumentConfig (Pydantic)
- `key`: str
- `url`: str
- `document_type`: str
- `title`: str
- `language`: str
- `chunk_size`: int
- `chunk_overlap`: int

### Metadata per Chunk (dict for ChromaDB)
- `document_type`: str
- `source_url`: str
- `document_title`: str
- `language`: str
- `page_number`: int
- `chunk_index`: int
