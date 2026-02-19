from datetime import UTC, datetime

import httpx
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

from src.config import settings


FINNHUB_BASE_URL = "https://finnhub.io/api/v1"
DEFAULT_TIMEOUT_SECONDS = 10.0
MAX_RETRIES = 3
INITIAL_RETRY_DELAY_SECONDS = 1.0


class FinnhubApiError(Exception):
    pass


class InvalidSymbolError(FinnhubApiError):
    pass


class FinnhubClient:
    def __init__(
        self,
        api_key: str | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._api_key = api_key or settings.finnhub_api_key
        self._timeout_seconds = timeout_seconds
        self._headers = {
            "X-Finnhub-Token": self._api_key or "",
            "Accept": "application/json",
        }

    @property
    def is_configured(self) -> bool:
        has_api_key = self._api_key is not None and len(self._api_key) > 0
        return has_api_key

    async def _make_request(self, endpoint: str, params: dict[str, str]) -> dict:
        url = f"{FINNHUB_BASE_URL}{endpoint}"

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

    async def get_quote(self, ticker: str) -> dict:
        if not self.is_configured:
            raise ValueError("Finnhub API key is not configured")

        normalized_ticker = ticker.strip().upper()
        request_params = {"symbol": normalized_ticker}

        response_data = await self._make_request("/quote", request_params)

        current_price = response_data.get("c", 0)
        is_no_price_data = current_price == 0
        if is_no_price_data:
            raise InvalidSymbolError(f"No quote data available for '{normalized_ticker}'")

        timestamp_seconds = response_data.get("t", 0)
        is_valid_timestamp = timestamp_seconds > 0
        if is_valid_timestamp:
            quote_datetime = datetime.fromtimestamp(timestamp_seconds, tz=UTC)
            iso_timestamp = quote_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            iso_timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        return {
            "ticker": normalized_ticker,
            "price": current_price,
            "previous_close": response_data.get("pc", current_price),
            "timestamp": iso_timestamp,
        }
