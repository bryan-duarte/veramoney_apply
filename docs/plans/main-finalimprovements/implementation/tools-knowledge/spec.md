# Tools - Knowledge Implementation

## Overview

Fix return type annotation (L2) for create_knowledge_tool function.

## Files to Modify

- `src/tools/knowledge/tool.py` - Fix return type

## Implementation Guidelines

### Fix Return Type Annotation (L2)

**Location**: `src/tools/knowledge/tool.py`

**Current** (incorrect):
```python
def create_knowledge_tool(retriever: KnowledgeRetriever | None) -> tool:
```

**Fix**:
```python
from langchain_core.tools import BaseTool

def create_knowledge_tool(retriever: KnowledgeRetriever | None) -> BaseTool:
```

### Full Function Signature

```python
from langchain.tools import tool
from langchain_core.tools import BaseTool

from src.rag.retriever import KnowledgeRetriever
from src.tools.knowledge.schemas import KnowledgeInput

def create_knowledge_tool(retriever: KnowledgeRetriever | None) -> BaseTool:
    @tool(args_schema=KnowledgeInput)
    async def search_knowledge(query: str, document_type: str | None = None) -> str:
        """Search the VeraMoney knowledge base..."""
        ...

    return search_knowledge
```

## Dependencies

- `langchain_core.tools.BaseTool` (already installed)

## Integration Notes

- The `@tool` decorator returns a `BaseTool` instance
- The previous annotation `tool` was referring to the decorator, not a type
- This fix improves type checking and IDE support
