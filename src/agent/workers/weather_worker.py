from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from langchain.tools import tool

from src.agent.workers.base import BaseWorkerFactory, WorkerConfig
from src.config import Settings
from src.tools.weather.tool import get_weather

if TYPE_CHECKING:
    from src.observability.prompts import PromptManager


logger = logging.getLogger(__name__)

WEATHER_WORKER_PROMPT = """You are a weather information specialist for VeraMoney.

Your only tool is get_weather. Use it to:
- Get current weather for any city
- Handle country code disambiguation when needed
- Report temperature in Celsius

Always:
- Parse location from natural language
- Include temperature and conditions
- Be concise and accurate

Current date: {{current_date}}"""


def create_weather_worker(
    settings: Settings | None = None,
    prompt_manager: PromptManager | None = None,
):
    factory = BaseWorkerFactory(settings=settings, prompt_manager=prompt_manager)
    config = WorkerConfig(
        name="weather",
        model=settings.worker_model if settings else "gpt-5-nano-2025-08-07",
        tool=get_weather,
        prompt=WEATHER_WORKER_PROMPT,
        description="Route weather-related questions to the weather specialist. Use for: current weather, temperature, conditions, forecasts",
    )
    return factory.create_worker(config)


def build_ask_weather_agent_tool(
    settings: Settings | None = None,
    prompt_manager: PromptManager | None = None,
):
    weather_worker = create_weather_worker(settings=settings, prompt_manager=prompt_manager)

    recursion_limit = (settings.worker_max_iterations * 2) + 1 if settings else 5

    @tool
    async def ask_weather_agent(request: str) -> str:
        """Route weather-related questions to the weather specialist. Use for: current weather, temperature, conditions, forecasts."""
        try:
            result = await weather_worker.ainvoke(
                {"messages": [{"role": "user", "content": request}]},
                {"recursion_limit": recursion_limit},
            )
            messages = result.get("messages", [])
            if not messages:
                return "I couldn't retrieve weather information right now. Please try again."
            return messages[-1].content
        except Exception:
            logger.exception("weather_worker_error request=%s", request[:50])
            return "I encountered an issue processing your weather request. Please try again."

    return ask_weather_agent
