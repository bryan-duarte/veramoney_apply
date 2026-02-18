# Stock Tool Implementation Specification

## Overview

Implement a LangChain-compatible stock price tool using Alpaca Market Data API. The tool retrieves the latest trade price and change from previous close for a given ticker symbol.

---

## Files to Create

| File | Purpose |
|------|---------|
| `src/tools/stock/schemas.py` | Pydantic models for input/output |
| `src/tools/stock/client.py` | Async Alpaca API client |
| `src/tools/stock/tool.py` | LangChain tool definition |
| `src/tools/stock/__init__.py` | Module exports |

## Files to Modify

| File | Changes |
|------|---------|
| `src/config/settings.py` | Add Alpaca API credentials |
| `.env.example` | Add Alpaca environment variables |

---

## Implementation Guidelines

### 1. Configuration Layer

**File:** `src/config/settings.py`

Add three new fields to the Settings class:

```
alpaca_api_key: str | None
    - description: "Alpaca API key ID for market data"
    - default: None

alpaca_secret_key: str | None
    - description: "Alpaca API secret key for market data"
    - default: None

alpaca_use_sandbox: bool
    - description: "Use Alpaca sandbox environment"
    - default: False
```

**File:** `.env.example`

Add:
```
ALPACA_API_KEY=
ALPACA_SECRET_KEY=
ALPACA_USE_SANDBOX=false
```

---

### 2. Schemas Module

**File:** `src/tools/stock/schemas.py`

**StockInput:**
- Extends BaseModel
- Fields:
  - ticker: str (min 1, max 5 chars, description: "Stock ticker symbol")
- Validator: normalize to uppercase, strip whitespace, validate pattern

**StockOutput:**
- Extends BaseModel
- Fields:
  - ticker: str (description: "Stock ticker symbol")
  - price: float (description: "Current stock price in USD")
  - currency: str (default "USD", description: "Currency code")
  - timestamp: str (description: "ISO 8601 timestamp of the trade")
  - change: str (description: "Price change from previous close with sign")
  - change_percent: str (description: "Percentage change from previous close with sign")

**Validation Logic:**
- Pattern: ^[A-Z]+$
- Use @field_validator decorator
- Raise ValueError with clear message

---

### 3. Client Module

**File:** `src/tools/stock/client.py`

**Constants:**
```
ALPACA_DATA_BASE_URL = "https://data.alpaca.markets/v2"
ALPACA_SANDBOX_BASE_URL = "https://data.sandbox.alpaca.markets/v2"
DEFAULT_TIMEOUT_SECONDS = 10.0
MAX_RETRIES = 3
INITIAL_RETRY_DELAY_SECONDS = 1.0
```

**Exceptions:**
```
class AlpacaMarketDataError(Exception):
    pass

class InvalidTickerSymbolError(AlpacaMarketDataError):
    pass
```

**AlpacaMarketDataClient Class:**

Constructor:
- Parameters: api_key, secret_key, use_sandbox, timeout_seconds
- All parameters optional (default to settings)
- Build headers dict with API credentials
- Select base URL based on sandbox flag

Properties:
- is_configured: bool (check both keys exist and non-empty)

Methods:
- _make_request(endpoint, params) -> dict
  - Async with httpx.AsyncClient
  - Retry on TimeoutException only
  - Exponential backoff
  - Raise HTTPStatusError immediately

- get_snapshot(ticker: str) -> dict
  - Normalize ticker (uppercase, strip)
  - Call /stocks/snapshots endpoint
  - Parse response for latestTrade and prevDay
  - Raise InvalidTickerSymbolError if not found
  - Return dict with ticker, price, previous_close, timestamp_nanoseconds

---

### 4. Tool Module

**File:** `src/tools/stock/tool.py`

**Helper Function:** `_fetch_stock_data(ticker: str) -> StockOutput`
- Create AlpacaMarketDataClient instance
- Call get_snapshot(ticker)
- Extract price from latestTrade.p
- Extract previous_close from prevDay.c
- Calculate change: price - previous_close
- Format change with sign (e.g., "+2.34", "-1.50")
- Calculate change_percent: (price - previous_close) / previous_close * 100
- Format change_percent with sign and % suffix (e.g., "+1.32%", "-0.85%")
- Convert nanosecond timestamp to ISO 8601 string
- Return StockOutput instance

**Tool Function:** `get_stock_price(ticker: str) -> str`
- Decorator: @tool(args_schema=StockInput)
- Docstring: "Get current stock price for a ticker symbol. Returns price in USD."
- Check is_configured -> return error JSON if not
- Try: call _fetch_stock_data, return model_dump_json()
- Except InvalidTickerSymbolError -> return error JSON
- Except HTTPStatusError -> return error JSON with status
- Except TimeoutException -> return timeout error JSON
- Except Exception -> return generic error JSON

---

### 5. Module Exports

**File:** `src/tools/stock/__init__.py`

Export:
- get_stock_price (from tool.py)
- StockInput (from schemas.py)
- StockOutput (from schemas.py)

Define __all__ list

---

## API Details

### Alpaca Snapshots Endpoint

**URL:** `GET /v2/stocks/snapshots`

**Query Parameters:**
- symbols: comma-separated ticker list (we send one)

**Headers:**
- APCA-API-KEY-ID: {api_key}
- APCA-API-SECRET-KEY: {secret_key}
- Accept: application/json

**Response:**
```json
{
  "AAPL": {
    "latestTrade": {
      "t": 1708312800000000000,
      "p": 178.52,
      "s": 100,
      "x": "V"
    },
    "latestQuote": {
      "t": 1708312800000000000,
      "bp": 178.50,
      "ap": 178.52
    },
    "prevDay": {
      "c": 176.18
    }
  }
}
```

**Field Mapping:**
- latestTrade.t -> timestamp (convert nanoseconds to ISO 8601)
- latestTrade.p -> price (float)
- prevDay.c -> previous_close (for change calculation)
- Change = price - previous_close, formatted with sign

**Timestamp Conversion:**
```
nanoseconds = 1708312800000000000
seconds = nanoseconds / 1_000_000_000
datetime = datetime.fromtimestamp(seconds, tz=timezone.utc)
iso_string = datetime.isoformat().replace("+00:00", "Z")
Result: "2024-02-18T14:30:00Z"
```

**Change Formatting:**
```
change_value = price - previous_close
if change_value >= 0:
    change = f"+{change_value:.2f}"
else:
    change = f"{change_value:.2f}"
Result: "+2.34" or "-1.50"
```

**Change Percent Formatting:**
```
change_percent_value = (price - previous_close) / previous_close * 100
if change_percent_value >= 0:
    change_percent = f"+{change_percent_value:.2f}%"
else:
    change_percent = f"{change_percent_value:.2f}%"
Result: "+1.32%" or "-0.85%"
```

---

## Output Schema

Final output:

```json
{
  "ticker": "AAPL",
  "price": 178.52,
  "currency": "USD",
  "timestamp": "2024-01-15T14:30:00Z",
  "change": "+2.34",
  "change_percent": "+1.32%"
}
```

---

## Error Response Format

All errors return JSON strings:

```json
{"error": "Error message here"}
```

Error messages must be:
- User-friendly (no stack traces)
- Actionable when possible
- Generic for unexpected errors

---

## Dependencies

No new dependencies needed. Uses existing:
- httpx (already in pyproject.toml)
- pydantic (already in pyproject.toml)
- langchain (already in pyproject.toml)
- datetime (standard library)

---

## Code Style Requirements

Per project guidelines:
- All functions async
- No comments (self-documenting code)
- Named boolean conditions (is_client_not_configured, etc.)
- Constants at module level (SCREAMING_SNAKE_CASE)
- No Any types
- Field descriptions on all Pydantic fields
- Python 3.11+ type syntax (str | None, not Optional[str])
