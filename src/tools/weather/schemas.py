from pydantic import BaseModel, Field


class WeatherInput(BaseModel):
    city_name: str = Field(description="Name of the city to get weather for")
    country_code: str | None = Field(
        default=None,
        description="ISO 3166 country code to disambiguate city names",
    )


class GeoLocation(BaseModel):
    latitude: float = Field(description="Geographical latitude coordinate")
    longitude: float = Field(description="Geographical longitude coordinate")
    city_name: str = Field(description="Canonical name of the location")
    country_code: str = Field(description="ISO 3166 country code")


class WeatherCondition(BaseModel):
    condition_id: int = Field(description="Weather condition ID")
    main: str = Field(description="Group of weather parameters")
    description: str = Field(description="Detailed weather condition description")
    icon: str = Field(description="Weather icon code")


class CurrentWeatherData(BaseModel):
    timestamp: int = Field(description="Unix timestamp of the weather data")
    temperature_celsius: float = Field(description="Temperature in Celsius")
    feels_like_celsius: float = Field(description="Feels-like temperature in Celsius")
    humidity_percent: int = Field(description="Relative humidity percentage")
    pressure_hpa: int = Field(description="Atmospheric pressure in hPa")
    wind_speed_ms: float = Field(description="Wind speed in meters per second")
    wind_direction_deg: int = Field(description="Wind direction in degrees")
    cloudiness_percent: int = Field(description="Cloudiness percentage")
    visibility_meters: int = Field(description="Visibility in meters")
    conditions: list[WeatherCondition] = Field(description="List of weather conditions")


class WeatherOutput(BaseModel):
    city: str = Field(description="Name of the city")
    country: str = Field(description="Country code")
    temperature_celsius: float = Field(description="Current temperature in Celsius")
    feels_like_celsius: float = Field(description="Feels-like temperature in Celsius")
    humidity_percent: int = Field(description="Relative humidity percentage")
    conditions: str = Field(description="Weather conditions description")
    wind_speed_ms: float = Field(description="Wind speed in meters per second")
    visibility_km: float = Field(description="Visibility in kilometers")
    timestamp: int = Field(description="Unix timestamp of the weather data")
