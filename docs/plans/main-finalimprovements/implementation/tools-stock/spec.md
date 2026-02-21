# Tools - Stock Client Implementation

## Overview

Fix division by zero bug (C3) and implement HTTP connection pooling (H6) in the stock client.

## Files to Modify

- `src/tools/stock/client.py` - Division by zero fix + connection pooling
- `src/tools/stock/schemas.py` - Update change_percent type

## Implementation Guidelines

### Division by Zero Fix (C3)

**Location**: `src/tools/stock/client.py` - `get_quote()` method

**Current Code** (problematic):
```python
change_percent_value = (change_value / previous_close) * 100
```

**Fix**:
```python
is_previous_close_zero = previous_close == 0
change_percent_value = (change_value / previous_close) * 100 if not is_previous_close_zero else 0.0
```

### Connection Pooling (H6)

**Location**: `src/tools/stock/client.py` - `FinnhubClient` class

**Add class variables**:
```python
class FinnhubClient:
    BASE_URL: str = "https://finnhub.io/api/v1"
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
            base_url=self.BASE_URL,
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
async def _make_request(self, endpoint: str, params: dict[str, str]) -> dict:
    client = await self._get_client()
    url = f"{self.BASE_URL}{endpoint}"

    async for attempt in AsyncRetrying(...):
        with attempt:
            response = await client.get(url, params=params, headers=self._headers)
            response.raise_for_status()
            return response.json()
```

### Schema Update

**Location**: `src/tools/stock/schemas.py`

**Current**:
```python
change_percent: str    # e.g., "+1.32%", "-0.85%"
```

**Fix**:
```python
change_percent: float  # e.g., 1.32, -0.85. Returns 0.0 when previous_close is 0
```

**Note**: This is a breaking change for consumers expecting string format. The tool function that creates the JSON response will need to format this appropriately.

## Dependencies

- `httpx` (already installed)
- `asyncio` (stdlib)

## Integration Notes

- Client cleanup must be registered in FastAPI lifespan (`src/api/app.py`)
- Tool functions (`src/tools/stock/tool.py`) may need updates for new client interface
