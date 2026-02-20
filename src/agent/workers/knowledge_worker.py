import logging

from langchain.tools import tool

from src.agent.workers.base import BaseWorkerFactory, WorkerConfig
from src.config import Settings
from src.rag.retriever import KnowledgeRetriever
from src.tools.knowledge.tool import create_knowledge_tool


logger = logging.getLogger(__name__)

KNOWLEDGE_WORKER_PROMPT = """You are a knowledge base specialist for VeraMoney.

Your only tool is search_knowledge. Use it to:
- Search internal documents
- Find relevant information about VeraMoney, fintech, banking

Always:
- Cite document titles in your response
- Indicate if information is not in the knowledge base
- Be accurate and don't fabricate citations

Current date: {{current_date}}"""


def create_knowledge_worker(
    knowledge_retriever: KnowledgeRetriever | None = None,
    settings: Settings | None = None,
):
    factory = BaseWorkerFactory(settings=settings)
    knowledge_tool = create_knowledge_tool(knowledge_retriever)
    config = WorkerConfig(
        name="knowledge",
        model=settings.worker_model if settings else "gpt-5-nano-2025-08-07",
        tool=knowledge_tool,
        prompt=KNOWLEDGE_WORKER_PROMPT,
        description="Route knowledge base questions to the document specialist. Use for: VeraMoney history, fintech regulations, banking policies",
    )
    return factory.create_worker(config)


def build_ask_knowledge_agent_tool(
    knowledge_retriever: KnowledgeRetriever | None = None,
    settings: Settings | None = None,
):
    knowledge_worker = create_knowledge_worker(
        knowledge_retriever=knowledge_retriever,
        settings=settings,
    )

    @tool
    async def ask_knowledge_agent(request: str) -> str:
        """Route knowledge base questions to the document specialist. Use for: VeraMoney history, fintech regulations, banking policies."""
        try:
            result = await knowledge_worker.ainvoke(
                {"messages": [{"role": "user", "content": request}]}
            )
            messages = result.get("messages", [])
            if not messages:
                return "I couldn't retrieve knowledge base information right now. Please try again."
            return messages[-1].content
        except Exception:
            logger.exception("knowledge_worker_error request=%s", request[:50])
            return "I encountered an issue processing your knowledge request. Please try again."

    return ask_knowledge_agent
