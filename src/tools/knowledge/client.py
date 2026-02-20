from src.rag.retriever import KnowledgeRetriever

_knowledge_retriever_instance: KnowledgeRetriever | None = None


def configure_knowledge_client(retriever: KnowledgeRetriever) -> None:
    global _knowledge_retriever_instance
    _knowledge_retriever_instance = retriever


def get_knowledge_client() -> KnowledgeRetriever:
    if _knowledge_retriever_instance is None:
        raise RuntimeError(
            "Knowledge client not configured. Call configure_knowledge_client() first."
        )
    return _knowledge_retriever_instance


def is_knowledge_client_configured() -> bool:
    return _knowledge_retriever_instance is not None
