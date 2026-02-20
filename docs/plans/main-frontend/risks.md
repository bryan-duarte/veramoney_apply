# Risks & Mitigations

## Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **SSE Parsing Complexity** | High | Medium | Use proven patterns from examples; test edge cases (empty lines, malformed JSON) |
| **Rate Limit Exhaustion** | Medium | Medium | Chainlit shares 60/min limit with other clients; monitor usage; consider increasing limit |
| **Network Latency** | Medium | Low | 120s timeout handles slow responses; auto-retry on failures |
| **Session ID Mismatch** | High | Low | Use `cl.context.session.thread_id` directly; validate UUID format |
| **API Key Exposure** | High | Low | Environment variables only; never log; use docker secrets in production |

## Integration Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **CORS Misconfiguration** | High | Medium | Clear documentation in .env.example; validate CORS on startup |
| **Backend Unavailable** | High | Low | Auto-retry with backoff; graceful error message; health check dependency |
| **Version Incompatibility** | Medium | Low | Pin chainlit version (>=2.4.0); test with existing dependencies |
| **Docker Network Issues** | Medium | Low | Use existing vera-network; verify service discovery |

## Edge Cases Identified

### SSE Stream Edge Cases

| Case | Handling |
|------|----------|
| Empty `data:` payload | Skip processing, continue iteration |
| Malformed JSON in data | Log warning, skip event |
| Missing `event:` line | Default to "token" behavior |
| Multiple tool calls in sequence | Open/close steps sequentially |
| Stream interruption | Trigger retry if attempts remaining |

### Error Edge Cases

| Case | Handling |
|------|----------|
| 401 Unauthorized | Show "Unable to connect to service"; no retry |
| 429 Rate Limited | Show "Please wait a moment..."; no retry |
| 500 Server Error | Show "Something went wrong"; retry up to 3x |
| Connection Refused | Show "Connecting..."; retry up to 3x |
| Timeout (120s) | Show "Request timed out"; retry up to 3x |
| Invalid session_id format | Should not occur (Chainlit provides valid IDs) |

### Session Edge Cases

| Case | Handling |
|------|----------|
| New session (no history) | Normal flow - backend creates new conversation |
| Resumed session | `thread_id` persists; backend loads history |
| Concurrent messages | Each message processes sequentially |
| Long conversation | Backend handles context window (max 20 messages) |

## Mitigation Strategies

### 1. SSE Parsing Robustness

Implement defensive parsing:
- Handle missing event types gracefully
- JSON decode with try/except
- Log parsing failures without crashing

### 2. Network Resilience

Auto-retry configuration:
- 3 attempts maximum
- Exponential backoff (1s, 2s, 4s)
- Only retry on retryable errors (network, 500, timeout)
- Visual feedback during retry ("Connecting...")

### 3. Error Message Sanitization

Never expose:
- Stack traces
- API keys
- Internal URLs
- Technical error codes

Instead show:
- "Unable to connect to service"
- "Please wait a moment..."
- "Something went wrong. Please try again."

### 4. Configuration Validation

On startup, validate:
- `CHAINLIT_API_KEY` is set
- `BACKEND_URL` is reachable (optional health check)
- CORS origins are configured in backend

## Monitoring Points

| Metric | Collection Method |
|--------|-------------------|
| Request latency | Log timing in handlers |
| Error rate | Log error events |
| Retry attempts | Log retry occurrences |
| Session duration | Track via Chainlit session |

## Rollback Plan

If issues arise:

1. **Immediate**: Remove chainlit service from docker-compose
2. **Short-term**: Disable Chainlit in load balancer/router
3. **Full rollback**: Remove `src/chainlit/` directory and dependencies

No database migrations required - all changes are additive.
