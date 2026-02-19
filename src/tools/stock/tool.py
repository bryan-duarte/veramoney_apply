import httpx
from langchain.tools import tool

from src.tools.stock.client import FinnhubClient, InvalidSymbolError
from src.tools.stock.schemas import StockInput, StockOutput


async def _fetch_stock_data(ticker: str) -> StockOutput:
    finnhub_client = FinnhubClient()
    quote_data = await finnhub_client.get_quote(ticker)

    price = quote_data["price"]
    previous_close = quote_data["previous_close"]
    change_value = price - previous_close
    change_percent_value = (change_value / previous_close) * 100

    is_positive_change = change_value >= 0
    change = f"+{change_value:.2f}" if is_positive_change else f"{change_value:.2f}"
    change_percent = (
        f"+{change_percent_value:.2f}%"
        if is_positive_change
        else f"{change_percent_value:.2f}%"
    )

    return StockOutput(
        ticker=quote_data["ticker"],
        price=price,
        currency="USD",
        timestamp=quote_data["timestamp"],
        change=change,
        change_percent=change_percent,
    )


@tool(args_schema=StockInput)
async def get_stock_price(ticker: str) -> str:
    """Get current stock price for a ticker symbol. Returns price in USD, change from previous close, and timestamp."""
    finnhub_client = FinnhubClient()

    is_client_not_configured = not finnhub_client.is_configured
    if is_client_not_configured:
        return '{"error": "Stock tool not configured. Set FINNHUB_API_KEY environment variable."}'

    try:
        stock_output = await _fetch_stock_data(ticker)
        return stock_output.model_dump_json()
    except InvalidSymbolError:
        return f'{{"error": "Invalid ticker: {ticker}"}}'
    except httpx.HTTPStatusError as http_error:
        status_code = http_error.response.status_code
        return f'{{"error": "Stock service error: {status_code}"}}'
    except httpx.TimeoutException:
        return '{"error": "Stock service unavailable. Please try again."}'
    except Exception:
        return '{"error": "Failed to retrieve stock data."}'
