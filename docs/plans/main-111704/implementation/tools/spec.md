# Tools Implementation

## Overview

Keep current tool structure unchanged. Tools already use a class-based client pattern with @tool decorator functions.

## Files Unchanged

- `src/tools/weather/client.py` - WeatherAPIClient class (keep)
- `src/tools/weather/schemas.py` - Pydantic models (keep)
- `src/tools/weather/tool.py` - @tool decorated function (keep)
- `src/tools/stock/client.py` - FinnhubClient class (keep)
- `src/tools/stock/schemas.py` - Pydantic models (keep)
- `src/tools/stock/tool.py` - @tool decorated function (keep)
- `src/tools/knowledge/schemas.py` - Pydantic models (keep)
- `src/tools/knowledge/tool.py` - @tool decorated function (keep)

## Files to Modify

- `src/tools/knowledge/client.py` - Remove globals, convert to helper functions

## Implementation Guidelines

### Knowledge Client Refactoring

Current pattern (with globals):
```python
_knowledge_retriever_instance: KnowledgeRetriever | None = None

def configure_knowledge_client(retriever: KnowledgeRetriever) -> None:
    global _knowledge_retriever_instance
    _knowledge_retriever_instance = retriever

def get_knowledge_client() -> KnowledgeRetriever:
    if _knowledge_retriever_instance is None:
        raise RuntimeError(...)
    return _knowledge_retriever_instance
```

New pattern (retriever passed to tool):
```python
# In knowledge/tool.py
async def search_knowledge(
    query: str,
    document_type: str | None = None,
) -> str:
    retriever = _get_retriever_from_context()
    if retriever is None:
        return KnowledgeError(error="Knowledge base unavailable").model_dump_json()
    # ... rest unchanged
```

The retriever is now provided via:
1. ServiceContainer holds RAGPipeline
2. RAGPipeline has get_retriever() method
3. Tool accesses retriever through container context

### Alternative: Retriever as Tool Parameter

Keep tool function signature but pass retriever via LangChain context:

```python
@tool(args_schema=KnowledgeInput)
async def search_knowledge(query: str, document_type: str | None = None) -> str:
    retriever = get_retriever_from_config()
    # ... use retriever
```

## Dependencies

- KnowledgeRetriever (from RAGPipeline)
- Settings (for error handling)

## Integration Notes

- WeatherAPIClient and FinnhubClient remain unchanged
- @tool decorator functions remain unchanged
- Only knowledge client globals are removed
- Retriever access changes from global to context-based
