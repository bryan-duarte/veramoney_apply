import logging

from langchain.tools import tool
from langchain_core.tools import BaseTool

from src.config.settings import settings
from src.rag.retriever import KnowledgeRetriever
from src.rag.schemas import RetrievalResult
from src.tools.knowledge.schemas import (
    KnowledgeError,
    KnowledgeInput,
    KnowledgeOutput,
    RetrievedChunkOutput,
)


logger = logging.getLogger(__name__)


def create_knowledge_tool(retriever: KnowledgeRetriever | None) -> BaseTool:
    @tool(args_schema=KnowledgeInput)
    async def search_knowledge(query: str, document_type: str | None = None) -> str:
        """Search the VeraMoney knowledge base. ALWAYS specify document_type to target the right collection:
- document_type='vera_history' for VeraMoney company history, founding, milestones, products, leadership
- document_type='fintec_regulation' for Uruguayan fintech regulations and compliance
- document_type='bank_regulation' for Uruguayan banking regulations and compliance
Make ONE targeted call with the correct document_type. Do NOT call this tool multiple times for different document types."""
        is_retriever_not_available = retriever is None

        if is_retriever_not_available:
            error_output = KnowledgeError(
                error="Knowledge base is not available. Please try again later."
            )
            return error_output.model_dump_json()

        try:
            knowledge_output = await _search_knowledge_base(query, document_type, retriever)
            return knowledge_output.model_dump_json()

        except Exception as error:
            logger.exception(
                "knowledge_tool_error query=%s error=%s",
                query[:50],
                str(error),
            )
            error_output = KnowledgeError(
                error="Failed to search the knowledge base. Please try again."
            )
            return error_output.model_dump_json()

    return search_knowledge


async def _search_knowledge_base(
    query: str,
    document_type: str | None,
    retriever: KnowledgeRetriever,
) -> KnowledgeOutput:
    retrieval_results = await retriever.search(
        query=query,
        document_type=document_type,
        k=settings.rag_retrieval_k,
    )

    chunk_outputs = [
        _convert_retrieval_result_to_output(result)
        for result in retrieval_results
    ]

    return KnowledgeOutput(
        query=query,
        chunks=chunk_outputs,
        total_results=len(chunk_outputs),
    )


def _convert_retrieval_result_to_output(
    result: RetrievalResult,
) -> RetrievedChunkOutput:
    return RetrievedChunkOutput(
        content=result.content,
        document_title=result.metadata.document_title,
        document_type=result.metadata.document_type,
        page_number=result.metadata.page_number,
        relevance_score=result.relevance_score,
    )
