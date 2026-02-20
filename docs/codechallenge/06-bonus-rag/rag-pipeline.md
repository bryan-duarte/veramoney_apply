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

## System Prompt Recommendations

### Option A: In-Memory Session Management (Simple)

```python
sessions: dict[str, list[Message]] = {}

def get_session_history(session_id: str) -> list[Message]:
    return sessions.get(session_id, [])

def add_to_session(session_id: str, message: Message):
    if session_id not in sessions:
        sessions[session_id] = []
    sessions[session_id].append(message)
```

### Option B: Redis Session Management (Production)

```python
import redis.asyncio as redis

redis_client = redis.from_url(settings.redis_url)

async def get_session_history(session_id: str) -> list[Message]:
    data = await redis_client.get(f"session:{session_id}")
    return json.loads(data) if data else []

async def add_to_session(session_id: str, message: Message):
    history = await get_session_history(session_id)
    history.append(message)
    await redis_client.setex(
        f"session:{session_id}",
        3600,
        json.dumps(history)
    )
```

### Option C: Simplified Dependencies

If LangFuse won't be used, simplify the stack:

```yaml
app:
  depends_on:
    chromadb:
      condition: service_healthy
    postgres-memory:
      condition: service_healthy
```

*Created by Bryan, the new team member of the Vera Team ;)*

### Option E: Conversation Awareness

Add conversation guidelines to the system prompt:

```
<conversation_guidelines>
- Remember context from earlier in the conversation
- Reference previous queries when relevant
- If user asks "what about the other one?", refer to previously discussed items
- Proactively connect related information from the conversation history
</conversation_guidelines>
```

## Dependencies

```toml
chromadb>=1.5.0
langchain-chroma>=1.1.0
```
