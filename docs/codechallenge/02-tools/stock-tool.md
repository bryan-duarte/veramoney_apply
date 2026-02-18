# Task 2: Stock Price Tool

> Status: TODO
> Priority: HIGH (Core Requirement)

## Overview

Create a tool that retrieves current stock price for a given ticker symbol.

## Requirements

- Input: Stock ticker (e.g., `AAPL`)
- Output: Structured JSON with price and timestamp
- Must be callable by the agent
- Validate ticker format
- Use public API or mock data

## Tasks

| ID | Task | Status | Notes |
|----|------|--------|-------|
| 2.2.1 | Create tool schema definition | TODO | Input: ticker, Output: price data |
| 2.2.2 | Implement stock fetch logic | TODO | Use httpx for async API calls |
| 2.2.3 | Validate ticker argument | TODO | Ensure valid ticker format |
| 2.2.4 | Return structured JSON | TODO | Price, timestamp, change |
| 2.2.5 | Make tool invocable | TODO | Register as LangChain tool |

## Output Schema

```json
{
  "ticker": "AAPL",
  "price": 178.52,
  "currency": "USD",
  "timestamp": "2024-01-15T14:30:00Z",
  "change": "+2.34"
}
```

## Implementation Location

```
src/tools/
└── stock/
    ├── __init__.py
    ├── tool.py          # LangChain tool definition
    ├── schemas.py       # Pydantic schemas
    └── client.py        # Async HTTP client
```

## LangChain Approach

**Reference:** `.claude/skills/langchain/reference/basics/tools.md`

Use the `@tool` decorator with validation:

```python
from langchain.tools import tool
from pydantic import BaseModel, Field
import re

class StockInput(BaseModel):
    ticker: str = Field(..., pattern=r"^[A-Z]{1,5}$")

@tool
async def get_stock_price(input_data: StockInput) -> dict:
    """Get current stock price for a ticker symbol."""
    # Implementation
    pass
```

## API Options

| Option | Pros | Cons |
|--------|------|------|
| Yahoo Finance | Free, no API key | Unofficial API |
| Alpha Vantage | Official, reliable | Rate limits |
| Mock Data | No dependencies | Not realistic |

**Recommendation:** Use mock data for development, add Yahoo Finance as enhancement.

## Ticker Validation

```python
TICKER_PATTERN = re.compile(r"^[A-Z]{1,5}$")

def validate_ticker(ticker: str) -> bool:
    return bool(TICKER_PATTERN.match(ticker.upper()))
```

## Error Handling

- Invalid ticker format: Return validation error
- Ticker not found: Return "not found" message
- API unavailable: Return cached/default data
- Timeout: Use retry with backoff

## Testing

```bash
# Unit test
pytest tests/tools/test_stock.py

# Integration test
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"message": "What is the price of AAPL?"}'
```

## Dependencies

```toml
httpx>=0.25.0  # Already installed
```
