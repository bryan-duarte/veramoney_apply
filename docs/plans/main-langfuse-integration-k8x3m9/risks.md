# Risks & Mitigations

## Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Langfuse SDK blocking event loop | High | Use background flush, wrap sync calls in `asyncio.to_thread()` |
| Trace memory accumulation | Medium | SDK handles batching; no in-memory trace storage |
| CallbackHandler conflicts with existing middleware | Medium | Test thoroughly; CallbackHandler is additive, not replacement |
| Prompt fetch latency on startup | Low | Create once, cache in memory; fallback to code if fails |
| Dataset item creation blocking | Low | Fire-and-forget pattern with error logging |

## Integration Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing agent behavior | High | CallbackHandler is passive; no changes to agent logic |
| Session_id not unique (UUID collision) | Very Low | UUID validation already in place; extremely unlikely |
| Missing environment variables in production | Medium | Graceful degradation; log warning, continue without tracing |
| Langfuse Docker stack unhealthy | Medium | Health checks in compose; app continues without tracing |

## Edge Cases Identified

### Opening Message Detection

**Edge Case:** User sends multiple rapid requests in a new session.

**Handling:** Check if session has prior messages in memory store BEFORE creating trace. First message wins.

### Dataset Duplicate Prevention

**Edge Case:** Same session sends same opening message multiple times.

**Handling:** Langfuse datasets allow duplicates. Not a problem for evaluation.

### Concurrent Trace Updates

**Edge Case:** Multiple requests for same session_id (parallel tool calls).

**Handling:** Langfuse SDK handles concurrent span creation. Trace ID is session_id, spans are nested correctly.

### Prompt Sync Race Conditions

**Edge Case:** Multiple app instances startup simultaneously.

**Handling:** Langfuse `get_prompt()` with `create_if_missing=True` is idempotent. No race condition.

### Network Partitions

**Edge Case:** Langfuse becomes unavailable mid-session.

**Handling:** Each request checks client health. If unhealthy, skip tracing, log warning.

### Large Trace Payloads

**Edge Case:** Very long conversations with many tool calls.

**Handling:** SDK batches and compresses. No action needed unless Langfuse reports issues.

## Rollback Plan

If Langfuse integration causes issues:

1. **Immediate:** Remove `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` from environment
2. **Code:** All code has `if langfuse_client is None` guards - will skip tracing
3. **Full rollback:** Revert commits, no database changes made

## Monitoring Recommendations

After deployment, monitor:

1. **Langfuse UI:** Traces appearing correctly
2. **App logs:** Warning messages about Langfuse failures
3. **Response latency:** Should not increase significantly
4. **Memory usage:** Should remain stable
5. **Error rates:** Should not increase
