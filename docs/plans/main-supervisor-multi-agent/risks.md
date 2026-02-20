# Risks & Mitigations

## Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Worker invocation latency** | High | Medium | Workers use smaller model (nano) for faster responses; no checkpointer overhead on workers |
| **Streaming complexity** | Medium | Medium | Start with progress events only; full token streaming from workers is future enhancement |
| **Langfuse trace fragmentation** | Low | Low | Clear trace ID naming convention (`{session_id}-{worker}`); parent linkage metadata |
| **Prompt synchronization failures** | Medium | Low | Fallback to local prompt constants if Langfuse unavailable (existing pattern) |
| **Model context limits** | Low | Low | Workers are single-purpose with minimal context; supervisor handles context management |
| **Tool call parsing errors** | Medium | Low | Robust error handling in worker tool wrappers; graceful degradation messages |

## Integration Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Breaking API changes** | High | Low | Response schema is additive (new `worker_details` field); existing clients unaffected |
| **Middleware compatibility** | Medium | Low | Workers use minimal middleware (logging only); full stack only on supervisor |
| **Memory leak in workers** | Medium | Low | Workers are stateless with no checkpointer; no conversation state accumulation |
| **Database connection exhaustion** | Medium | Low | Only supervisor uses checkpointer; no additional DB connections from workers |
| **Langfuse rate limits** | Low | Low | Nested traces share session context; not independent API calls |

## Performance Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Sequential worker execution** | Medium | High | By design for first version; parallel execution is future enhancement via Router Pattern |
| **Double LLM calls per query** | High | High | Workers use cheaper model (nano) to minimize cost impact; supervisor only calls needed workers |
| **Streaming event overhead** | Low | Medium | Progress events are optional; clients can ignore if not needed |
| **Cold start latency** | Low | Medium | Workers are lightweight; no database initialization needed |

## Operational Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Debugging multi-agent traces** | Medium | Medium | Langfuse nested traces with clear naming; log correlation via session_id |
| **Prompt versioning complexity** | Low | Low | Centralized in PromptManager; same pattern as existing supervisor prompt |
| **Model availability** | High | Low | Worker model (nano) is standard OpenAI model; fallback to mini if unavailable |
| **Cost increase** | Medium | Medium | Nano model is cheaper than mini; net cost similar or lower than single agent |

---

## Edge Cases Identified

### 1. Multi-Domain Queries

**Scenario:** User asks "What's the weather in Apple HQ and what's AAPL stock price?"

**Handling:**
- Supervisor recognizes both weather and stock intent
- Calls `ask_weather_agent` with "What's the weather in Apple HQ (Cupertino)?"
- Calls `ask_stock_agent` with "What's AAPL stock price?"
- Synthesizes both responses into coherent answer

### 2. Ambiguous Queries

**Scenario:** User asks "What's the temperature?" without location

**Handling:**
- Supervisor routes to weather worker
- Weather worker recognizes missing location
- Worker responds asking for clarification (within its domain expertise)
- Supervisor passes through the clarification request

### 3. Worker Tool Failure

**Scenario:** Weather API returns 500 error

**Handling:**
- Worker tool wrapper catches exception
- Returns error message: "I'm having trouble accessing weather data right now."
- Supervisor receives this as tool result
- Supervisor includes in final response: "I couldn't get the weather data, but..."

### 4. Knowledge Base Empty Results

**Scenario:** Search returns no relevant documents

**Handling:**
- Knowledge worker receives empty results
- Worker responds: "I couldn't find relevant information in the knowledge base."
- Supervisor may fall back to general knowledge (with appropriate caveats)

### 5. Concurrent Session Load

**Scenario:** High traffic with many simultaneous sessions

**Handling:**
- Workers are stateless, no session coupling
- Supervisor checkpointer handles concurrent sessions via thread_id
- No shared state between sessions

### 6. Very Long Conversations

**Scenario:** Session with 50+ messages

**Handling:**
- Supervisor checkpointer manages context (existing `agent_max_context_messages` setting)
- Workers don't accumulate context (stateless)
- Context window pressure only on supervisor level

---

## Rollback Plan

If critical issues arise:

1. **Quick Rollback:**
   - Revert `src/agent/core/supervisor.py` to previous `factory.py` logic
   - Restore `AgentFactory` class
   - Remove worker imports from API handlers

2. **Partial Rollback:**
   - Keep worker modules for future use
   - Disable worker tools in supervisor
   - Fall back to direct tool usage

3. **Feature Flag (Future):**
   - Add `use_multi_agent` configuration option
   - Toggle between single agent and supervisor at runtime

---

## Monitoring Recommendations

### Key Metrics to Track

1. **Latency**
   - Supervisor response time
   - Worker invocation time per worker type
   - End-to-end request latency

2. **Cost**
   - Token usage per model (mini vs nano)
   - Tokens per worker type
   - Cost per query comparison

3. **Quality**
   - Worker routing accuracy (correct specialist selected)
   - Error rate per worker
   - User satisfaction (if measurable)

4. **Observability**
   - Langfuse trace completeness
   - Nested trace linkage success rate
   - Prompt version distribution
