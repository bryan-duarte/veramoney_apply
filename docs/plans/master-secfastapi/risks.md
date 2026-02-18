# Risks & Mitigations

## Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| API key exposed in git history | HIGH | Use `.env` file (gitignored), rotate key if exposed |
| Rate limiter state lost on restart | MEDIUM | Acceptable for single-instance; document Redis upgrade path |
| CORS misconfiguration blocks legitimate requests | MEDIUM | Test with actual frontend, provide clear error messages |
| Input validation too strict | LOW | 32000 char limit is generous; can adjust based on feedback |
| Security headers break frontend | LOW | Minimal headers selected; test with frontend integration |
| LLM calls take too long | LOW | No timeout implemented per user decision; monitor and add if needed |

## Integration Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Frontend doesn't send X-API-Key header | HIGH | Document API key requirement clearly, provide examples |
| Frontend origin not in CORS_ORIGINS | HIGH | Document CORS setup, provide localhost default |
| Rate limits too aggressive for legitimate use | MEDIUM | 60/min is conservative but reasonable; configurable via env |
| Async blocking in dependencies | LOW | API key validation is sync (OK for in-memory comparison) |

## Edge Cases Identified

### Authentication Edge Cases

| Case | Handling |
|------|----------|
| No X-API-Key header | Return 401 Unauthorized |
| Empty X-API-Key header | Return 401 Unauthorized |
| Wrong API key | Return 401 Unauthorized |
| Multiple X-API-Key headers | Framework uses first value |
| API key with special characters | Accept as-is, validate exact match |

### Rate Limiting Edge Cases

| Case | Handling |
|------|----------|
| Rate limit exceeded | Return 429 Too Many Requests with Retry-After header |
| Concurrent requests at limit boundary | May allow 1-2 over limit (acceptable) |
| Rate limiter memory exhaustion | slowapi uses LRU, old entries evicted automatically |
| Clock skew between requests | Handled by slowapi internally |

### CORS Edge Cases

| Case | Handling |
|------|----------|
| Origin not in allowlist | Return CORS error, block request |
| Origin with trailing slash | Exact match required; document clearly |
| Localhost with port | Must be explicitly listed in CORS_ORIGINS |
| Wildcard in allowlist | Not supported; explicit list required |

### Input Validation Edge Cases

| Case | Handling |
|------|----------|
| message is empty string | Rejected by min_length=1 |
| message is whitespace only | Accepted (valid string); trim if desired |
| message at exactly 32000 chars | Accepted (boundary inclusive) |
| message at 32001 chars | Rejected by max_length=32000 |
| session_id not UUID format | Rejected by UUID validator |
| session_id is empty string | Rejected by UUID validator |
| session_id is null | Accepted (Optional field) |

### Error Handling Edge Cases

| Case | Handling |
|------|----------|
| Unexpected exception | Generic 500 error, details logged |
| Pydantic validation error | 422 with field-level errors (FastAPI default) |
| Rate limit error | 429 with standard rate limit headers |
| Auth error | 401 with generic "Invalid or missing API key" |

## Security Considerations

### What This Plan Addresses

- [x] Authentication (API Key)
- [x] Rate Limiting (DoS protection)
- [x] CORS (CSRF mitigation)
- [x] Input Validation (injection prevention via Pydantic)
- [x] Error Sanitization (information disclosure prevention)
- [x] Security Headers (basic browser protections)
- [x] Async Architecture (event loop compatibility)

### What This Plan Does NOT Address

- [ ] Request timeouts (user decided not to implement)
- [ ] Request body size limits via middleware (using Pydantic only)
- [ ] Authorization (not needed for single-tenant)
- [ ] Encryption at rest (no data storage)
- [ ] Audit logging (can be added later)
- [ ] IP whitelisting (not required)
- [ ] WAF integration (infrastructure concern)
- [ ] Secret rotation automation (manual for MVP)
- [ ] Multi-instance deployment (single instance assumed)

## Async-Specific Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Blocking call in async context | HIGH | Only sync operations allowed are env parsing, string comparison, logging |
| SlowAPI incompatibility with async | LOW | SlowAPIMiddleware is async-compatible |
| Future tools using sync HTTP | HIGH | httpx added now; document that `requests` is forbidden |
| Event loop blocked by LLM call | MEDIUM | LangChain is async-compatible; use `await` properly |

## Rollback Plan

If security implementation causes issues:

1. **Immediate**: Set `ENVIRONMENT=development` to enable permissive mode (if implemented)
2. **Short-term**: Comment out security middleware, redeploy
3. **Fallback**: Revert to previous version via git

## Monitoring Recommendations

After implementation, monitor:

1. **Rate limit events** - Are legitimate users being throttled?
2. **Auth failures** - Could indicate key exposure or configuration issues
3. **4xx error rates** - High rates may indicate frontend integration issues
4. **Response times** - Security overhead should be minimal (<5ms)
5. **CORS errors** - Frontend may need origin configuration updates
6. **LLM call durations** - If consistently long, may need timeout later
