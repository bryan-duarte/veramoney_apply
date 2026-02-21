import httpx
from langchain.tools import tool

from src.tools.weather.client import (
    CityNotFoundError,
    InvalidAPIKeyError,
    QuotaExceededError,
    WeatherAPIClient,
)
from src.tools.weather.schemas import WeatherError, WeatherInput, WeatherOutput


_shared_weather_client = WeatherAPIClient()


async def _fetch_weather_data(
    city_name: str, country_code: str | None
) -> WeatherOutput:
    return await _shared_weather_client.get_current_weather(city_name, country_code)


def get_shared_weather_client() -> WeatherAPIClient:
    return _shared_weather_client


@tool(args_schema=WeatherInput)
async def get_weather(city_name: str, country_code: str | None = None) -> str:  # noqa: PLR0911
    """Get current weather information for a city. Returns temperature, humidity, conditions, and wind speed."""
    is_client_not_configured = not _shared_weather_client.is_configured
    if is_client_not_configured:
        return WeatherError(error="Weather tool is not configured. Please set WEATHERAPI_KEY environment variable.").model_dump_json()

    try:
        weather_output = await _fetch_weather_data(city_name, country_code)
        return weather_output.model_dump_json()
    except CityNotFoundError:
        formatted_query = f"{city_name}, {country_code}" if country_code else city_name
        return WeatherError(error=f"City '{formatted_query}' not found.").model_dump_json()
    except InvalidAPIKeyError:
        return WeatherError(error="Invalid WeatherAPI.com API key.", code="INVALID_KEY").model_dump_json()
    except QuotaExceededError:
        return WeatherError(error="WeatherAPI.com quota exceeded. Please try again later.", code="QUOTA_EXCEEDED").model_dump_json()
    except httpx.HTTPStatusError as http_error:
        status_code = http_error.response.status_code if http_error.response else 500
        return WeatherError(error=f"Weather service error: {status_code}", code="HTTP_ERROR").model_dump_json()
    except Exception:
        return WeatherError(error="Failed to retrieve weather data.").model_dump_json()
