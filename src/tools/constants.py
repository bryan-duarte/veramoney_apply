TOOL_WEATHER = "get_weather"
TOOL_STOCK = "get_stock_price"
TOOL_KNOWLEDGE = "search_knowledge"

TOOL_SERVICE_NAMES: dict[str, str] = {
    TOOL_WEATHER: "weather data",
    TOOL_STOCK: "stock market data",
    TOOL_KNOWLEDGE: "knowledge base",
}

ASK_WEATHER_AGENT = "ask_weather_agent"
ASK_STOCK_AGENT = "ask_stock_agent"
ASK_KNOWLEDGE_AGENT = "ask_knowledge_agent"

ALL_WORKER_TOOLS = [ASK_WEATHER_AGENT, ASK_STOCK_AGENT, ASK_KNOWLEDGE_AGENT]
