# User Preferences & Decisions

## Configuration Preferences

| Preference | Choice |
|------------|--------|
| Context Level | Profundo |
| Participation Level | Equilibrado |
| Detail Level | Pseudocode |
| Extras | None (no tests, no documentation tasks) |

---

## Q&A and Rationale

### Data Source

**Q:** Which data source should the stock tool use?

**A:** Alpaca (Recommended)

**Decision:** Use Alpaca Market Data API as the sole data source.

**Rationale:** Demonstrates integration with a professional financial brokerage API, proper authentication handling, and understanding of API limitations. The 15-minute delay on free tier is acceptable for this assessment.

**Rejected:** yfinance (unofficial API), Hybrid approach (unnecessary complexity)

---

### Data Fields

**Q:** What stock data fields should the tool return?

**A:** Price + Change (requirement alignment)

**Decision:** Return: `ticker`, `price`, `currency`, `timestamp`, `change`.

**Rationale:** Requirement explicitly specifies change field. Alpaca /snapshots endpoint provides previous_close for change calculation.

**Rejected:** Price Only (missing required field), Price + Spread (over-engineering)

---

### Error Handling Strategy

**Q:** How should the tool handle API failures or invalid tickers?

**A:** Error JSON Only

**Decision:** Return structured JSON error messages. No fallback to alternative data sources.

**Rationale:** Simple and predictable behavior. The agent layer can decide how to present errors to users. Fallback mechanisms add complexity for a single-tool implementation.

**Rejected:** Fallback to yfinance (complexity), Cached Fallback (requires caching infrastructure)

---

### Integration Scope

**Q:** Should this task include agent integration?

**A:** Tool Only

**Decision:** Implement only the stock tool. Agent integration is a separate task.

**Rationale:** Focused scope. The tool will be ready for agent integration when that task is executed. Clean separation of concerns.

**Rejected:** Tool + Basic Agent (scope creep)

---

### Rate Limiting

**Q:** Should we implement rate limiting for Alpaca's 200 req/min limit?

**A:** No Rate Limiting

**Decision:** Rely on Alpaca's server-side rate limiting. No client-side throttling.

**Rationale:** 200 requests/minute is generous for a single-user tool. The assessment doesn't require production-grade rate limiting. Can be added later if needed.

**Rejected:** Add Request Limiting (unnecessary for assessment)

---

### Ticker Validation

**Q:** How strict should ticker symbol validation be?

**A:** Strict (A-Z, 1-5 chars)

**Decision:** Validate ticker format: 1-5 uppercase letters only.

**Rationale:** Matches US stock ticker format. Catches obvious input errors early. Pydantic validator normalizes input to uppercase.

**Rejected:** Permissive (could allow invalid inputs that fail at API level)

---

### Environment Configuration

**Q:** Should the tool default to Alpaca sandbox or production environment?

**A:** Production Default

**Decision:** Default to production environment (IEX feed with 15-minute delay). Sandbox available via environment variable.

**Rationale:** Production provides real data. Sandbox has limited symbol support. The 15-minute delay is acceptable for this assessment.

**Rejected:** Sandbox Default (limited data, less realistic)

---

### Tool Output Format

**Q:** Should the tool return raw structured JSON or a formatted message?

**A:** Raw Data Only

**Decision:** Return structured JSON. No human-readable formatting.

**Rationale:** Clean separation between data retrieval and presentation. The agent layer is responsible for formatting responses for users. JSON is machine-readable for agent processing.

**Rejected:** Formatted Message (mixes concerns)

---

### Requirements Alignment Updates

**After cross-check with stock-tool.md:**

**Q:** Should we add the 'change' field?

**A:** Yes - Add change field

**Decision:** Include `change` field to match requirement specification.

**Rationale:** Requirement explicitly shows `change: "+2.34"` in output schema. Alpaca /snapshots endpoint provides `previous_close` for calculation.

---

**Q:** What timestamp format?

**A:** ISO 8601 string

**Decision:** Use ISO 8601 format (`"2024-01-15T14:30:00Z"`) instead of Unix integer.

**Rationale:** Matches requirement example exactly. More human-readable.

---

**Q:** Input field name - ticker or symbol?

**A:** ticker

**Decision:** Use `ticker` for input field name instead of `symbol`.

**Rationale:** Consistent with requirement example and output field naming.

---

**Q:** Should we add percentage variation?

**A:** Yes - Add change_percent field

**Decision:** Include `change_percent` field formatted as string (e.g., "+1.32%").

**Rationale:** Gives agent more context to convey significance of price movement. Calculated as: (price - previous_close) / previous_close * 100.
