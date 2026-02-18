# Implementation Tasks

## Task Breakdown

### Configuration Layer

- [ ] Add Alpaca API key settings to `src/config/settings.py`
- [ ] Update `.env.example` with Alpaca environment variables

### Schemas Module

- [ ] Create `src/tools/stock/schemas.py`
- [ ] Define `StockInput` with ticker field and validation
- [ ] Define `StockOutput` with ticker, price, currency, timestamp, change, change_percent
- [ ] Add field_validator for ticker normalization (uppercase, strip)
- [ ] Add pattern validation (^[A-Z]+$)

### Client Module

- [ ] Create `src/tools/stock/client.py`
- [ ] Define constants (URLs, timeouts, retry config)
- [ ] Create `InvalidTickerSymbolError` exception
- [ ] Create `AlpacaMarketDataError` base exception
- [ ] Implement `AlpacaMarketDataClient` class
  - [ ] Constructor with API keys and timeout
  - [ ] `is_configured` property
  - [ ] `_make_request` async method with retry logic
  - [ ] `get_snapshot` async method (calls /stocks/snapshots)

### Tool Module

- [ ] Create `src/tools/stock/tool.py`
- [ ] Implement `_fetch_stock_data` async helper function
  - [ ] Call get_snapshot
  - [ ] Extract price and previous_close
  - [ ] Calculate change (price - previous_close)
  - [ ] Format change with sign
  - [ ] Calculate change_percent ((price - prev) / prev * 100)
  - [ ] Format change_percent with sign and % suffix
  - [ ] Convert nanosecond timestamp to ISO 8601
- [ ] Implement `get_stock_price` with `@tool` decorator
- [ ] Handle unconfigured state
- [ ] Handle InvalidTickerSymbolError
- [ ] Handle httpx.HTTPStatusError
- [ ] Handle httpx.TimeoutException
- [ ] Handle generic exceptions

### Module Exports

- [ ] Create `src/tools/stock/__init__.py`
- [ ] Export `get_stock_price`, `StockInput`, `StockOutput`

---

## Task Dependencies

```
Configuration → Schemas → Client → Tool → Exports
```

All tasks are sequential - each depends on the previous being complete.

---

## Estimated Complexity

| Task | Complexity | Notes |
|------|------------|-------|
| Configuration | Low | Add 3 fields to existing Settings class |
| Schemas | Low | 2 simple Pydantic models |
| Client | Medium | HTTP client with retry logic |
| Tool | Low | Follow weather tool pattern |
| Exports | Low | Simple __init__.py |

---

## Files Summary

| File | Action | Lines (Est.) |
|------|--------|--------------|
| `src/config/settings.py` | Modify | +15 |
| `.env.example` | Modify | +3 |
| `src/tools/stock/schemas.py` | Create | ~30 |
| `src/tools/stock/client.py` | Create | ~100 |
| `src/tools/stock/tool.py` | Create | ~50 |
| `src/tools/stock/__init__.py` | Create | ~10 |

**Total estimated lines: ~200**

---

## Verification Steps

After implementation:

1. **Import Test**
   ```python
   from src.tools.stock import get_stock_price, StockInput, StockOutput
   ```

2. **Direct Tool Test**
   ```python
   result = await get_stock_price.ainvoke({"symbol": "AAPL"})
   print(result)  # Should show JSON with price or error
   ```

3. **Configuration Test**
   - Verify tool returns "not configured" error when keys are missing
   - Verify tool works when keys are set

4. **Validation Test**
   - Verify lowercase ticker is normalized to uppercase
   - Verify invalid format (numbers, too long) returns error

5. **Error Handling Test**
   - Verify invalid ticker returns proper error JSON
   - Verify API errors are handled gracefully
