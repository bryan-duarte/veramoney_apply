# RAG Pipeline Implementation

## Overview

Convert the 152-line `initialize_rag_pipeline()` function into a `RAGPipeline` class with clear method separation.

## Files to Create

- `src/rag/pipeline.py` - RAGPipeline class (replace function)
- `src/rag/loader.py` - DocumentLoader class (replace functions)

## Files to Modify

- `src/rag/__init__.py` - Export RAGPipeline class
- `src/di/container.py` - Instantiate RAGPipeline

## Implementation Guidelines

### RAGPipeline Class

```python
class RAGPipeline:
    def __init__(
        self,
        settings: Settings,
        vector_store_manager: ChromaVectorStoreManager | None = None,
        document_loader: DocumentLoader | None = None,
    ):
        self._settings = settings
        self._vector_store_manager = vector_store_manager
        self._document_loader = document_loader
        self._retriever: KnowledgeRetriever | None = None
        self._status = RAGPipelineStatus(
            status="initializing",
            document_count=0,
            chunk_count=0,
            errors=[],
        )

    @classmethod
    def from_settings(cls, settings: Settings) -> "RAGPipeline":
        return cls(settings=settings)

    @classmethod
    def with_dependencies(
        cls,
        settings: Settings,
        vector_store_manager: ChromaVectorStoreManager,
        document_loader: DocumentLoader,
    ) -> "RAGPipeline":
        return cls(
            settings=settings,
            vector_store_manager=vector_store_manager,
            document_loader=document_loader,
        )

    @property
    def status(self) -> RAGPipelineStatus:
        return self._status

    @property
    def retriever(self) -> KnowledgeRetriever:
        if self._retriever is None:
            raise RuntimeError("Pipeline not initialized. Call initialize() first.")
        return self._retriever

    @property
    def is_ready(self) -> bool:
        return self._status.status == "ready"

    @property
    def has_errors(self) -> bool:
        return len(self._status.errors) > 0

    async def initialize(self) -> None:
        await self._initialize_vector_store()

        collection_already_loaded = self._vector_store_manager.collection_has_documents()
        if collection_already_loaded:
            self._set_cached_status()
            self._retriever = self._create_retriever()
            return

        await self._load_documents()

    async def _initialize_vector_store(self) -> None:
        if self._vector_store_manager is None:
            self._vector_store_manager = ChromaVectorStoreManager(
                chroma_host=self._settings.chroma_host,
                chroma_port=self._settings.chroma_port,
                collection_name=self._settings.rag_collection_name,
                openai_api_key=self._settings.openai_api_key,
                embedding_model=self._settings.openai_embedding_model,
            )
            await self._vector_store_manager.initialize()

    async def _load_documents(self) -> None:
        loader = self._document_loader or DocumentLoader()
        all_chunks: list[Document] = []
        load_errors: list[str] = []

        for document_config in DOCUMENT_SOURCES:
            try:
                documents = await loader.download_and_load(document_config)
                chunks = split_documents(documents, document_config)
                all_chunks.extend(chunks)
                self._status.document_count += 1
            except Exception as error:
                error_message = f"Failed to load {document_config.key}: {error}"
                load_errors.append(error_message)

        await self._index_chunks(all_chunks, load_errors)
        self._retriever = self._create_retriever()

    async def _index_chunks(
        self,
        chunks: list[Document],
        errors: list[str],
    ) -> None:
        has_chunks = len(chunks) > 0
        if has_chunks:
            await self._vector_store_manager.add_documents(chunks)
            self._status.chunk_count = len(chunks)

        self._status.status = "ready" if not errors else "partial"
        self._status.errors = errors

    def _create_retriever(self) -> KnowledgeRetriever:
        return KnowledgeRetriever(
            vector_store_manager=self._vector_store_manager,
            default_k=self._settings.rag_retrieval_k,
        )

    def _set_cached_status(self) -> None:
        chunk_count = self._vector_store_manager.get_collection_count()
        self._status = RAGPipelineStatus(
            status="ready",
            document_count=EXPECTED_DOCUMENT_COUNT,
            chunk_count=chunk_count,
            errors=[],
        )

    def get_retriever(self) -> KnowledgeRetriever:
        return self.retriever

    def get_status(self) -> RAGPipelineStatus:
        return self.status
```

### DocumentLoader Class

```python
class DocumentLoader:
    def __init__(
        self,
        http_client: httpx.AsyncClient | None = None,
        timeout_seconds: float = DOWNLOAD_TIMEOUT_SECONDS,
    ):
        self._http_client = http_client
        self._timeout_seconds = timeout_seconds

    @classmethod
    def with_timeout(cls, timeout_seconds: float) -> "DocumentLoader":
        return cls(timeout_seconds=timeout_seconds)

    async def download_and_load(
        self,
        config: DocumentConfig,
    ) -> list[Document]:
        temp_path = await self._download_pdf(config.url)
        documents = self._load_pdf(temp_path)
        temp_path.unlink()

        return self._enrich_metadata(documents, config)

    async def _download_pdf(self, url: str) -> Path:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(MAX_DOWNLOAD_RETRIES),
            wait=wait_exponential(multiplier=INITIAL_RETRY_DELAY_SECONDS),
            reraise=True,
        ):
            with attempt:
                async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                    response = await client.get(url)
                    response.raise_for_status()

                    temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
                    temp_file.write(response.content)
                    temp_file.close()
                    return Path(temp_file.name)

    @staticmethod
    def _load_pdf(path: Path) -> list[Document]:
        documents: list[Document] = []
        with pdfplumber.open(path) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                has_text = text is not None and len(text.strip()) > 0
                if has_text:
                    documents.append(Document(
                        page_content=text,
                        metadata={"page": page_number},
                    ))
        return documents

    @staticmethod
    def _enrich_metadata(
        documents: list[Document],
        config: DocumentConfig,
    ) -> list[Document]:
        enriched: list[Document] = []
        for document in documents:
            page_number = document.metadata.get("page", 0)
            chunk_metadata = ChunkMetadata(
                document_type=config.document_type.value,
                source_url=config.url,
                document_title=config.title,
                language=config.language,
                page_number=page_number,
                chunk_index=0,
            )
            enriched.append(Document(
                page_content=document.page_content,
                metadata=chunk_metadata.model_dump(),
            ))
        return enriched
```

## OOP Patterns Applied

| Pattern | Usage |
|---------|-------|
| `@classmethod` | `from_settings()` - factory from settings |
| `@classmethod` | `with_dependencies()` - factory with all deps |
| `@classmethod` | `with_timeout()` - alternative constructor |
| `@property` | `status` - read-only access to pipeline status |
| `@property` | `retriever` - read-only access with validation |
| `@property` | `is_ready` - boolean state check |
| `@property` | `has_errors` - boolean error check |
| `@staticmethod` | `_load_pdf()` - pure function of path |
| `@staticmethod` | `_enrich_metadata()` - pure function of inputs |
| Helper methods | `_initialize_vector_store()`, `_load_documents()`, `_index_chunks()` |
| Named booleans | `collection_already_loaded`, `has_chunks`, `has_text` |
| Constructor injection | `vector_store_manager`, `document_loader`, `http_client` |

## Method Extraction from Original Function

| Original Code Section | New Method | Type |
|-----------------------|------------|------|
| VectorStoreManager creation | `_initialize_vector_store()` | Helper |
| Collection check | `collection_already_loaded` | Named boolean |
| Document loading loop | `_load_documents()` | Helper |
| Chunk indexing | `_index_chunks()` | Helper |
| Retriever creation | `_create_retriever()` | Helper |
| Status creation | `_set_cached_status()` | Helper |

## Dependencies

- Settings (required)
- ChromaVectorStoreManager (optional, created if None)
- DocumentLoader (optional, created if None)
- httpx.AsyncClient (optional for DocumentLoader)

## Integration Notes

- `initialize_rag_pipeline()` function kept for backward compatibility
- Function creates RAGPipeline instance via `from_settings()` and calls `initialize()`
- Same return signature: `tuple[KnowledgeRetriever, RAGPipelineStatus]`
- Properties provide cleaner API for status checks
- Static methods improve testability of pure functions
