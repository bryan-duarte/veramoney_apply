# RAG Pipeline Implementation

## Overview

Core RAG pipeline in `src/rag/` responsible for downloading PDFs, processing them into chunks, embedding them, and storing in ChromaDB. Also provides retrieval interface for the knowledge tool.

## Files to Create

- `src/rag/schemas.py` - Data models for document configuration, chunk metadata, and pipeline state
- `src/rag/document_configs.py` - Static configuration for the 3 PDF sources
- `src/rag/loader.py` - Async PDF download + PDFPlumberLoader processing
- `src/rag/splitter.py` - Type-specific text splitting
- `src/rag/vectorstore.py` - ChromaDB collection management and embedding storage
- `src/rag/retriever.py` - Similarity search with metadata filtering
- `src/rag/__init__.py` - Public API exports

## Implementation Guidelines

### schemas.py
- `DocumentConfig` model: key, url, document_type, title, language, chunk_size, chunk_overlap
- `DocumentType` StrEnum: VERA_HISTORY, FINTEC_REGULATION, BANK_REGULATION
- `ChunkMetadata` model: document_type, source_url, document_title, language, page_number, chunk_index
- `RetrievalResult` model: content, metadata (ChunkMetadata), relevance_score

### document_configs.py
- Module-level constant `DOCUMENT_SOURCES: list[DocumentConfig]` with the 3 PDFs
- Each entry has hardcoded metadata (URL, type, title, language, chunk_size, chunk_overlap)
- vera_history: chunk_size=1000, chunk_overlap=200
- fintec_regulation: chunk_size=1500, chunk_overlap=300
- bank_regulation: chunk_size=1500, chunk_overlap=300

### loader.py
- Class `PDFDocumentLoader`
- Async method `download_and_load(document_config: DocumentConfig) -> list[Document]`
- Uses httpx.AsyncClient to download PDF to a temporary file
- Uses PDFPlumberLoader from langchain_community to extract pages
- Enriches each Document's metadata with fields from DocumentConfig
- Retry with tenacity on download failures (3 attempts, exponential backoff)
- Custom exception `DocumentDownloadError`
- Uses `tempfile` for temporary PDF storage, cleanup after loading

### splitter.py
- Function `split_documents(documents: list[Document], document_config: DocumentConfig) -> list[Document]`
- Creates RecursiveCharacterTextSplitter with chunk_size and chunk_overlap from config
- Separators: ["\n\n", "\n", ". ", " ", ""]
- Adds chunk_index to each chunk's metadata
- Returns list of chunked Documents

### vectorstore.py
- Class `ChromaVectorStoreManager`
- Init: receives chroma_host, chroma_port, collection_name, embedding model name
- Async method `initialize()` - creates ChromaDB HTTP client, initializes OpenAIEmbeddings
- Method `collection_has_documents() -> bool` - checks if collection exists and has >0 documents
- Async method `add_documents(documents: list[Document]) -> None` - batch adds with embeddings
- Batch size constant (e.g., EMBEDDING_BATCH_SIZE = 100)
- Async method `similarity_search(query: str, k: int, filter_metadata: dict | None) -> list[RetrievalResult]`
- Uses langchain_chroma.Chroma as the vector store interface

### retriever.py
- Class `KnowledgeRetriever`
- Wraps ChromaVectorStoreManager
- Async method `search(query: str, document_type: str | None, k: int) -> list[RetrievalResult]`
- Builds metadata filter dict if document_type is provided
- Returns structured RetrievalResult objects with relevance scores

### __init__.py
- Export: KnowledgeRetriever, ChromaVectorStoreManager, PDFDocumentLoader, DOCUMENT_SOURCES
- Export: initialize_rag_pipeline function (orchestrates full check-and-load flow)

## Dependencies

- langchain-community (PDFPlumberLoader)
- langchain-chroma (Chroma vector store)
- langchain-openai (OpenAIEmbeddings)
- chromadb (HTTP client)
- httpx (PDF download)
- tenacity (retry logic)
- pdfplumber (PDF processing backend)

## Integration Notes

- `initialize_rag_pipeline` is called from app lifespan on startup
- `KnowledgeRetriever` instance is used by the knowledge tool client
- ChromaDB connection uses settings.chroma_host and settings.chroma_port
- Embedding model uses settings.openai_embedding_model and settings.openai_api_key
