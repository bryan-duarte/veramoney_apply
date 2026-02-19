import httpx
from langchain.tools import tool

from src.tools.weather.client import (
    CityNotFoundError,
    InvalidAPIKeyError,
    QuotaExceededError,
    WeatherAPIClient,
)
from src.tools.weather.schemas import WeatherInput, WeatherOutput


async def _fetch_weather_data(
    city_name: str, country_code: str | None
) -> WeatherOutput:
    weather_client = WeatherAPIClient()
    return await weather_client.get_current_weather(city_name, country_code)


@tool(args_schema=WeatherInput)
async def get_weather(city_name: str, country_code: str | None = None) -> str:
    """Get current weather information for a city. Returns temperature, humidity, conditions, and wind speed."""
    weather_client = WeatherAPIClient()

    is_client_not_configured = not weather_client.is_configured
    if is_client_not_configured:
        return '{"error": "Weather tool is not configured. Please set WEATHERAPI_KEY environment variable."}'

    try:
        weather_output = await _fetch_weather_data(city_name, country_code)
        return weather_output.model_dump_json()
    except CityNotFoundError:
        formatted_query = f"{city_name}, {country_code}" if country_code else city_name
        return f'{{"error": "City \'{formatted_query}\' not found."}}'
    except InvalidAPIKeyError:
        return '{"error": "Invalid WeatherAPI.com API key."}'
    except QuotaExceededError:
        return '{"error": "WeatherAPI.com quota exceeded. Please try again later."}'
    except httpx.HTTPStatusError as http_error:
        status_code = http_error.response.status_code if http_error.response else 500
        return f'{{"error": "Weather service error: {status_code}"}}'
    except Exception:
        return '{"error": "Failed to retrieve weather data."}'
