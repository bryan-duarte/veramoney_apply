# Risks & Mitigations

## Technical Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Connection pool exhaustion under high load | High | Medium | Set `max_connections=100`, `max_keepalive_connections=20`, monitor pool usage |
| Lock contention in supervisor initialization | Medium | Low | Use double-checked locking, locks are short-lived |
| Breaking change in StockOutput schema | Medium | Low | `change_percent` float is backward-compatible with string parsing |
| WeatherAPI HTTPS not supported | Medium | Low | Verified: WeatherAPI supports HTTPS |
| Langfuse async SDK availability | Low | Low | Using `asyncio.to_thread()` as fallback |

## Integration Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Circular import after prompts extraction | High | Medium | Careful import ordering, use `TYPE_CHECKING` where needed |
| Mixin `__init__` conflicts | Medium | Medium | Use explicit `Mixin.__init__(self, ...)` calls, document MRO |
| Client cleanup not called on crash | Medium | Low | Use try/finally in lifespan, log cleanup status |
| Rate limit key change breaks existing users | Low | Low | Sanitization preserves key format, just validates |

## Edge Cases Identified

### Division by Zero (C3)

**Scenario**: Stock has `previous_close=0` (new IPO, penny stock glitch)

**Handling**: Return `0.0` for `change_percent`, valid float value

**Alternative Considered**: Return `None` - rejected as breaking change

### None Checkpointer (C4)

**Scenario**: New session with no prior state in memory store

**Handling**: Return `True` from `is_opening_message()`, treat as fresh conversation

**Alternative Considered**: Raise exception - rejected as over-engineering

### Empty API Key in Rate Limiter

**Scenario**: Request with empty `X-API-Key: ""` header

**Handling**: Sanitization should reject empty strings, fall back to IP-based rate limiting

### Malformed URL in RAG Loader

**Scenario**: URL like `file:///etc/passwd` or `http://localhost:8080`

**Handling**: Allowlist validation rejects non-HTTPS and non-allowlisted domains

**Error Message**: `"URL not in allowlist. Only configured document URLs are permitted."`

### Concurrent Supervisor Initialization

**Scenario**: 100 requests arrive simultaneously on cold start

**Handling**: Lock ensures only one initialization, others wait and reuse

**Worst Case**: 99 requests wait ~500ms for memory store initialization

### Log Injection Attempt

**Scenario**: Session ID contains `\nERROR: Fake log entry`

**Handling**: `sanitize_for_log()` escapes `\n` to `\\n`, truncates to 100 chars

### Connection Pool Saturation

**Scenario**: 150 concurrent requests to weather API

**Handling**: Pool limits to 100 connections, 50 wait in queue

**Monitoring**: Add metric for connection pool wait time (future enhancement)

## Rollback Considerations

### If Connection Pooling Causes Issues

1. **Immediate**: Set `max_connections=1` to force serial behavior
2. **Fallback**: Revert to transient `async with httpx.AsyncClient()` pattern
3. **Debug**: Add logging for connection lifecycle events

### If Mixin Composition Breaks

1. **Immediate**: Revert ChatHandlerBase to single class
2. **Fallback**: Keep extracted services as composed objects instead of mixins
3. **Debug**: Check MRO with `ClassName.__mro__`

### If Prompts Extraction Fails

1. **Immediate**: Add `sys.path` manipulation as temporary fix
2. **Fallback**: Revert to TYPE_CHECKING pattern
3. **Debug**: Use `python -c "import module"` to test imports

## Testing Recommendations

### Unit Tests (Future)

- Test division by zero returns 0.0
- Test None state returns True for is_opening_message
- Test timing attack protection with various key lengths
- Test SSRF protection with malicious URLs
- Test rate limit key sanitization with special characters
- Test log sanitization with injection attempts

### Integration Tests (Future)

- Test connection pool under concurrent load
- Test lock behavior with concurrent supervisor creation
- Test full request flow with new mixins
- Test cleanup on application shutdown

### Manual Verification

- [ ] Verify HTTPS WeatherAPI calls work
- [ ] Verify stock with zero previous_close doesn't crash
- [ ] Verify new session doesn't crash supervisor
- [ ] Verify connection reuse in logs (httpx debug logging)
