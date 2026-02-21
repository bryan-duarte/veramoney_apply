import asyncio

import httpx
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

from src.config import settings
from src.tools.weather.schemas import WeatherAPIResponse, WeatherOutput


class CityNotFoundError(Exception):
    pass


class InvalidAPIKeyError(Exception):
    pass


class QuotaExceededError(Exception):
    pass


class WeatherAPIClient:
    BASE_URL: str = "https://api.weatherapi.com/v1/current.json"
    DEFAULT_TIMEOUT_SECONDS: float = 10.0
    MAX_RETRIES: int = 3
    INITIAL_RETRY_DELAY_SECONDS: float = 1.0
    ERROR_LOCATION_NOT_FOUND: int = 1006
    ERROR_INVALID_API_KEY: int = 2006
    ERROR_QUOTA_EXCEEDED: int = 2007
    MAX_CONNECTIONS: int = 100
    MAX_KEEPALIVE_CONNECTIONS: int = 20

    def __init__(
        self,
        api_key: str | None = None,
        timeout_seconds: float | None = None,
    ):
        self._api_key = api_key or settings.weatherapi_key
        self._timeout_seconds = timeout_seconds if timeout_seconds is not None else self.DEFAULT_TIMEOUT_SECONDS
        self._base_headers = {"Accept": "application/json"}
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

    async def _make_request(
        self, url: str, params: dict[str, str]
    ) -> dict:
        client = await self._get_client()

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.MAX_RETRIES),
            wait=wait_exponential(multiplier=self.INITIAL_RETRY_DELAY_SECONDS),
            retry=lambda exc: isinstance(exc, httpx.TimeoutException),
            reraise=True,
        ):
            with attempt:
                response = await client.get(
                    url, params=params, headers=self._base_headers
                )
                response.raise_for_status()
                return response.json()
        raise httpx.TimeoutException("Max retries exceeded")

    def _build_location_query(self, city_name: str, country_code: str | None) -> str:
        has_country_code = country_code is not None and len(country_code) > 0
        if has_country_code:
            return f"{city_name},{country_code}"
        return city_name

    def _check_api_error(self, response_data: dict) -> None:
        has_error = "error" in response_data
        if not has_error:
            return

        error_info = response_data.get("error", {})
        error_code = error_info.get("code")

        is_location_not_found = error_code == self.ERROR_LOCATION_NOT_FOUND
        is_invalid_api_key = error_code == self.ERROR_INVALID_API_KEY
        is_quota_exceeded = error_code == self.ERROR_QUOTA_EXCEEDED

        if is_location_not_found:
            raise CityNotFoundError(error_info.get("message", "Location not found"))
        if is_invalid_api_key:
            raise InvalidAPIKeyError("Invalid WeatherAPI.com API key")
        if is_quota_exceeded:
            raise QuotaExceededError("WeatherAPI.com quota exceeded")

        raise httpx.HTTPStatusError(
            f"WeatherAPI error: {error_info.get('message', 'Unknown error')}",
            request=None,
            response=None,
        )

    async def get_current_weather(
        self, city_name: str, country_code: str | None = None
    ) -> WeatherOutput:
        if not self.is_configured:
            raise ValueError("WeatherAPI.com API key is not configured")

        location_query = self._build_location_query(city_name, country_code)
        request_params = {
            "key": self._api_key,
            "q": location_query,
            "aqi": "no",
        }

        response_data = await self._make_request(self.BASE_URL, request_params)

        self._check_api_error(response_data)

        weather_response = WeatherAPIResponse.model_validate(response_data)

        return WeatherOutput(
            city=weather_response.location.name,
            country=weather_response.location.country,
            region=weather_response.location.region,
            temperature_celsius=weather_response.current.temp_c,
            feels_like_celsius=weather_response.current.feelslike_c,
            humidity_percent=weather_response.current.humidity,
            conditions=weather_response.current.condition.text,
            wind_speed_kph=weather_response.current.wind_kph,
            visibility_km=weather_response.current.vis_km,
            timestamp=weather_response.current.last_updated_epoch,
        )
