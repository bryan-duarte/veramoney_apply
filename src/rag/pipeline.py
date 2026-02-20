import logging
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from langchain_core.documents import Document

from src.config import Settings
from src.rag.document_configs import DOCUMENT_SOURCES
from src.rag.loader import DocumentLoader
from src.rag.retriever import KnowledgeRetriever
from src.rag.schemas import RAGPipelineStatus
from src.rag.splitter import split_documents
from src.rag.vectorstore import ChromaVectorStoreManager


logger = logging.getLogger(__name__)

EXPECTED_DOCUMENT_COUNT = 3


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
        logger.info("=" * 60)
        logger.info("RAG PIPELINE INITIALIZATION")
        logger.info("=" * 60)

        await self._initialize_vector_store()

        collection_already_loaded = self._vector_store_manager.collection_has_documents()

        if collection_already_loaded:
            self._set_cached_status()
            self._retriever = self._create_retriever()
            logger.info("RAG PIPELINE READY (cached)")
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
        logger.info(
            "chroma_host=%s chroma_port=%d collection=%s",
            self._settings.chroma_host,
            self._settings.chroma_port,
            self._settings.rag_collection_name,
        )
        await self._vector_store_manager.initialize()

    async def _load_documents(self) -> None:
        self._status.status = "loading"
        loader = self._document_loader or DocumentLoader()
        all_chunks: list[Document] = []
        load_errors: list[str] = []

        for index, document_config in enumerate(DOCUMENT_SOURCES, start=1):
            logger.info("[%d/%d] Loading: %s", index, EXPECTED_DOCUMENT_COUNT, document_config.title)
            try:
                documents = await loader.download_and_load(document_config)
                chunks = split_documents(documents=documents, document_config=document_config)
                all_chunks.extend(chunks)
                self._status.document_count += 1
                logger.info(
                    "[%d/%d] SUCCESS: %s - %d pages -> %d chunks",
                    index, EXPECTED_DOCUMENT_COUNT, document_config.key,
                    len(documents), len(chunks),
                )
            except Exception as error:
                error_message = f"Failed to load {document_config.key}: {error}"
                load_errors.append(error_message)
                logger.exception("[%d/%d] FAILED: %s", index, EXPECTED_DOCUMENT_COUNT, document_config.key)

        await self._index_chunks(all_chunks, load_errors)
        self._retriever = self._create_retriever()

    async def _index_chunks(self, chunks: list, errors: list[str]) -> None:
        has_chunks = len(chunks) > 0
        if has_chunks:
            logger.info("Indexing %d chunks into ChromaDB...", len(chunks))
            await self._vector_store_manager.add_documents(chunks)

        self._status.status = "ready" if not errors else "partial"
        self._status.chunk_count = len(chunks)
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
