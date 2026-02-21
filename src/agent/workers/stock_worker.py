from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from langchain.tools import tool

from src.agent.workers.base import BaseWorkerFactory, WorkerConfig
from src.config import Settings
from src.tools.stock.tool import get_stock_price

if TYPE_CHECKING:
    from src.observability.prompts import PromptManager


logger = logging.getLogger(__name__)

STOCK_WORKER_PROMPT = """You are a stock price specialist for VeraMoney. Return structured data for the supervisor to synthesize.

<instructions>
1. Extract ticker symbol from request (resolve company names to tickers)
2. Call get_stock_price with the ticker
3. Return a structured response with price data
</instructions>

<output_format>
Ticker: [SYMBOL]
Price: $[PRICE]
Change: $[CHANGE] ([CHANGE_PERCENT]%)
</output_format>

<error_handling>
- Invalid ticker: Return "Unable to find ticker '[input]'. Common tickers: AAPL, MSFT, GOOGL, TSLA"
- API error: Return "Stock data temporarily unavailable for [ticker]."
</error_handling>

<company_to_ticker>
Apple → AAPL | Microsoft → MSFT | Google → GOOGL | Tesla → TSLA
Amazon → AMZN | Meta → META | Netflix → NFLX | NVIDIA → NVDA
</company_to_ticker>

<examples>
Input: "What's [COMPANY_NAME] stock at?"
→ Call get_stock_price("[TICKER]")
→ Return: "Ticker: [TICKER] | Price: $[PRICE] | Change: $[CHANGE] ([CHANGE_PERCENT]%)"

Input: "[COMPANY_NAME] price"
→ Call get_stock_price("[TICKER]")
→ Return: "Ticker: [TICKER] | Price: $[PRICE] | Change: $[CHANGE] ([CHANGE_PERCENT]%)"

Input: "[TICKER]"
→ Call get_stock_price("[TICKER]")
→ Return: "Ticker: [TICKER] | Price: $[PRICE] | Change: $[CHANGE] ([CHANGE_PERCENT]%)"
</examples>

Current date: {{current_date}}"""


def create_stock_worker(
    settings: Settings | None = None,
    prompt_manager: PromptManager | None = None,
):
    factory = BaseWorkerFactory(settings=settings, prompt_manager=prompt_manager)
    config = WorkerConfig(
        name="stock",
        model=settings.worker_model if settings else "gpt-5-nano-2025-08-07",
        tool=get_stock_price,
        prompt=STOCK_WORKER_PROMPT,
        description="Route stock price questions to the stock specialist. Use for: stock prices, market data, ticker quotes",
    )
    return factory.create_worker(config)


def build_ask_stock_agent_tool(
    settings: Settings | None = None,
    prompt_manager: PromptManager | None = None,
):
    stock_worker = create_stock_worker(settings=settings, prompt_manager=prompt_manager)

    recursion_limit = (settings.worker_max_iterations * 2) + 1 if settings else 5

    @tool
    async def ask_stock_agent(request: str) -> str:
        """Route stock price questions to the stock specialist. Use for: stock prices, market data, ticker quotes."""
        try:
            result = await stock_worker.ainvoke(
                {"messages": [{"role": "user", "content": request}]},
                {"recursion_limit": recursion_limit},
            )
            messages = result.get("messages", [])
            if not messages:
                return "I couldn't retrieve stock information right now. Please try again."
            return messages[-1].content
        except Exception:
            logger.exception("stock_worker_error request=%s", request[:50])
            return "I encountered an issue processing your stock request. Please try again."

    return ask_stock_agent
