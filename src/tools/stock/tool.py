import httpx
from langchain.tools import tool

from src.tools.stock.client import AlpacaMarketDataClient, InvalidTickerSymbolError
from src.tools.stock.schemas import StockInput, StockOutput


async def _fetch_stock_data(ticker: str) -> StockOutput:
    alpaca_client = AlpacaMarketDataClient()
    snapshot_data = await alpaca_client.get_snapshot(ticker)

    price = snapshot_data["price"]
    previous_close = snapshot_data["previous_close"]
    change_value = price - previous_close
    change_percent_value = (change_value / previous_close) * 100

    is_positive_change = change_value >= 0
    change = f"+{change_value:.2f}" if is_positive_change else f"{change_value:.2f}"
    change_percent = f"+{change_percent_value:.2f}%" if is_positive_change else f"{change_percent_value:.2f}%"

    return StockOutput(
        ticker=snapshot_data["ticker"],
        price=price,
        currency="USD",
        timestamp=snapshot_data["timestamp"],
        change=change,
        change_percent=change_percent,
    )


@tool(args_schema=StockInput)
async def get_stock_price(ticker: str) -> str:
    """Get current stock price for a ticker symbol. Returns price in USD, change from previous close, and timestamp."""
    alpaca_client = AlpacaMarketDataClient()

    is_client_not_configured = not alpaca_client.is_configured
    if is_client_not_configured:
        return '{"error": "Stock tool not configured. Set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables."}'

    try:
        stock_output = await _fetch_stock_data(ticker)
        return stock_output.model_dump_json()
    except InvalidTickerSymbolError:
        return f'{{"error": "Invalid ticker: {ticker}"}}'
    except httpx.HTTPStatusError as http_error:
        status_code = http_error.response.status_code
        return f'{{"error": "Stock service error: {status_code}"}}'
    except httpx.TimeoutException:
        return '{"error": "Stock service unavailable. Please try again."}'
    except Exception:
        return '{"error": "Failed to retrieve stock data."}'
