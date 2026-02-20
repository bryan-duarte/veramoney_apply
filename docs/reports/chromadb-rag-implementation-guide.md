# ChromaDB RAG Implementation Guide for Financial Knowledge Base

> *"A vector database without metadata is like a library without a catalog - all the books are there, but good luck finding the one on Uruguayan financial regulations."*
> — **El Barto**

## Executive Summary

This guide provides a complete blueprint for implementing a RAG (Retrieval-Augmented Generation) system using ChromaDB and LangChain v1 for the VeraMoney financial assistant. It covers PDF document loading, intelligent chunking strategies, metadata management for Uruguay-specific regulations, and integration as a tool for conversational agents. The implementation leverages your existing infrastructure: ChromaDB v1.5.0+ SDK, langchain-chroma v1.1.0+, and the Docker Chroma image.

---

## 1. Current Infrastructure Analysis

### 1.1 Version Inventory

| Component | Version | Source |
|-----------|---------|--------|
| **chromadb** | `>=1.5.0` | `pyproject.toml` |
| **langchain-chroma** | `>=1.1.0` | `pyproject.toml` |
| **langchain** | `>=1.2.10` | `pyproject.toml` |
| **langchain-openai** | `>=1.1.10` | `pyproject.toml` |
| **Docker Chroma Image** | `ghcr.io/chroma-core/chroma:latest` | `docker-compose.yml` |

### 1.2 Existing Configuration

Your Docker Compose already includes ChromaDB with:
- Host: `chromadb` (internal Docker network)
- Port: `8000` (internal), mapped to `8001` externally
- Volume: `chroma-data:/chroma/chroma`
- Telemetry: Connected to Langfuse via OpenTelemetry

```yaml
chromadb:
  image: ghcr.io/chroma-core/chroma:latest
  environment:
    - CHROMA_SERVER_HOST=0.0.0.0
    - CHROMA_SERVER_HTTP_PORT=8000
    - ALLOW_RESET=true
```

---

## 2. RAG Architecture Overview

### 2.1 Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RAG PIPELINE FLOW                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌───────────┐  │
│  │   PDF Files  │───>│  Document    │───>│    Text      │───>│ Embedding │  │
│  │  (Knowledge  │    │   Loaders    │    │  Splitters   │    │   Model   │  │
│  │    Base)     │    │              │    │              │    │           │  │
│  └──────────────┘    └──────────────┘    └──────────────┘    └─────┬─────┘  │
│                                                                   │         │
│                                                                   ▼         │
│                                                          ┌───────────────┐   │
│                                                          │   ChromaDB    │   │
│                                                          │  (Collections │   │
│                                                          │   + Metadata) │   │
│                                                          └───────┬───────┘   │
│                                                                  │           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │           │
│  │   User       │───>│   Retriever  │───>│   Context    │<──────┘           │
│  │   Query      │    │   (Similarity│    │   Assembly   │                    │
│  │              │    │    Search)   │    │              │                    │
│  └──────────────┘    └──────────────┘    └──────┬───────┘                    │
│                                                   │                           │
│                                                   ▼                           │
│                                          ┌───────────────┐                    │
│                                          │  LLM (OpenAI) │                    │
│                                          │  + Citations  │                    │
│                                          └───────────────┘                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 RAG Patterns Comparison

| Pattern | Use Case | Latency | Control | Recommendation |
|---------|----------|---------|---------|----------------|
| **Agentic RAG** | Multi-turn, complex queries | Variable | Low | General-purpose |
| **2-Step RAG** | Simple Q&A, predictable flow | Low | High | FAQ, simple retrieval |
| **Hybrid RAG** | Compliance-heavy domains | Medium | Medium | **Financial regulations** |

**Recommendation:** Use **Agentic RAG** for your VeraMoney assistant since it needs to handle complex multi-step queries about regulations, company history, and financial systems in Uruguay.

---

## 3. PDF Document Loading

### 3.1 PDF Loader Options for Financial Documents

| Loader | Strengths | Weaknesses | Best For |
|--------|-----------|------------|----------|
| **PyPDFLoader** | Fast, preserves structure | Weak table extraction | Simple text PDFs |
| **PDFPlumberLoader** | Good table extraction | Slower, more memory | **Financial reports** |
| **PyMuPDFLoader** | Best image support | Complex setup | Scanned documents |
| **UnstructuredPDFLoader** | Handles all formats | Heavy dependencies | Mixed content |

### 3.2 Implementation for Financial/Regulatory PDFs

```python
from langchain_community.document_loaders import PyPDFLoader, PDFPlumberLoader
from pathlib import Path
from typing import AsyncIterator

async def load_financial_pdf(file_path: Path) -> list:
    loader = PDFPlumberLoader(str(file_path))
    documents = await loader.aload()
    return enrich_documents_with_metadata(documents, file_path)

def enrich_documents_with_metadata(documents: list, file_path: Path) -> list:
    document_type = classify_document_type(file_path.name)
    jurisdiction = extract_jurisdiction(file_path.name)

    for doc in documents:
        doc.metadata.update({
            "source_file": file_path.name,
            "document_type": document_type,
            "jurisdiction": jurisdiction,
            "loaded_at": datetime.utcnow().isoformat(),
        })
    return documents

def classify_document_type(filename: str) -> str:
    classifications = {
        "regulation": ["ley", "decreto", "resolucion", "normativa", "regulation"],
        "company_history": ["historia", "history", "empresa", "company", "vera"],
        "financial_system": ["financiero", "financial", "bcentral", "bcu"],
        "layout": ["layout", "estructura", "structure", "organigrama"],
    }

    filename_lower = filename.lower()
    for doc_type, keywords in classifications.items():
        if any(kw in filename_lower for kw in keywords):
            return doc_type
    return "general"
```

### 3.3 Directory Loading Pattern

```python
from langchain_community.document_loaders import DirectoryLoader

async def load_knowledge_base(knowledge_dir: Path) -> list:
    pdf_loader = DirectoryLoader(
        str(knowledge_dir),
        glob="**/*.pdf",
        loader_cls=PDFPlumberLoader,
        show_progress=True,
    )

    markdown_loader = DirectoryLoader(
        str(knowledge_dir),
        glob="**/*.md",
        loader_cls=TextLoader,
    )

    pdf_docs = await pdf_loader.aload()
    md_docs = await markdown_loader.aload()

    return pdf_docs + md_docs
```

---

## 4. Text Splitting Strategies

### 4.1 Chunking for Financial/Regulatory Documents

Financial documents require special chunking to preserve legal references and regulatory context.

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import Literal

CHUNK_SIZES = {
    "regulation": 1500,
    "company_history": 1000,
    "financial_system": 1200,
    "layout": 800,
    "general": 1000,
}

OVERLAP_RATIOS = {
    "regulation": 0.25,
    "company_history": 0.15,
    "financial_system": 0.20,
    "layout": 0.10,
    "general": 0.20,
}

def create_text_splitter(
    document_type: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> RecursiveCharacterTextSplitter:

    effective_chunk_size = chunk_size or CHUNK_SIZES.get(document_type, 1000)
    default_overlap = int(effective_chunk_size * OVERLAP_RATIOS.get(document_type, 0.20))
    effective_overlap = chunk_overlap or default_overlap

    return RecursiveCharacterTextSplitter(
        chunk_size=effective_chunk_size,
        chunk_overlap=effective_overlap,
        length_function=len,
        separators=[
            "\n\n",
            "\n",
            ". ",
            "; ",
            ", ",
            " ",
            "",
        ],
        add_start_index=True,
        strip_whitespace=True,
    )
```

### 4.2 Document Processing Pipeline

```python
from langchain_core.documents import Document
from typing import AsyncGenerator

async def process_documents_for_indexing(
    documents: list[Document],
) -> AsyncGenerator[list[Document], None]:

    documents_by_type: dict[str, list[Document]] = {}

    for doc in documents:
        doc_type = doc.metadata.get("document_type", "general")
        if doc_type not in documents_by_type:
            documents_by_type[doc_type] = []
        documents_by_type[doc_type].append(doc)

    for doc_type, type_docs in documents_by_type.items():
        splitter = create_text_splitter(doc_type)
        chunks = splitter.split_documents(type_docs)

        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = i
            chunk.metadata["total_chunks"] = len(chunks)

        yield chunks
```

---

## 5. ChromaDB Integration

### 5.1 Collection Management Strategy

For Uruguay financial/regulatory documents, organize collections by document domain:

```python
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from chromadb.config import Settings
import chromadb

COLLECTIONS = {
    "regulations_uruguay": "Laws, decrees, and financial regulations from Uruguay",
    "company_history": "Vera company history, mission, and organizational information",
    "financial_systems": "Information about Uruguay's financial system (BCU, BSE, etc.)",
    "internal_policies": "Internal company policies and procedures",
}

async def create_chroma_client(host: str, port: int) -> chromadb.AsyncClient:
    settings = Settings(
        chroma_server_host=host,
        chroma_server_http_port=port,
        anonymized_telemetry=False,
    )
    return chromadb.AsyncClient(settings=settings)

class ChromaVectorStoreManager:
    def __init__(
        self,
        host: str,
        port: int,
        embedding_model: str = "text-embedding-3-small",
    ):
        self.host = host
        self.port = port
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self._stores: dict[str, Chroma] = {}

    async def get_store(self, collection_name: str) -> Chroma:
        if collection_name not in self._stores:
            self._stores[collection_name] = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                client=await create_chroma_client(self.host, self.port),
            )
        return self._stores[collection_name]

    async def index_documents(
        self,
        collection_name: str,
        documents: list[Document],
        batch_size: int = 100,
    ) -> list[str]:
        store = await self.get_store(collection_name)
        all_ids = []

        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            ids = await store.aadd_documents(batch)
            all_ids.extend(ids)

        return all_ids
```

### 5.2 Metadata Schema for Uruguay Financial Documents

```python
from pydantic import BaseModel, Field
from typing import Literal
from datetime import date

class UruguayDocumentMetadata(BaseModel):
    source_file: str = Field(description="Original PDF filename")
    document_type: Literal[
        "regulation",
        "company_history",
        "financial_system",
        "layout",
        "general",
    ]
    jurisdiction: Literal["uruguay", "international", "internal"] = Field(
        default="uruguay"
    )
    publication_date: date | None = Field(default=None)
    effective_date: date | None = Field(default=None)
    issuing_authority: str | None = Field(
        default=None,
        description="BCU, BSE, Government ministry, etc.",
    )
    regulation_number: str | None = Field(
        default=None,
        description="e.g., 'Ley 19.210', 'Decreto 123/020'",
    )
    chunk_index: int
    total_chunks: int
    page_number: int | None = Field(default=None)

    class Config:
        extra = "allow"
```

### 5.3 Hybrid Search with Metadata Filtering

```python
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever

async def search_with_filters(
    store: Chroma,
    query: str,
    document_types: list[str] | None = None,
    jurisdiction: str | None = None,
    issuing_authority: str | None = None,
    k: int = 5,
) -> list[Document]:

    where_filter = {}

    if document_types:
        where_filter["document_type"] = {"$in": document_types}

    if jurisdiction:
        where_filter["jurisdiction"] = jurisdiction

    if issuing_authority:
        where_filter["issuing_authority"] = issuing_authority

    results = await store.asimilarity_search(
        query,
        k=k,
        filter=where_filter if where_filter else None,
    )

    return results

async def multi_collection_search(
    manager: ChromaVectorStoreManager,
    query: str,
    collections: list[str],
    k_per_collection: int = 3,
) -> list[tuple[str, Document]]:

    results = []
    for collection_name in collections:
        store = await manager.get_store(collection_name)
        docs = await store.asimilarity_search(query, k=k_per_collection)
        for doc in docs:
            results.append((collection_name, doc))

    return sorted(results, key=lambda x: x[1].metadata.get("score", 0), reverse=True)
```

---

## 6. RAG as an Agent Tool

### 6.1 Creating the Knowledge Base Tool

```python
from langchain.tools import tool
from langchain_core.documents import Document
from typing import Literal

@tool(response_format="content_and_artifact")
async def search_uruguay_knowledge(
    query: str,
    document_type: Literal[
        "regulation",
        "company_history",
        "financial_system",
        "all",
    ] = "all",
) -> tuple[str, list[Document]]:
    """Search the VeraMoney knowledge base for information about Uruguay's
    financial regulations, company history, and financial systems.

    Use this tool when users ask about:
    - Uruguayan financial laws and regulations
    - Vera company information and history
    - Bank compliance in Uruguay

    Args:
        query: The search query in natural language
        document_type: Filter by document type, or "all" for no filter
    """
    collections_to_search = (
        ["regulations_uruguay", "company_history", "financial_systems"]
        if document_type == "all"
        else [f"{document_type}s_uruguay"]
        if document_type != "company_history"
        else ["company_history"]
    )

    manager = get_vector_store_manager()
    results = await multi_collection_search(
        manager,
        query,
        collections_to_search,
        k_per_collection=3,
    )

    if not results:
        return "No relevant information found in the knowledge base.", []

    formatted_results = []
    retrieved_docs = []

    for collection, doc in results[:6]:
        source = doc.metadata.get("source_file", "Unknown")
        page = doc.metadata.get("page_number", "N/A")
        authority = doc.metadata.get("issuing_authority", "")
        regulation = doc.metadata.get("regulation_number", "")

        citation_parts = [f"Source: {source}"]
        if page != "N/A":
            citation_parts.append(f"Page: {page}")
        if authority:
            citation_parts.append(f"Authority: {authority}")
        if regulation:
            citation_parts.append(f"Regulation: {regulation}")

        formatted_results.append(
            f"[{' | '.join(citation_parts)}]\n{doc.page_content}"
        )
        retrieved_docs.append(doc)

    return "\n\n---\n\n".join(formatted_results), retrieved_docs
```

### 6.2 Integrating with the Conversational Agent

```python
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.tools import Tool

async def create_rag_enabled_agent(
    model_name: str = "gpt-4.1",
) -> :

    model = ChatOpenAI(
        model=model_name,
        temperature=0.1,
    )

    tools = [
        search_uruguay_knowledge,
    ]

    system_prompt = """You are a knowledgeable financial assistant for VeraMoney,
specializing in Uruguay's financial system, regulations, and company information.

<guidelines>
- Always use the search_uruguay_knowledge tool when users ask about:
  * Uruguayan financial laws, regulations, or compliance
  * Vera company history or policies
  * BCU (Central Bank of Uruguay) requirements
  * Financial services in Uruguay

- When providing information from the knowledge base:
  * Always cite your sources using the format [Source: filename | Page: X]
  * If the information is incomplete, acknowledge the limitation
  * Never hallucinate or invent regulations or policies

- For questions outside the knowledge base scope:
  * Clearly state that the information is not in your knowledge base
  * Suggest where the user might find accurate information

- Respond in the same language the user used (Spanish or English)
</guidelines>"""

    agent = create_agent(
        model,
        tools=tools,
        system_prompt=system_prompt,
    )

    return agent
```

### 6.3 Streaming RAG Responses

```python
from langchain.messages import HumanMessage, AIMessage

async def stream_rag_response(
    agent,
    query: str,
    session_id: str | None = None,
):
    config = {"configurable": {"thread_id": session_id}} if session_id else {}

    async for event in agent.astream(
        {"messages": [HumanMessage(content=query)]},
        config=config,
        stream_mode="values",
    ):
        last_message = event["messages"][-1]

        if isinstance(last_message, AIMessage):
            if last_message.content:
                yield {
                    "type": "token",
                    "content": last_message.content,
                }

            if last_message.tool_calls:
                for tool_call in last_message.tool_calls:
                    yield {
                        "type": "tool_call",
                        "name": tool_call["name"],
                        "args": tool_call["args"],
                    }
```

---

## 7. Knowledge Base Document Structure

### 7.1 Recommended Directory Layout

```
docs/knowledge_base/
├── regulations/
│   ├── uruguay/
│   │   ├── ley_19_210_transparencia.pdf          # Transparency Law
│   │   ├── ley_18_312_usura.pdf                  # Usury Law
│   │   ├── decreto_154_020_compliance.pdf        # Compliance decree
│   │   └── bcu_regulations/
│   │       ├── bcu_recircular_2294.pdf           # BCU circulars
│   │       └── bcu_norma_externa.pdf             # External regulations
│   └── international/
│       └── basilea_iii_resumen.pdf               # Basel III summary
│
├── company_history/
│   ├── vera_historia_empresa.md
│   ├── vera_mision_vision.md
│   └── vera_organigrama.pdf
│
├── financial_system/
│   ├── sistema_financiero_uruguayo.md            # Overview
│   ├── bcu_funciones.md                          # BCU functions
│   └── bse_servicios.md                          # BSE services
│
└── internal_policies/
    ├── politica_privacidad.md
    ├── terminos_servicio.md
    └── procedimientos_kyc.pdf
```

### 7.2 Document Metadata Extraction

```python
import re
from datetime import datetime

def extract_regulation_metadata(filename: str) -> dict:
    patterns = {
        "ley": r"ley[_\s]*(\d+)[_\._](\d+)",
        "decreto": r"decreto[_\s]*(\d+)[/_](\d+)",
        "bcu": r"bcu[_\s]*(recircular|norma)[_\s]*(\d+)",
    }

    filename_lower = filename.lower()

    for doc_type, pattern in patterns.items():
        match = re.search(pattern, filename_lower)
        if match:
            if doc_type == "ley":
                return {
                    "document_type": "regulation",
                    "issuing_authority": "Poder Legislativo",
                    "regulation_number": f"Ley {match.group(1)}.{match.group(2)}",
                }
            elif doc_type == "decreto":
                year = match.group(2)
                if len(year) == 2:
                    year = f"20{year}" if int(year) < 50 else f"19{year}"
                return {
                    "document_type": "regulation",
                    "issuing_authority": "Poder Ejecutivo",
                    "regulation_number": f"Decreto {match.group(1)}/{year}",
                }
            elif doc_type == "bcu":
                return {
                    "document_type": "regulation",
                    "issuing_authority": "BCU",
                    "regulation_number": f"{match.group(1).title()} {match.group(2)}",
                }

    return {"document_type": "general"}
```

---

## 8. Embedding Model Selection

### 8.1 Model Comparison for Financial Documents

| Model | Dimensions | Context | Cost | Best For |
|-------|------------|---------|------|----------|
| **text-embedding-3-small** | 1536 | 8191 | $0.02/1M | **General purpose** |
| **text-embedding-3-large** | 3072 | 8191 | $0.13/1M | High precision |
| **text-embedding-ada-002** | 1536 | 8191 | $0.10/1M | Legacy compatibility |

### 8.2 Recommended Configuration

```python
from langchain_openai import OpenAIEmbeddings
from pydantic_settings import BaseSettings

class EmbeddingConfig(BaseSettings):
    openai_api_key: str
    embedding_model: str = "text-embedding-3-small"
    embedding_batch_size: int = 100

    class Config:
        env_prefix = ""

def create_embedding_model(config: EmbeddingConfig) -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=config.embedding_model,
        chunk_size=config.embedding_batch_size,
    )
```

**Recommendation:** Use `text-embedding-3-small` for Spanish/Uruguayan financial documents. It provides excellent performance-to-cost ratio and handles mixed language content well.

---

## 9. Performance Optimization

### 9.1 Batch Loading Strategy

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
)
async def batch_index_documents(
    manager: ChromaVectorStoreManager,
    collection_name: str,
    documents: list[Document],
    batch_size: int = 100,
) -> int:

    total_indexed = 0
    for i in range(0, len(documents), batch_size):
        batch = documents[i : i + batch_size]
        ids = await manager.index_documents(collection_name, batch)
        total_indexed += len(ids)

    return total_indexed
```

### 9.2 Indexing Pipeline Script

```python
import asyncio
from pathlib import Path

async def run_indexing_pipeline(
    knowledge_base_path: Path,
    chroma_host: str,
    chroma_port: int,
):

    print("Loading documents...")
    documents = await load_knowledge_base(knowledge_base_path)
    print(f"Loaded {len(documents)} documents")

    print("Processing and chunking documents...")
    all_chunks = []
    async for chunks in process_documents_for_indexing(documents):
        all_chunks.extend(chunks)
    print(f"Created {len(all_chunks)} chunks")

    print("Indexing in ChromaDB...")
    manager = ChromaVectorStoreManager(chroma_host, chroma_port)

    chunks_by_collection: dict[str, list[Document]] = {}
    for chunk in all_chunks:
        doc_type = chunk.metadata.get("document_type", "general")
        collection = f"{doc_type}s_uruguay"
        if collection not in chunks_by_collection:
            chunks_by_collection[collection] = []
        chunks_by_collection[collection].append(chunk)

    for collection, collection_chunks in chunks_by_collection.items():
        indexed = await batch_index_documents(manager, collection, collection_chunks)
        print(f"Indexed {indexed} chunks in {collection}")

    print("Indexing complete!")

if __name__ == "__main__":
    asyncio.run(
        run_indexing_pipeline(
            Path("docs/knowledge_base"),
            "localhost",
            8001,
        )
    )
```

---

## 10. Key Findings

1. **ChromaDB v1.5.0+** introduces improved async support and better metadata filtering - both critical for the Uruguay regulatory search use case

2. **PDFPlumberLoader** is the optimal choice for financial documents due to its superior table extraction capabilities

3. **Chunk overlap of 20-25%** is essential for regulatory documents to maintain legal context across chunk boundaries

4. **Metadata-driven filtering** enables targeted retrieval (e.g., "only BCU regulations from 2024")

5. **Agentic RAG** pattern is recommended for VeraMoney - it allows the agent to make multiple targeted searches for complex regulatory queries

6. **Citations via artifacts** - LangChain v1's `response_format="content_and_artifact"` enables proper source attribution without polluting the LLM context

7. **Collection-per-domain** strategy provides cleaner separation than a single monolithic collection

---

## 11. Implementation Checklist

- [ ] Create `docs/knowledge_base/` directory structure
- [ ] Add PDF documents (Laws, BCU regulations, company history)
- [ ] Implement `src/rag/loader.py` with PDFPlumberLoader
- [ ] Implement `src/rag/splitter.py` with domain-specific chunking
- [ ] Implement `src/rag/vectorstore.py` with ChromaDB manager
- [ ] Implement `src/rag/retriever.py` with hybrid search
- [ ] Create `search_uruguay_knowledge` tool in `src/tools/knowledge.py`
- [ ] Add tool to conversational agent configuration
- [ ] Test indexing pipeline with sample documents
- [ ] Verify citation formatting in responses
- [ ] Add integration tests for RAG queries

---

## 12. References

### Official Documentation
- [LangChain RAG Tutorial](https://docs.langchain.com/oss/python/langchain/rag)
- [LangChain Retrieval Guide](https://docs.langchain.com/oss/python/langchain/retrieval)
- [LangChain Chroma Integration](https://docs.langchain.com/oss/python/integrations/vectorstores/chroma)
- [ChromaDB Official Docs](https://docs.trychroma.com/)

### Project Internal References
- `.claude/skills/langchain/reference/advanced/rag_agent.md` - Complete RAG implementation
- `.claude/skills/langchain/reference/advanced/retrieval.md` - Retrieval patterns
- `.claude/skills/langchain/reference/basics/tools.md` - Tool creation patterns
- `docs/codechallenge/06-bonus-rag/rag-pipeline.md` - Project RAG requirements

### Research Sources
- [FinMTEB: Finance Massive Text Embedding Benchmark](https://huggingface.co/datasets/FinanceMTEB)
- [RAG Citation Best Practices](https://python.langchain.com.cn/docs/modules/chains/additional/)

---

*Report generated by: El Barto*
*Date: 2026-02-19*
