import logging
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from langchain_core.documents import Document

from src.config import Settings
from src.rag.document_configs import DOCUMENT_SOURCES
from src.rag.loader import DocumentLoader, download_and_load_document
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

    def get_retriever(self) -> KnowledgeRetriever:
        return self.retriever

    def get_status(self) -> RAGPipelineStatus:
        return self.status


async def initialize_rag_pipeline(  # noqa: PLR0915
    chroma_host: str,
    chroma_port: int,
    collection_name: str,
    openai_api_key: str,
    embedding_model: str,
    retrieval_k: int = 4,
) -> tuple[KnowledgeRetriever, RAGPipelineStatus]:
    logger.info("=" * 60)
    logger.info("RAG PIPELINE INITIALIZATION")
    logger.info("=" * 60)
    logger.info("chroma_host=%s chroma_port=%d collection=%s", chroma_host, chroma_port, collection_name)

    status = RAGPipelineStatus(
        status="initializing",
        document_count=0,
        chunk_count=0,
        errors=[],
    )

    vector_store_manager = ChromaVectorStoreManager(
        chroma_host=chroma_host,
        chroma_port=chroma_port,
        collection_name=collection_name,
        openai_api_key=openai_api_key,
        embedding_model=embedding_model,
    )

    logger.info("Connecting to ChromaDB...")
    await vector_store_manager.initialize()
    logger.info("ChromaDB connection established")

    logger.info("Checking if collection '%s' already has documents...", collection_name)
    collection_already_populated = vector_store_manager.collection_has_documents()
    existing_chunk_count = vector_store_manager.get_collection_count()

    if collection_already_populated:
        logger.info("-" * 60)
        logger.info("IDEMPOTENT LOAD: Collection already populated")
        logger.info("Skipping document download and indexing")
        logger.info("Existing chunks in collection: %d", existing_chunk_count)
        logger.info("-" * 60)

        retriever = KnowledgeRetriever(
            vector_store_manager=vector_store_manager,
            default_k=retrieval_k,
        )

        status.status = "ready"
        status.chunk_count = existing_chunk_count
        status.document_count = EXPECTED_DOCUMENT_COUNT

        logger.info("=" * 60)
        logger.info("RAG PIPELINE READY (cached)")
        logger.info("=" * 60)

        return retriever, status

    logger.info("-" * 60)
    logger.info("FRESH LOAD: Collection is empty, loading documents")
    logger.info("Documents to load: %d", EXPECTED_DOCUMENT_COUNT)
    logger.info("-" * 60)

    status.status = "loading"

    all_chunks: list[Document] = []
    documents_loaded = 0
    load_errors: list[str] = []

    for index, document_config in enumerate(DOCUMENT_SOURCES, start=1):
        logger.info("[%d/%d] Loading: %s", index, EXPECTED_DOCUMENT_COUNT, document_config.title)

        try:
            documents = await download_and_load_document(document_config)

            chunks = split_documents(
                documents=documents,
                document_config=document_config,
            )

            all_chunks.extend(chunks)
            documents_loaded += 1

            logger.info("[%d/%d] SUCCESS: %s - %d pages -> %d chunks",
                index,
                EXPECTED_DOCUMENT_COUNT,
                document_config.key,
                len(documents),
                len(chunks),
            )

        except Exception as error:
            error_message = f"Failed to load {document_config.key}: {error}"
            load_errors.append(error_message)
            logger.exception(
                "[%d/%d] FAILED: %s - %s",
                index,
                EXPECTED_DOCUMENT_COUNT,
                document_config.key,
                str(error),
            )

    if all_chunks:
        logger.info("-" * 60)
        logger.info("Indexing %d chunks into ChromaDB...", len(all_chunks))
        await vector_store_manager.add_documents(all_chunks)
        logger.info("Indexing complete")

    retriever = KnowledgeRetriever(
        vector_store_manager=vector_store_manager,
        default_k=retrieval_k,
    )

    status.status = "ready" if not load_errors else "partial"
    status.document_count = documents_loaded
    status.chunk_count = len(all_chunks)
    status.errors = load_errors

    logger.info("-" * 60)
    logger.info("RAG LOAD SUMMARY:")
    logger.info("  Documents loaded: %d/%d", documents_loaded, EXPECTED_DOCUMENT_COUNT)
    logger.info("  Total chunks: %d", len(all_chunks))
    logger.info("  Errors: %d", len(load_errors))
    if load_errors:
        for error in load_errors:
            logger.warning("  - %s", error)
    logger.info("=" * 60)
    logger.info("RAG PIPELINE READY")
    logger.info("=" * 60)

    return retriever, status
