import httpx
from langchain.tools import tool

from src.tools.weather.client import CityNotFoundError, OpenWeatherClient
from src.tools.weather.schemas import WeatherInput, WeatherOutput


async def _fetch_weather_data(
    city_name: str, country_code: str | None
) -> WeatherOutput:
    weather_client = OpenWeatherClient()

    location = await weather_client.geocode_city(city_name, country_code)
    weather = await weather_client.get_current_weather(
        location.latitude, location.longitude
    )

    conditions_description = (
        ", ".join(condition.description for condition in weather.conditions)
        or "Unknown"
    )

    return WeatherOutput(
        city=location.city_name,
        country=location.country_code,
        temperature_celsius=weather.temperature_celsius,
        feels_like_celsius=weather.feels_like_celsius,
        humidity_percent=weather.humidity_percent,
        conditions=conditions_description,
        wind_speed_ms=weather.wind_speed_ms,
        visibility_km=weather.visibility_meters / 1000,
        timestamp=weather.timestamp,
    )


@tool(args_schema=WeatherInput)
async def get_weather(city_name: str, country_code: str | None = None) -> str:
    """Get current weather information for a city. Returns temperature, humidity, conditions, and wind speed."""
    weather_client = OpenWeatherClient()

    is_client_not_configured = not weather_client.is_configured
    if is_client_not_configured:
        return '{"error": "Weather tool is not configured. Please set OPENWEATHER_API_KEY environment variable."}'

    try:
        weather_output = await _fetch_weather_data(city_name, country_code)
        return weather_output.model_dump_json()
    except CityNotFoundError:
        formatted_query = f"{city_name}, {country_code}" if country_code else city_name
        return f'{{"error": "City \'{formatted_query}\' not found."}}'
    except httpx.HTTPStatusError as http_error:
        status_code = http_error.response.status_code
        return f'{{"error": "Weather service error: {status_code}"}}'
    except Exception:
        return '{"error": "Failed to retrieve weather data."}'
