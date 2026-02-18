# Bonus 1: RAG Pipeline

> Status: TODO
> Priority: BONUS (Strongly Valued)

## Overview

Implement a Retrieval-Augmented Generation pipeline with a knowledge base.

## Requirements

- Create 3-10 documents about Vera, fintech regulations, policies
- Generate embeddings
- Store in vector database (ChromaDB)
- Retrieve relevant documents
- Inject context into prompt
- Include citations in responses

## Tasks

| ID | Task | Status | Notes |
|----|------|--------|-------|
| B1.1 | Create knowledge documents | TODO | 3-10 markdown files |
| B1.2 | Generate embeddings | TODO | OpenAI embeddings |
| B1.3 | Set up vector database | TODO | ChromaDB |
| B1.4 | Store embeddings | TODO | Index documents |
| B1.5 | Implement retrieval logic | TODO | Similarity search |
| B1.6 | Inject context into prompt | TODO | Add to system prompt |
| B1.7 | Add citations to responses | TODO | Reference sources |

## Implementation Location

```
src/rag/
├── __init__.py
├── embeddings.py           # Embedding generation
├── retriever.py            # Vector store retrieval
├── citations.py            # Citation formatting
└── knowledge_base/         # Source documents
    ├── vera_overview.md
    ├── fintech_regulations.md
    ├── privacy_policy.md
    └── ...

docs/knowledge_base/        # Alternative location
├── vera_overview.md
├── fintech_regulations.md
└── ...
```

## LangChain Approach

**Reference:** `.claude/skills/langchain/reference/advanced/rag_agent.md`

### Embeddings

```python
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

embeddings = OpenAIEmbeddings(
    model=settings.openai_embedding_model
)

vectorstore = Chroma(
    embedding_function=embeddings,
    persist_directory="./chroma_db"
)
```

### Document Loading

```python
from langchain_community.document_loaders import DirectoryLoader, TextLoader

loader = DirectoryLoader(
    "./docs/knowledge_base",
    glob="**/*.md",
    loader_cls=TextLoader
)
documents = loader.load()
```

### Retrieval

```python
from langchain.retrievers import ContextualCompressionRetriever

retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}
)
```

### RAG Agent

```python
from langchain.agents import create_agent

rag_agent = create_agent(
    model,
    tools=[...],
    system_prompt="""You are a helpful assistant with access to a knowledge base.
    When answering questions, use the retrieved context.
    Always cite your sources using [Source: filename] format."""
)
```

## Knowledge Base Documents

Create documents about:

1. **Vera Overview** - Company history, mission, services
2. **Fintech Regulations** - Compliance requirements, KYC, AML
3. **Privacy Policy** - Data handling, user rights
4. **Security Practices** - Encryption, authentication
5. **Terms of Service** - User agreements, limitations
6. **API Documentation** - Endpoints, rate limits
7. **FAQ** - Common questions and answers

## Citation Format

```json
{
  "response": "Vera was founded in 2020...",
  "citations": [
    {"source": "vera_overview.md", "snippet": "Founded in 2020..."}
  ]
}
```

## Testing

```bash
# Index documents
python -m src.rag.embeddings --index

# Test retrieval
python -m src.rag.retriever --query "What is Vera?"

# Integration test
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key" \
  -d '{"message": "Tell me about Vera privacy policy"}'
```

## Dependencies

```toml
chromadb>=1.5.0
langchain-chroma>=1.1.0
```
