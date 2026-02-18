# Alpaca Market Data API Feasibility Report

> *"Free real-time stock data? Sure, if your definition of 'real-time' includes a 15-minute coffee break."*
> — **El Barto**

## Executive Summary

Alpaca provides a legitimate Market Data API with stock quote endpoints, but the **free tier delivers 15-minute delayed data via IEX feed**. Real-time quotes require a paid SIP subscription (~$9-15/month). The official Python SDK (`alpaca-py`) is synchronous-only, requiring a custom async wrapper for this project's async-first architecture. **Verdict: Feasible for development/testing with delayed data, but not suitable for production real-time quotes without paid subscription.**

---

## API Endpoint Analysis

### Available Endpoints for Real-Time Quotes

| Endpoint | Base URL | Purpose |
|----------|----------|---------|
| `/v2/stocks/quotes/latest` | `data.alpaca.markets` | Latest quote for single/multiple symbols |
| `/v2/stocks/trades/latest` | `data.alpaca.markets` | Latest trade execution |
| `/v2/stocks/snapshots` | `data.alpaca.markets` | Comprehensive snapshot (quote + trade + bars) |
| WebSocket `/v2/{feed}` | `stream.data.alpaca.markets` | Real-time streaming quotes |

### Request/Response Structure

**Latest Quote Request:**
```
GET /v2/stocks/quotes/latest?symbols=AAPL,GOOGL
Headers:
  APCA-API-KEY-ID: {api_key}
  APCA-API-SECRET-KEY: {secret_key}
```

**Response Structure:**
```json
{
  "quotes": {
    "AAPL": {
      "t": 1708312800000000000,
      "bp": 178.52,
      "bs": 100,
      "ap": 178.54,
      "as": 200,
      "bx": "V",
      "ax": "Q"
    }
  }
}
```

| Field | Description |
|-------|-------------|
| `t` | Unix nanosecond timestamp |
| `bp` | Bid price |
| `bs` | Bid size (shares) |
| `ap` | Ask price |
| `as` | Ask size (shares) |
| `bx` | Bid exchange code |
| `ax` | Ask exchange code |

---

## Free Tier Analysis

### What's Available on Free Tier

| Feature | Free Tier (IEX) | Paid Tier (SIP) |
|---------|-----------------|-----------------|
| **Data Latency** | 15-minute delay | Real-time |
| **Exchanges** | IEX only | NYSE, NASDAQ, AMEX, all major |
| **Quote Types** | Quotes, trades, bars | Quotes, trades, bars, Level 2 |
| **Historical Data** | Limited | Extended |
| **WebSocket Streaming** | Yes (delayed) | Yes (real-time) |
| **Symbol Limit** | Unlimited | Unlimited |
| **Rate Limits** | 200 req/min | 200 req/min |
| **Cost** | $0 | ~$9-15/month |

### Critical Limitation

**The IEX free feed provides 15-minute delayed data.** This is the core constraint for real-time stock price requirements. The delay is not configurable—it's inherent to the IEX feed without a paid subscription.

### Account Types

| Account Type | Purpose | Market Data Included |
|--------------|---------|---------------------|
| **Paper Trading** | Development/testing | Free IEX (delayed) |
| **Live Trading** | Real money trades | Requires paid subscription for real-time |

**Paper trading accounts are free and include market data access** (delayed IEX). No funding or KYC verification required for paper trading.

---

## Technical Implementation

### SDK Assessment

| Property | `alpaca-py` (Current) | `alpaca-trade-api` (Legacy) |
|----------|----------------------|----------------------------|
| **Status** | Active | Deprecated (2023) |
| **Python Support** | 3.8+ | 3.7+ |
| **Async Support** | No (synchronous only) | No |
| **PyPI Package** | `alpaca-py` | `alpaca-trade-api` |

**Critical Finding:** The official Alpaca SDK does **NOT support async operations**. This violates the project's async-first architecture requirement.

### Recommended Implementation: Custom Async Client

Since the SDK is synchronous, implement a custom async client using `httpx`:

```python
# src/tools/stock/client.py

import httpx
from src.config import settings

ALPACA_DATA_BASE_URL = "https://data.alpaca.markets/v2"
ALPACA_SANDBOX_BASE_URL = "https://data.sandbox.alpaca.markets/v2"
DEFAULT_TIMEOUT_SECONDS = 10.0


class AlpacaMarketDataError(Exception):
    pass


class InvalidTickerSymbolError(AlpacaMarketDataError):
    pass


class AlpacaMarketDataClient:
    def __init__(
        self,
        api_key: str | None = None,
        secret_key: str | None = None,
        use_sandbox: bool = True,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ):
        self._api_key = api_key or settings.alpaca_api_key
        self._secret_key = secret_key or settings.alpaca_secret_key
        self._base_url = ALPACA_SANDBOX_BASE_URL if use_sandbox else ALPACA_DATA_BASE_URL
        self._timeout_seconds = timeout_seconds
        self._headers = {
            "APCA-API-KEY-ID": self._api_key,
            "APCA-API-SECRET-KEY": self._secret_key,
            "Accept": "application/json",
        }

    @property
    def is_configured(self) -> bool:
        has_api_key = self._api_key is not None and len(self._api_key) > 0
        has_secret = self._secret_key is not None and len(self._secret_key) > 0
        return has_api_key and has_secret

    async def _make_request(self, endpoint: str, params: dict | None = None) -> dict:
        url = f"{self._base_url}/{endpoint}"
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.get(url, params=params, headers=self._headers)
            response.raise_for_status()
            return response.json()

    async def get_latest_quote(self, symbol: str) -> dict:
        if not self.is_configured:
            raise ValueError("Alpaca API keys not configured")

        normalized_symbol = symbol.upper().strip()
        if not normalized_symbol:
            raise InvalidTickerSymbolError("Ticker symbol cannot be empty")

        params = {"symbols": normalized_symbol}
        response = await self._make_request("stocks/quotes/latest", params)

        quote_data = response.get("quotes", {}).get(normalized_symbol)
        if quote_data is None:
            raise InvalidTickerSymbolError(f"No quote found for: {normalized_symbol}")

        return {
            "symbol": normalized_symbol,
            "bid_price": quote_data.get("bp"),
            "ask_price": quote_data.get("ap"),
            "bid_size": quote_data.get("bs"),
            "ask_size": quote_data.get("as"),
            "timestamp": quote_data.get("t"),
        }

    async def get_latest_trade(self, symbol: str) -> dict:
        normalized_symbol = symbol.upper().strip()
        params = {"symbols": normalized_symbol}
        response = await self._make_request("stocks/trades/latest", params)

        trade_data = response.get("trades", {}).get(normalized_symbol)
        if trade_data is None:
            raise InvalidTickerSymbolError(f"No trade found for: {normalized_symbol}")

        return {
            "symbol": normalized_symbol,
            "price": trade_data.get("p"),
            "size": trade_data.get("s"),
            "timestamp": trade_data.get("t"),
            "exchange": trade_data.get("x"),
        }

    async def get_snapshot(self, symbol: str) -> dict:
        normalized_symbol = symbol.upper().strip()
        params = {"symbols": normalized_symbol}
        response = await self._make_request("stocks/snapshots", params)

        snapshot = response.get(normalized_symbol)
        if snapshot is None:
            raise InvalidTickerSymbolError(f"No snapshot found for: {normalized_symbol}")

        latest_quote = snapshot.get("latestQuote", {})
        latest_trade = snapshot.get("latestTrade", {})

        return {
            "symbol": normalized_symbol,
            "price": latest_trade.get("p"),
            "bid_price": latest_quote.get("bp"),
            "ask_price": latest_quote.get("ap"),
            "bid_size": latest_quote.get("bs"),
            "ask_size": latest_quote.get("as"),
            "timestamp": latest_quote.get("t"),
        }
```

### LangChain Tool Integration

```python
# src/tools/stock/tool.py

import httpx
from langchain.tools import tool

from src.tools.stock.client import AlpacaMarketDataClient, InvalidTickerSymbolError
from src.tools.stock.schemas import StockPriceOutput


async def _fetch_stock_price(symbol: str) -> StockPriceOutput:
    client = AlpacaMarketDataClient()
    snapshot = await client.get_snapshot(symbol)

    spread_usd = snapshot["ask_price"] - snapshot["bid_price"]

    return StockPriceOutput(
        symbol=snapshot["symbol"],
        price=snapshot["price"],
        bid_price=snapshot["bid_price"],
        ask_price=snapshot["ask_price"],
        bid_size=snapshot["bid_size"],
        ask_size=snapshot["ask_size"],
        spread_usd=round(spread_usd, 4),
        timestamp=snapshot["timestamp"],
    )


@tool
async def get_stock_price(symbol: str) -> str:
    """Get current stock price for a ticker symbol. Returns bid, ask, spread, and last trade price."""
    client = AlpacaMarketDataClient()

    if not client.is_configured:
        return '{"error": "Stock tool not configured. Set ALPACA_API_KEY and ALPACA_SECRET_KEY."}'

    try:
        result = await _fetch_stock_price(symbol)
        return result.model_dump_json()
    except InvalidTickerSymbolError as e:
        return f'{{"error": "Invalid ticker: {symbol}"}}'
    except httpx.HTTPStatusError as e:
        return f'{{"error": "API error: HTTP {e.response.status_code}"}}'
    except Exception:
        return '{"error": "Failed to retrieve stock data"}'
```

---

## Signup Process

### Step-by-Step

1. **Create Account**: Visit [alpaca.markets](https://alpaca.markets) → "Get Started"
2. **Select Paper Trading**: Choose paper trading (free, no funding required)
3. **Email Verification**: Verify email address
4. **Generate API Keys**: Dashboard → API Keys → Generate New Keys
5. **Save Credentials**: Store `Key ID` and `Secret Key` securely (shown once)

### Environment Configuration

```bash
# .env
ALPACA_API_KEY=your_key_id_here
ALPACA_SECRET_KEY=your_secret_key_here
ALPACA_USE_SANDBOX=true
```

---

## Alternative Providers Comparison

| Provider | Real-Time Free | Free Tier Limits | Async-Friendly | Complexity |
|----------|---------------|------------------|----------------|------------|
| **Alpaca (IEX)** | No (15min delay) | 200 req/min | Custom client needed | Medium |
| **Alpha Vantage** | No (delayed) | 25 req/day | Yes (httpx) | Low |
| **yfinance** | Yes | Unlimited | Yes (httpx) | Very Low |
| **Polygon.io** | No (15min delay) | 5 calls/min | Yes | Medium |
| **Finnhub** | Limited | 60 calls/min | Yes | Medium |

### Recommendation for Assessment

**yfinance** is the simplest free alternative for real-time(ish) data:

```python
import yfinance as yf

ticker = yf.Ticker("AAPL")
info = ticker.info
price = info.get("currentPrice") or info.get("regularMarketPrice")
```

No API key required, completely free, adequate for technical assessment purposes.

---

## Key Findings

1. **Free Tier Exists**: Alpaca offers free paper trading with IEX market data access
2. **Data Is Delayed**: Free tier provides 15-minute delayed quotes, not real-time
3. **SDK Limitation**: Official `alpaca-py` SDK is synchronous-only—requires custom async wrapper
4. **Implementation Required**: Custom `httpx` client needed for async-first architecture
5. **Alternative Available**: `yfinance` provides free data without API keys for simpler implementation
6. **Signup Required**: Must create Alpaca account and generate API keys even for free tier

---

## Recommendations

### For Development/Testing
Use Alpaca with IEX feed (free tier). The 15-minute delay is acceptable for development and demonstrates integration with a professional brokerage API.

### For Production Real-Time
Either:
1. Pay for Alpaca SIP subscription ($9-15/month)
2. Use `yfinance` for free real-time(ish) data
3. Consider other providers (Polygon, Finnhub) based on specific requirements

### For This Assessment
Recommend using `yfinance` as the primary implementation due to:
- Zero configuration (no API keys)
- Truly free without rate limit concerns
- Adequate data quality for demonstration
- Simpler implementation

---

## Verdict Matrix

| Requirement | Alpaca Free Tier | Alpaca Paid | yfinance |
|-------------|------------------|-------------|----------|
| Real-time quotes | No | Yes | Yes* |
| Free cost | Yes | No | Yes |
| API key required | Yes | Yes | No |
| Async support | Custom needed | Custom needed | Yes |
| Professional API | Yes | Yes | No |
| Assessment fit | Medium | High | High |

* yfinance provides near-real-time data but is not a professional financial API

---

*Report generated by: El Barto*
*Date: 2026-02-18*
