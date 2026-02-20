TOOL_WEATHER = "get_weather"
TOOL_STOCK = "get_stock_price"
TOOL_KNOWLEDGE = "search_knowledge"

ALL_TOOLS = [TOOL_WEATHER, TOOL_STOCK, TOOL_KNOWLEDGE]

TOOL_SERVICE_NAMES: dict[str, str] = {
    TOOL_WEATHER: "weather data",
    TOOL_STOCK: "stock market data",
    TOOL_KNOWLEDGE: "knowledge base",
}
