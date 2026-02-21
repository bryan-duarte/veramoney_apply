# Tools - Weather Client Implementation

## Overview

Implement HTTP connection pooling (H5), fix HTTPS (L6), and use Pydantic error schemas (L5).

## Files to Modify

- `src/tools/weather/client.py` - Connection pooling + HTTPS fix
- `src/tools/weather/tool.py` - Use Pydantic error schemas
- `src/tools/weather/schemas.py` - Add WeatherError model

## Implementation Guidelines

### Connection Pooling (H5)

**Location**: `src/tools/weather/client.py` - `WeatherAPIClient` class

**Add class variables**:
```python
class WeatherAPIClient:
    BASE_URL: str = "https://api.weatherapi.com/v1/current.json"  # Changed from http
    DEFAULT_TIMEOUT_SECONDS: float = 10.0
    MAX_RETRIES: int = 3
    INITIAL_RETRY_DELAY_SECONDS: float = 0.5

    _client: httpx.AsyncClient | None = None
    _lock: asyncio.Lock = asyncio.Lock()
```

**Add lazy client getter**:
```python
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
                max_connections=100,
                max_keepalive_connections=20,
            ),
            http2=True,
        )
    return self._client
```

**Add cleanup method**:
```python
async def aclose(self) -> None:
    async with self._lock:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
```

**Update _make_request**:
```python
async def _make_request(self, url: str, params: dict[str, str]) -> dict:
    client = await self._get_client()

    async for attempt in AsyncRetrying(...):
        with attempt:
            response = await client.get(url, params=params, headers=self._base_headers)
            response.raise_for_status()
            return response.json()
```

### HTTPS Fix (L6)

**Current**:
```python
BASE_URL: str = "http://api.weatherapi.com/v1/current.json"
```

**Fix**:
```python
BASE_URL: str = "https://api.weatherapi.com/v1/current.json"
```

### Error Schema (L5)

**Location**: `src/tools/weather/schemas.py`

**Add error model**:
```python
class WeatherError(BaseModel):
    error: str
    code: str | None = None
```

**Location**: `src/tools/weather/tool.py`

**Update error returns**:
```python
# Before
return '{"error": "Weather tool is not configured..."}'

# After
from src.tools.weather.schemas import WeatherError

error_output = WeatherError(error="Weather tool is not configured...")
return error_output.model_dump_json()
```

Apply this pattern to all error returns in the tool function.

## Dependencies

- `httpx` (already installed)
- `asyncio` (stdlib)

## Integration Notes

- Client cleanup must be registered in FastAPI lifespan
- Note: API key in URL (M5) is kept as-is per user decision (API limitation)
