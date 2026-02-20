import logging

from langchain.agents.middleware import AgentState, after_model
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langgraph.runtime import Runtime

from src.tools.constants import TOOL_KNOWLEDGE

from .utils import KnowledgeToolResult, parse_json_content


logger = logging.getLogger(__name__)


@after_model
async def knowledge_guardrails(state: AgentState, _runtime: Runtime) -> dict[str, str] | None:
    messages = state.get("messages", [])
    if not messages:
        return None

    last_message = messages[-1]
    if not isinstance(last_message, AIMessage):
        return None

    if not last_message.content:
        return None

    knowledge_tool_results = _extract_knowledge_tool_results(messages)

    if not knowledge_tool_results:
        return None

    response_content = last_message.content.lower()

    _check_citation_presence(response_content, knowledge_tool_results)
    _check_for_fabricated_citations(response_content, knowledge_tool_results)

    return None


def _extract_knowledge_tool_results(messages: list[BaseMessage]) -> list[KnowledgeToolResult]:
    results: list[KnowledgeToolResult] = []

    for message in messages:
        if isinstance(message, ToolMessage):
            tool_name = getattr(message, "name", None)
            if tool_name == TOOL_KNOWLEDGE:
                parsed_content = parse_json_content(message.content)
                if parsed_content is not None:
                    results.append(parsed_content)

    return results


def _check_citation_presence(response_content: str, tool_results: list[KnowledgeToolResult]) -> None:
    has_chunks = any(
        result.get("chunks") and len(result.get("chunks", [])) > 0
        for result in tool_results
    )

    if not has_chunks:
        return

    citation_indicators = [
        "source",
        "fuente",
        "according to",
        "según",
        "documento",
        "document",
        "page",
        "página",
    ]

    has_citation = any(indicator in response_content for indicator in citation_indicators)

    if not has_citation:
        logger.warning(
            "knowledge_guardrails_no_citation response_length=%d",
            len(response_content),
        )


def _check_for_fabricated_citations(response_content: str, tool_results: list[KnowledgeToolResult]) -> None:
    retrieved_titles = set()
    retrieved_pages = set()

    for result in tool_results:
        chunks = result.get("chunks", [])
        for chunk in chunks:
            document_title = chunk.get("document_title", "")
            page_number = chunk.get("page_number")

            if document_title:
                retrieved_titles.add(document_title.lower())
            if page_number is not None:
                retrieved_pages.add(page_number)

    mentioned_titles = _extract_document_titles_from_response(response_content)

    for mentioned_title in mentioned_titles:
        is_known_title = any(
            mentioned_title in known_title or known_title in mentioned_title
            for known_title in retrieved_titles
        )

        if not is_known_title and retrieved_titles:
            logger.warning(
                "knowledge_guardrails_potential_fabricated_title title=%s known_titles=%s",
                mentioned_title,
                list(retrieved_titles),
            )


def _extract_document_titles_from_response(response_content: str) -> list[str]:
    title_indicators = [
        "historia de veramoney",
        "regulacion fintech",
        "regulacion bancaria",
        "veramoney history",
        "fintech regulation",
        "banking regulation",
    ]

    return [indicator for indicator in title_indicators if indicator in response_content]
