from datetime import UTC, datetime

import httpx
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

from src.config import settings


ALPACA_DATA_BASE_URL = "https://data.alpaca.markets/v2"
ALPACA_SANDBOX_BASE_URL = "https://data.sandbox.alpaca.markets/v2"
DEFAULT_TIMEOUT_SECONDS = 10.0
MAX_RETRIES = 3
INITIAL_RETRY_DELAY_SECONDS = 1.0
NANOSECONDS_PER_SECOND = 1_000_000_000


class AlpacaMarketDataError(Exception):
    pass


class InvalidTickerSymbolError(AlpacaMarketDataError):
    pass


class AlpacaMarketDataClient:
    def __init__(
        self,
        api_key: str | None = None,
        secret_key: str | None = None,
        use_sandbox: bool | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._api_key = api_key or settings.alpaca_api_key
        self._secret_key = secret_key or settings.alpaca_secret_key
        self._use_sandbox = (
            use_sandbox if use_sandbox is not None else settings.alpaca_use_sandbox
        )
        self._timeout_seconds = timeout_seconds
        self._base_url = (
            ALPACA_SANDBOX_BASE_URL if self._use_sandbox else ALPACA_DATA_BASE_URL
        )
        self._headers = {
            "APCA-API-KEY-ID": self._api_key or "",
            "APCA-API-SECRET-KEY": self._secret_key or "",
            "Accept": "application/json",
        }

    @property
    def is_configured(self) -> bool:
        has_api_key = self._api_key is not None and len(self._api_key) > 0
        has_secret_key = self._secret_key is not None and len(self._secret_key) > 0
        return has_api_key and has_secret_key

    async def _make_request(self, endpoint: str, params: dict[str, str]) -> dict:
        url = f"{self._base_url}{endpoint}"

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(MAX_RETRIES),
            wait=wait_exponential(multiplier=INITIAL_RETRY_DELAY_SECONDS),
            retry=lambda exc: isinstance(exc, httpx.TimeoutException),
            reraise=True,
        ):
            with attempt:
                async with httpx.AsyncClient(
                    timeout=self._timeout_seconds
                ) as http_client:
                    response = await http_client.get(
                        url, params=params, headers=self._headers
                    )
                    response.raise_for_status()
                    return response.json()
        raise httpx.TimeoutException("Max retries exceeded")

    async def get_snapshot(self, ticker: str) -> dict:
        if not self.is_configured:
            raise ValueError("Alpaca API credentials are not configured")

        normalized_ticker = ticker.strip().upper()
        request_params = {"symbols": normalized_ticker}

        response_data = await self._make_request("/stocks/snapshots", request_params)

        is_ticker_not_in_response = normalized_ticker not in response_data
        if is_ticker_not_in_response:
            raise InvalidTickerSymbolError(f"Ticker '{normalized_ticker}' not found")

        ticker_data = response_data[normalized_ticker]
        is_missing_trade_data = (
            "latestTrade" not in ticker_data or ticker_data["latestTrade"] is None
        )
        if is_missing_trade_data:
            raise InvalidTickerSymbolError(
                f"No trade data available for '{normalized_ticker}'"
            )

        latest_trade = ticker_data["latestTrade"]
        previous_day_data = ticker_data.get("prevDay", {})

        is_missing_previous_close = "c" not in previous_day_data
        if is_missing_previous_close:
            raise InvalidTickerSymbolError(
                f"No previous close data for '{normalized_ticker}'"
            )

        timestamp_nanoseconds = latest_trade["t"]
        timestamp_seconds = timestamp_nanoseconds / NANOSECONDS_PER_SECOND
        trade_datetime = datetime.fromtimestamp(timestamp_seconds, tz=UTC)
        iso_timestamp = trade_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")

        return {
            "ticker": normalized_ticker,
            "price": latest_trade["p"],
            "previous_close": previous_day_data["c"],
            "timestamp": iso_timestamp,
        }
