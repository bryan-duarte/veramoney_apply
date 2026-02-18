# Technical Design

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    LangChain Agent                       │
│                  (Future Integration)                    │
└─────────────────────┬───────────────────────────────────┘
                      │ invokes
                      ▼
┌─────────────────────────────────────────────────────────┐
│                  src/tools/stock/tool.py                 │
│  @tool get_stock_price(symbol: str) -> str              │
│  - Validates input via WeatherInput schema              │
│  - Returns JSON string (data or error)                  │
└─────────────────────┬───────────────────────────────────┘
                      │ calls
                      ▼
┌─────────────────────────────────────────────────────────┐
│                src/tools/stock/client.py                 │
│  class AlpacaMarketDataClient                           │
│  - Async httpx requests                                  │
│  - Authentication via headers                            │
│  - Retry logic with exponential backoff                  │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP GET
                      ▼
┌─────────────────────────────────────────────────────────┐
│           Alpaca Market Data API                         │
│  https://data.alpaca.markets/v2/stocks/...              │
│  - /quotes/latest (bid/ask)                              │
│  - /trades/latest (last trade price)                     │
│  - /snapshots (comprehensive)                            │
└─────────────────────────────────────────────────────────┘
```

---

## Three-Layer Tool Architecture

Following the existing weather tool pattern:

### Layer 1: Schemas (`schemas.py`)
- `StockInput` - Input validation (symbol field)
- `StockOutput` - Output structure (ticker, price, currency, timestamp)

### Layer 2: Client (`client.py`)
- `AlpacaMarketDataClient` class
- Async HTTP operations with httpx
- Error handling with custom exceptions

### Layer 3: Tool (`tool.py`)
- `get_stock_price` function with `@tool` decorator
- Business logic orchestration
- Error handling and JSON response formatting

---

## API Endpoint Selection

Alpaca provides three relevant endpoints:

| Endpoint | Use Case | Selected |
|----------|----------|----------|
| `/v2/stocks/quotes/latest` | Bid/ask prices | No |
| `/v2/stocks/trades/latest` | Last trade execution | No |
| `/v2/stocks/snapshots` | Comprehensive data | **Yes** |

**Decision:** Use `/snapshots` endpoint.

**Rationale:**
- Provides both latest trade price AND previous close
- Previous close needed for `change` calculation
- Single API call for all required data
- Matches requirement output schema

---

## Data Structures

### StockInput

```
StockInput(BaseModel):
    ticker: str
        - description: "Stock ticker symbol (e.g., AAPL, GOOGL)"
        - min_length: 1
        - max_length: 5
        - validation: uppercase letters only
        - normalization: uppercase, strip whitespace
```

### StockOutput

```
StockOutput(BaseModel):
    ticker: str
        - description: "Stock ticker symbol"
    price: float
        - description: "Current stock price in USD"
    currency: str
        - description: "Currency code"
        - default: "USD"
    timestamp: str
        - description: "ISO 8601 timestamp of the trade"
    change: str
        - description: "Price change from previous close with sign (e.g., '+2.34', '-1.50')"
    change_percent: str
        - description: "Percentage change from previous close with sign (e.g., '+1.32%', '-0.85%')"
```

### API Response Mapping

Alpaca `/snapshots` response:
```
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

Mapping to StockOutput:
- `ticker` <- ticker (from request)
- `price` <- `latestTrade.p` field
- `currency` <- hardcoded "USD"
- `timestamp` <- `latestTrade.t` converted to ISO 8601 string
- `change` <- calculated: `price - prevDay.c`, formatted with sign
- `change_percent` <- calculated: `(price - prevDay.c) / prevDay.c * 100`, formatted with sign and % suffix

---

## Error Handling

### Custom Exceptions

```
InvalidTickerSymbolError(AlpacaMarketDataError)
    - Raised when ticker not found or invalid

AlpacaMarketDataError(Exception)
    - Base exception for Alpaca errors
```

### Error Response Format

Tool returns JSON error strings (following weather tool pattern):

| Scenario | Response |
|----------|----------|
| API not configured | `{"error": "Stock tool not configured. Set ALPACA_API_KEY and ALPACA_SECRET_KEY."}` |
| Invalid ticker format | `{"error": "Invalid ticker format. Use 1-5 uppercase letters."}` |
| Ticker not found | `{"error": "Invalid ticker: {symbol}"}` |
| API error (HTTP 4xx/5xx) | `{"error": "Stock service error: {status_code}"}` |
| Timeout | `{"error": "Stock service unavailable. Please try again."}` |
| Unknown error | `{"error": "Failed to retrieve stock data."}` |

---

## Retry Strategy

Following weather tool pattern:

```
MAX_RETRIES = 3
INITIAL_RETRY_DELAY_SECONDS = 1.0

Retry Logic:
  - Only retry on TimeoutException
  - Exponential backoff: 1s, 2s, 4s
  - Do NOT retry on HTTPStatusError (4xx/5xx)
```

---

## Configuration

### Settings Additions

```
# src/config/settings.py

alpaca_api_key: str | None = Field(
    default=None,
    description="Alpaca API key ID for market data"
)

alpaca_secret_key: str | None = Field(
    default=None,
    description="Alpaca API secret key for market data"
)

alpaca_use_sandbox: bool = Field(
    default=False,
    description="Use Alpaca sandbox environment"
)
```

### Environment Variables

```
# .env.example additions

ALPACA_API_KEY=your_api_key_here
ALPACA_SECRET_KEY=your_secret_key_here
ALPACA_USE_SANDBOX=false
```

### URL Configuration

```
ALPACA_DATA_BASE_URL = "https://data.alpaca.markets/v2"
ALPACA_SANDBOX_BASE_URL = "https://data.sandbox.alpaca.markets/v2"
DEFAULT_TIMEOUT_SECONDS = 10.0
```

---

## Integration Points

### No Direct Integration (This Task)

The tool is standalone. Future agent integration will:
1. Import `get_stock_price` from `src.tools.stock`
2. Add to agent's tools list
3. Agent handles tool calling and response formatting

### Weather Tool Pattern Reference

The stock tool follows the exact pattern of the existing weather tool:
- Same directory structure
- Same async patterns
- Same error handling approach
- Same JSON response format

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `httpx` | >=0.25.0 | Async HTTP client (already installed) |
| `pydantic` | >=2.12.5 | Schema validation (already installed) |
| `langchain` | >=1.2.10 | Tool decorator (already installed) |

**No new dependencies required.**

---

## Security Considerations

1. **API Keys in Headers** - Alpaca requires keys in headers, not query params
2. **.env Exclusion** - Keys stored in .env (gitignored)
3. **No Key Logging** - Keys never logged or returned in errors
4. **Input Sanitization** - Ticker validated before use

---

## Constants

```
# client.py constants

ALPACA_DATA_BASE_URL = "https://data.alpaca.markets/v2"
ALPACA_SANDBOX_BASE_URL = "https://data.sandbox.alpaca.markets/v2"
DEFAULT_TIMEOUT_SECONDS = 10.0
MAX_RETRIES = 3
INITIAL_RETRY_DELAY_SECONDS = 1.0

# validation constants (schemas.py)

TICKER_MIN_LENGTH = 1
TICKER_MAX_LENGTH = 5
TICKER_PATTERN = r"^[A-Z]+$"
```
