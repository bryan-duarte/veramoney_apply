# Knowledge Tool Implementation

## Overview

LangChain tool wrapper for the RAG pipeline, following the existing three-layer tool pattern (client, schemas, tool). Exposes `search_knowledge` as an agent-callable tool.

## Files to Create

- `src/tools/knowledge/schemas.py` - Input/output Pydantic models
- `src/tools/knowledge/client.py` - KnowledgeRetrieverClient wrapping the RAG retriever
- `src/tools/knowledge/tool.py` - @tool decorated async function
- `src/tools/knowledge/__init__.py` - Exports

## Implementation Guidelines

### schemas.py
- Constants: QUERY_MIN_LENGTH = 1, QUERY_MAX_LENGTH = 1000
- `DocumentTypeFilter` StrEnum: VERA_HISTORY, FINTEC_REGULATION, BANK_REGULATION (mirrors RAG schema)
- `KnowledgeInput(BaseModel)`:
  - query: str (min_length=QUERY_MIN_LENGTH, max_length=QUERY_MAX_LENGTH)
  - document_type: str | None = None (optional filter)
- `RetrievedChunkOutput(BaseModel)`:
  - content: str
  - document_title: str
  - document_type: str
  - page_number: int
  - relevance_score: float
- `KnowledgeOutput(BaseModel)`:
  - query: str
  - chunks: list[RetrievedChunkOutput]
  - total_results: int

### client.py
- Module-level variable for singleton: `_retriever_instance: KnowledgeRetriever | None`
- Function `configure_knowledge_client(retriever: KnowledgeRetriever) -> None` - sets the singleton
- Function `get_knowledge_client() -> KnowledgeRetriever` - returns singleton, raises if not configured
- This follows the pattern of weather/stock clients but wraps the RAG retriever instead of an external API

### tool.py
- `@tool(args_schema=KnowledgeInput)` decorator
- `async def search_knowledge(query: str, document_type: str | None = None) -> str`
- Docstring describes the tool for the agent (what it searches, when to use it)
- Gets client via `get_knowledge_client()`
- Calls retriever.search() with query, document_type, k from settings
- Returns JSON string with KnowledgeOutput data
- Error handling: returns JSON error string on failure (same pattern as weather/stock)
- Guard clause for client not configured

### __init__.py
- Export: search_knowledge, KnowledgeInput, KnowledgeOutput, configure_knowledge_client

## Files to Modify

- `src/tools/__init__.py` - Add search_knowledge to exports and __all__

## Dependencies

- src/rag (KnowledgeRetriever)
- src/config (settings for retrieval_k)

## Integration Notes

- `configure_knowledge_client()` is called during app lifespan after RAG pipeline initialization
- Tool is registered in `create_conversational_agent()` tools list
- Returns JSON strings (consistent with weather and stock tools)
- The tool's docstring is critical - it guides the agent on when to use it
