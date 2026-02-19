from pydantic import BaseModel, Field


class WeatherInput(BaseModel):
    city_name: str = Field(description="Name of the city to get weather for")
    country_code: str | None = Field(
        default=None,
        description="ISO 3166 country code to disambiguate city names",
    )


class WeatherAPICondition(BaseModel):
    text: str = Field(description="Weather condition text")
    code: int = Field(description="Weather condition code")


class WeatherAPILocation(BaseModel):
    name: str = Field(description="Location name")
    region: str = Field(description="Region or state")
    country: str = Field(description="Country name")
    lat: float = Field(description="Latitude")
    lon: float = Field(description="Longitude")
    localtime_epoch: int = Field(description="Local time as unix timestamp")


class WeatherAPICurrent(BaseModel):
    last_updated_epoch: int = Field(description="Last update time as unix timestamp")
    temp_c: float = Field(description="Temperature in Celsius")
    feelslike_c: float = Field(description="Feels-like temperature in Celsius")
    humidity: int = Field(description="Relative humidity percentage")
    pressure_mb: float = Field(description="Pressure in millibars")
    wind_kph: float = Field(description="Wind speed in kilometers per hour")
    wind_degree: int = Field(description="Wind direction in degrees")
    cloud: int = Field(description="Cloud cover percentage")
    vis_km: float = Field(description="Visibility in kilometers")
    condition: WeatherAPICondition = Field(description="Weather condition")


class WeatherAPIResponse(BaseModel):
    location: WeatherAPILocation = Field(description="Location information")
    current: WeatherAPICurrent = Field(description="Current weather data")


class WeatherAPIError(BaseModel):
    error: dict = Field(description="Error details from WeatherAPI.com")


class WeatherOutput(BaseModel):
    city: str = Field(description="Name of the city")
    country: str = Field(description="Country name")
    region: str = Field(description="Region or state")
    temperature_celsius: float = Field(description="Current temperature in Celsius")
    feels_like_celsius: float = Field(description="Feels-like temperature in Celsius")
    humidity_percent: int = Field(description="Relative humidity percentage")
    conditions: str = Field(description="Weather conditions description")
    wind_speed_kph: float = Field(description="Wind speed in kilometers per hour")
    visibility_km: float = Field(description="Visibility in kilometers")
    timestamp: int = Field(description="Unix timestamp of the weather data")
