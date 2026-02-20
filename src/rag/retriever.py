import logging

from src.rag.schemas import DocumentType, RetrievalResult
from src.rag.vectorstore import ChromaVectorStoreManager


logger = logging.getLogger(__name__)


class KnowledgeRetriever:
    def __init__(
        self,
        vector_store_manager: ChromaVectorStoreManager,
        default_k: int = 4,
    ):
        self._vector_store_manager = vector_store_manager
        self._default_k = default_k

    async def search(
        self,
        query: str,
        document_type: str | None = None,
        k: int | None = None,
    ) -> list[RetrievalResult]:
        retrieval_k = k if k is not None else self._default_k

        filter_metadata = _build_metadata_filter(document_type)

        results = await self._vector_store_manager.similarity_search(
            query=query,
            k=retrieval_k,
            filter_metadata=filter_metadata,
        )

        if not results and filter_metadata is not None:
            logger.info(
                "retriever_fallback_no_results query=%s document_type=%s",
                query[:50],
                document_type,
            )

            results = await self._vector_store_manager.similarity_search(
                query=query,
                k=retrieval_k,
                filter_metadata=None,
            )

        logger.info(
            "retriever_search query=%s document_type=%s k=%d results=%d",
            query[:50],
            document_type,
            retrieval_k,
            len(results),
        )

        return results


def _build_metadata_filter(document_type: str | None) -> dict[str, str] | None:
    if document_type is None:
        return None

    valid_types = {
        DocumentType.VERA_HISTORY.value,
        DocumentType.FINTEC_REGULATION.value,
        DocumentType.BANK_REGULATION.value,
    }

    is_valid_document_type = document_type in valid_types

    if not is_valid_document_type:
        logger.warning(
            "retriever_invalid_document_type document_type=%s",
            document_type,
        )
        return None

    return {"document_type": document_type}
