import httpx
from tenacity import AsyncRetrying, RetryError, stop_after_attempt, wait_exponential

from src.config import settings
from src.tools.weather.schemas import (
    CurrentWeatherData,
    GeoLocation,
    WeatherCondition,
)

OPENWEATHER_GEOCODING_BASE_URL = "http://api.openweathermap.org/geo/1.0/direct"
OPENWEATHER_ONECALL_BASE_URL = "https://api.openweathermap.org/data/3.0/onecall"
DEFAULT_TIMEOUT_SECONDS = 10.0
GEOCODING_RESULTS_LIMIT = 1
MAX_RETRIES = 3
INITIAL_RETRY_DELAY_SECONDS = 1.0


class CityNotFoundError(Exception):
    pass


class OpenWeatherClient:
    def __init__(self, api_key: str | None = None, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS):
        self._api_key = api_key or settings.openweather_api_key
        self._timeout_seconds = timeout_seconds
        self._base_headers = {"Accept": "application/json"}

    @property
    def is_configured(self) -> bool:
        return self._api_key is not None and len(self._api_key) > 0

    async def _make_request(self, url: str, params: dict[str, str | int]) -> dict | list:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(MAX_RETRIES),
            wait=wait_exponential(multiplier=INITIAL_RETRY_DELAY_SECONDS),
            retry=lambda exc: isinstance(exc, httpx.TimeoutException),
            reraise=True,
        ):
            with attempt:
                async with httpx.AsyncClient(timeout=self._timeout_seconds) as http_client:
                    response = await http_client.get(url, params=params, headers=self._base_headers)
                    response.raise_for_status()
                    return response.json()
        raise httpx.TimeoutException("Max retries exceeded")

    def _build_city_query(self, city_name: str, country_code: str | None) -> str:
        has_country_code = country_code is not None and len(country_code) > 0
        if has_country_code:
            return f"{city_name},{country_code}"
        return city_name

    async def geocode_city(self, city_name: str, country_code: str | None = None) -> GeoLocation:
        if not self.is_configured:
            raise ValueError("OpenWeatherMap API key is not configured")

        query = self._build_city_query(city_name, country_code)
        request_params = {
            "q": query,
            "limit": GEOCODING_RESULTS_LIMIT,
            "appid": self._api_key,
        }

        response_data = await self._make_request(OPENWEATHER_GEOCODING_BASE_URL, request_params)

        is_response_empty = not response_data or not isinstance(response_data, list)
        if is_response_empty:
            raise CityNotFoundError(f"City '{query}' not found")

        first_result = response_data[0]
        return GeoLocation(
            latitude=first_result["lat"],
            longitude=first_result["lon"],
            city_name=first_result["name"],
            country_code=first_result.get("country", ""),
        )

    async def get_current_weather(self, latitude: float, longitude: float) -> CurrentWeatherData:
        if not self.is_configured:
            raise ValueError("OpenWeatherMap API key is not configured")

        request_params = {
            "lat": latitude,
            "lon": longitude,
            "units": "metric",
            "exclude": "minutely,hourly,daily,alerts",
            "appid": self._api_key,
        }

        response_data = await self._make_request(OPENWEATHER_ONECALL_BASE_URL, request_params)
        current_data = response_data.get("current", {})

        weather_conditions = [
            WeatherCondition(
                condition_id=condition["id"],
                main=condition["main"],
                description=condition["description"],
                icon=condition["icon"],
            )
            for condition in current_data.get("weather", [])
        ]

        return CurrentWeatherData(
            timestamp=current_data.get("dt", 0),
            temperature_celsius=current_data.get("temp", 0.0),
            feels_like_celsius=current_data.get("feels_like", 0.0),
            humidity_percent=current_data.get("humidity", 0),
            pressure_hpa=current_data.get("pressure", 0),
            wind_speed_ms=current_data.get("wind_speed", 0.0),
            wind_direction_deg=current_data.get("wind_deg", 0),
            cloudiness_percent=current_data.get("clouds", 0),
            visibility_meters=current_data.get("visibility", 10000),
            conditions=weather_conditions,
        )
