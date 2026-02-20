import logging

from langchain.tools import tool

from src.agent.workers.base import BaseWorkerFactory, WorkerConfig
from src.config import Settings
from src.tools.stock.tool import get_stock_price


logger = logging.getLogger(__name__)

STOCK_WORKER_PROMPT = """You are a stock price specialist for VeraMoney.

Your only tool is get_stock_price. Use it to:
- Get current stock prices by ticker symbol
- Handle company name to ticker resolution

Always:
- Parse ticker symbols from company names
- Include price, change, and percentage
- Be concise and accurate

Current date: {{current_date}}"""


def create_stock_worker(settings: Settings | None = None):
    factory = BaseWorkerFactory(settings=settings)
    config = WorkerConfig(
        name="stock",
        model=settings.worker_model if settings else "gpt-5-nano-2025-08-07",
        tool=get_stock_price,
        prompt=STOCK_WORKER_PROMPT,
        description="Route stock price questions to the stock specialist. Use for: stock prices, market data, ticker quotes",
    )
    return factory.create_worker(config)


def build_ask_stock_agent_tool(settings: Settings | None = None):
    stock_worker = create_stock_worker(settings=settings)

    @tool
    async def ask_stock_agent(request: str) -> str:
        """Route stock price questions to the stock specialist. Use for: stock prices, market data, ticker quotes."""
        try:
            result = await stock_worker.ainvoke(
                {"messages": [{"role": "user", "content": request}]}
            )
            messages = result.get("messages", [])
            if not messages:
                return "I couldn't retrieve stock information right now. Please try again."
            return messages[-1].content
        except Exception:
            logger.exception("stock_worker_error request=%s", request[:50])
            return "I encountered an issue processing your stock request. Please try again."

    return ask_stock_agent
