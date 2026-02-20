# Startup Loader & Configuration Implementation

## Overview

Application startup logic that initializes the RAG pipeline (check-and-load), configures the knowledge tool client, and adds necessary settings fields.

## Files to Modify

- `src/config/settings.py` - Add ChromaDB and RAG settings
- `src/api/app.py` - Implement lifespan startup/shutdown hooks
- `pyproject.toml` - Add pdfplumber dependency

## Implementation Guidelines

### settings.py
- Add fields:
  - `chroma_host: str` (default "localhost", alias for docker override)
  - `chroma_port: int` (default 8001)
  - `rag_collection_name: str` (default "veramoney_knowledge")
  - `rag_retrieval_k: int` (default 4)
- These follow the existing field patterns with Field descriptions
- Docker-compose already passes CHROMA_HOST and CHROMA_PORT to the app container

### app.py lifespan
- Import initialize_rag_pipeline from src.rag
- Import configure_knowledge_client from src.tools.knowledge
- In lifespan startup (before yield):
  1. Initialize MemoryStore (if not already done)
  2. Call `initialize_rag_pipeline(settings)` which:
     - Creates ChromaVectorStoreManager with settings
     - Checks if collection has documents
     - If empty: downloads PDFs, processes, embeds, stores
     - If populated: skips (fast path)
     - Returns KnowledgeRetriever instance
  3. Call `configure_knowledge_client(retriever)` to set up the tool's singleton
  4. Log startup completion with document count
- In lifespan shutdown (after yield):
  - Close ChromaDB connections if needed
  - Close MemoryStore
- Wrap entire RAG init in try-except: if RAG fails, log error but don't crash the app
  - App should still serve weather/stock queries without RAG

### pyproject.toml
- Add `pdfplumber>=0.11.0` to dependencies
- This is needed as a backend for langchain-community's PDFPlumberLoader
- Verify if langchain-community already pulls it as a dependency; if so, skip

### .env.example
- Add CHROMA_HOST and CHROMA_PORT entries (they exist in docker-compose but not in .env.example)
- Add RAG_COLLECTION_NAME and RAG_RETRIEVAL_K entries

## Dependencies

- src/rag (initialize_rag_pipeline)
- src/tools/knowledge (configure_knowledge_client)
- src/config (Settings)

## Integration Notes

- The check-and-load strategy means first startup after a fresh ChromaDB volume takes 30-60s
- Subsequent startups with populated ChromaDB are fast (<1s for the check)
- Graceful degradation: if ChromaDB is down, app starts without RAG capabilities
- Docker-compose already has a health check on ChromaDB - the app waits for it
- The lifespan is the single orchestration point for all startup logic
