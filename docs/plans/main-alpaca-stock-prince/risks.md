# Risks & Mitigations

## Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Alpaca API changes or deprecation | Medium | Use stable v2 endpoints; abstract API calls in client class |
| 15-minute data delay confusion | Low | Document limitation clearly; timestamp shows actual trade time |
| API key exposure in logs | Medium | Never log API keys; use separate header construction |
| Rate limit exceeded (200 req/min) | Low | Not a concern for single-user assessment; can add later if needed |
| Network timeouts | Medium | Implement retry logic with exponential backoff (same as weather tool) |
| Invalid ticker validation bypass | Low | Pydantic validates at entry point; API also validates |

---

## Integration Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Tool not compatible with LangChain agent | Medium | Use standard @tool decorator; follow weather tool pattern exactly |
| JSON parsing errors in agent | Low | Return valid JSON strings; use model_dump_json() |
| Missing dependency version | Low | All dependencies already in pyproject.toml |
| Settings not loading | Low | Follow existing pydantic-settings pattern |

---

## Edge Cases Identified

### Ticker Symbol Edge Cases

| Case | Handling |
|------|----------|
| Lowercase input (aapl) | Normalized to uppercase via validator |
| Whitespace (" AAPL ") | Stripped via validator |
| Numbers in symbol (AAPL1) | Rejected by pattern validation |
| Too long (APPLEINC) | Rejected by max_length validation |
| Empty string | Rejected by min_length validation |
| Special chars (AAPL!) | Rejected by pattern validation |

### API Response Edge Cases

| Case | Handling |
|------|----------|
| Empty trades object | Raise InvalidTickerSymbolError |
| Null price field | Propagate as None (Pydantic handles) |
| Future timestamp | Accept as-is (Alpaca returns nanoseconds) |
| Missing trades key | Raise InvalidTickerSymbolError |

### Environment Edge Cases

| Case | Handling |
|------|----------|
| API key set, secret missing | is_configured returns False |
| Both keys missing | is_configured returns False |
| Empty string keys | is_configured returns False (len check) |
| Sandbox enabled | Use sandbox URL instead of production |

---

## Error Scenarios

### HTTP Status Codes

| Code | Meaning | Response |
|------|---------|----------|
| 200 | Success | Parse and return data |
| 400 | Bad request | `{"error": "Stock service error: 400"}` |
| 401 | Unauthorized | `{"error": "Stock service error: 401"}` |
| 403 | Forbidden | `{"error": "Stock service error: 403"}` |
| 404 | Not found | `{"error": "Invalid ticker: {symbol}"}` |
| 429 | Rate limited | `{"error": "Stock service error: 429"}` |
| 500+ | Server error | `{"error": "Stock service error: {code}"}` |

### Network Errors

| Error | Handling |
|-------|----------|
| TimeoutException | Retry up to 3 times with backoff |
| ConnectError | Raise after retries exhausted |
| ReadError | Raise after retries exhausted |

---

## Known Limitations

1. **15-Minute Data Delay**
   - Free tier uses IEX feed with delay
   - Not suitable for real-time trading decisions
   - Timestamp reflects actual trade time

2. **US Markets Only**
   - Alpaca free tier only supports US stocks
   - International tickers will fail

3. **No Historical Data**
   - Tool only returns latest trade
   - No price history or charts

4. **No After-Hours Data**
   - Free tier may have limited pre/post market data
   - Primary use case is during market hours

---

## Rollback Plan

If implementation fails or causes issues:

1. **Revert File Changes**
   ```bash
   git checkout HEAD -- src/config/settings.py .env.example
   ```

2. **Remove New Files**
   ```bash
   rm -rf src/tools/stock/
   ```

3. **No Database Migrations** - This feature has no database changes

4. **No External State** - Tool is stateless, no cleanup needed
