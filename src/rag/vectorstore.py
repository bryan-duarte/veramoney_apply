import logging
from typing import TypedDict

import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from src.rag.schemas import ChunkMetadata, RetrievalResult


logger = logging.getLogger(__name__)


class ChromaFilter(TypedDict, total=False):
    document_type: str
    language: str
    source_url: str


class ChromaVectorStoreManager:
    EMBEDDING_BATCH_SIZE: int = 100
    DEFAULT_RETRIEVAL_K: int = 4

    def __init__(
        self,
        chroma_host: str,
        chroma_port: int,
        collection_name: str,
        openai_api_key: str,
        embedding_model: str,
    ):
        self._chroma_host = chroma_host
        self._chroma_port = chroma_port
        self._collection_name = collection_name
        self._openai_api_key = openai_api_key
        self._embedding_model = embedding_model
        self._chroma_client: chromadb.HttpClient | None = None
        self._vector_store: Chroma | None = None
        self._embeddings: OpenAIEmbeddings | None = None

    async def initialize(self) -> None:
        self._chroma_client = chromadb.HttpClient(
            host=self._chroma_host,
            port=self._chroma_port,
        )

        self._embeddings = OpenAIEmbeddings(
            model=self._embedding_model,
            api_key=self._openai_api_key,
        )

        self._vector_store = Chroma(
            client=self._chroma_client,
            collection_name=self._collection_name,
            embedding_function=self._embeddings,
        )

        logger.info(
            "vectorstore_initialized host=%s port=%d collection=%s",
            self._chroma_host,
            self._chroma_port,
            self._collection_name,
        )

    def collection_has_documents(self) -> bool:
        if self._chroma_client is None:
            return False

        try:
            collection = self._chroma_client.get_collection(
                name=self._collection_name
            )
            document_count = collection.count()
            has_documents = document_count > 0

            logger.info(
                "vectorstore_check collection=%s count=%d has_documents=%s",
                self._collection_name,
                document_count,
                has_documents,
            )

            return has_documents
        except Exception:
            logger.info(
                "vectorstore_collection_not_found collection=%s",
                self._collection_name,
            )
            return False

    async def add_documents(self, documents: list[Document]) -> int:
        if self._vector_store is None:
            raise RuntimeError("Vector store not initialized. Call initialize() first.")

        total_chunks = len(documents)
        chunks_added = 0

        for batch_start in range(0, total_chunks, self.EMBEDDING_BATCH_SIZE):
            batch_end = min(batch_start + self.EMBEDDING_BATCH_SIZE, total_chunks)
            batch_documents = documents[batch_start:batch_end]

            await self._vector_store.aadd_documents(batch_documents)

            chunks_added += len(batch_documents)

            logger.info(
                "vectorstore_batch_added batch=%d-%d total=%d",
                batch_start,
                batch_end,
                total_chunks,
            )

        logger.info(
            "vectorstore_complete total_chunks=%d",
            chunks_added,
        )

        return chunks_added

    async def similarity_search(
        self,
        query: str,
        k: int | None = None,
        filter_metadata: ChromaFilter | None = None,
    ) -> list[RetrievalResult]:
        if self._vector_store is None:
            raise RuntimeError("Vector store not initialized. Call initialize() first.")

        retrieval_k = k if k is not None else self.DEFAULT_RETRIEVAL_K

        results_with_scores = await self._vector_store.asimilarity_search_with_score(
            query=query,
            k=retrieval_k,
            filter=filter_metadata,
        )

        retrieval_results = []

        for document, score in results_with_scores:
            chunk_metadata = ChunkMetadata(**document.metadata)

            retrieval_result = RetrievalResult(
                content=document.page_content,
                metadata=chunk_metadata,
                relevance_score=float(score),
            )
            retrieval_results.append(retrieval_result)

        logger.info(
            "vectorstore_search query_length=%d k=%d results=%d",
            len(query),
            retrieval_k,
            len(retrieval_results),
        )

        return retrieval_results

    def get_collection_count(self) -> int:
        if self._chroma_client is None:
            return 0

        try:
            collection = self._chroma_client.get_collection(
                name=self._collection_name
            )
            return collection.count()
        except Exception:
            return 0
