import json
import logging

from langchain.tools import tool

from src.config.settings import settings
from src.rag.schemas import RetrievalResult
from src.tools.knowledge.client import get_knowledge_client, is_knowledge_client_configured
from src.tools.knowledge.schemas import (
    KnowledgeInput,
    KnowledgeOutput,
    KnowledgeError,
    RetrievedChunkOutput,
)

logger = logging.getLogger(__name__)


@tool(args_schema=KnowledgeInput)
async def search_knowledge(query: str, document_type: str | None = None) -> str:
    """Search the VeraMoney knowledge base for information about company history, Uruguayan fintech regulation, and banking regulation. Use this tool when the user asks about VeraMoney's background, financial regulations in Uruguay, or compliance requirements. Returns relevant document chunks with source citations."""
    is_client_not_configured = not is_knowledge_client_configured()

    if is_client_not_configured:
        error_output = KnowledgeError(
            error="Knowledge base is not available. Please try again later."
        )
        return error_output.model_dump_json()

    try:
        knowledge_output = await _search_knowledge_base(query, document_type)
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


async def _search_knowledge_base(
    query: str,
    document_type: str | None,
) -> KnowledgeOutput:
    retriever = get_knowledge_client()

    retrieval_results = await retriever.search(
        query=query,
        document_type=document_type,
        k=settings.rag_retrieval_k if hasattr(settings, "rag_retrieval_k") else 4,
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
