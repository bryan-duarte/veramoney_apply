import asyncio
from datetime import UTC, datetime

import httpx
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

from src.config import settings


class InvalidSymbolError(Exception):
    pass


class FinnhubClient:
    BASE_URL: str = "https://finnhub.io/api/v1"
    DEFAULT_TIMEOUT_SECONDS: float = 10.0
    MAX_RETRIES: int = 3
    INITIAL_RETRY_DELAY_SECONDS: float = 1.0
    MAX_CONNECTIONS: int = 100
    MAX_KEEPALIVE_CONNECTIONS: int = 20

    def __init__(
        self,
        api_key: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self._api_key = api_key or settings.finnhub_api_key
        self._timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else self.DEFAULT_TIMEOUT_SECONDS
        )
        self._headers = {
            "X-Finnhub-Token": self._api_key or "",
            "Accept": "application/json",
        }
        self._client: httpx.AsyncClient | None = None
        self._lock = asyncio.Lock()

    @property
    def is_configured(self) -> bool:
        has_api_key = self._api_key is not None and len(self._api_key) > 0
        return has_api_key

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is not None:
            return self._client

        async with self._lock:
            if self._client is not None:
                return self._client

            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                timeout=httpx.Timeout(
                    connect=5.0,
                    read=self._timeout_seconds,
                    write=10.0,
                    pool=5.0,
                ),
                limits=httpx.Limits(
                    max_connections=self.MAX_CONNECTIONS,
                    max_keepalive_connections=self.MAX_KEEPALIVE_CONNECTIONS,
                ),
                http2=True,
            )
        return self._client

    async def aclose(self) -> None:
        async with self._lock:
            if self._client is not None:
                await self._client.aclose()
                self._client = None

    async def _make_request(self, endpoint: str, params: dict[str, str]) -> dict:
        client = await self._get_client()
        url = f"{self.BASE_URL}{endpoint}"

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.MAX_RETRIES),
            wait=wait_exponential(multiplier=self.INITIAL_RETRY_DELAY_SECONDS),
            retry=lambda exc: isinstance(exc, httpx.TimeoutException),
            reraise=True,
        ):
            with attempt:
                response = await client.get(
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
