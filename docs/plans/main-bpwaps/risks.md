# Risks & Mitigations

## Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **gpt-5-mini model not available** | High | Medium | Verify model availability first; fallback to gpt-4o-mini if needed |
| **PostgreSQL connection failures** | High | Low | Connection pooling with retry logic; health check endpoint |
| **LLM timeout during tool execution** | Medium | Medium | 30s timeout with clear error messages; consider tool-level timeouts |
| **Memory store performance degradation** | Medium | Low | Index on session_id; connection pooling; query optimization |
| **Streaming connection drops** | Low | Medium | Implement reconnection guidance in API docs; keep-alive events |
| **Middleware order causing issues** | Medium | Low | Document execution order; unit test middleware chain |
| **Context window exceeded despite 20 message limit** | Medium | Low | Token counting before LLM call; dynamic trimming if needed |

## Integration Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Breaking existing /chat consumers** | High | High | Provide /chat/complete as migration path; version API |
| **Tool API rate limits hit by agent** | Medium | Medium | Tools already have retry logic; add per-session rate limiting |
| **PostgreSQL schema migration complexity** | Low | Low | Simple schema with JSONB; no complex migrations needed |
| **Dependency version conflicts** | Medium | Low | Verify asyncpg compatibility with existing stack |
| **LangChain v1 API changes** | Medium | Low | Pin versions; monitor changelog; use stable APIs only |

## Security Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Session hijacking via session_id** | High | Low | UUID validation; consider adding IP binding in future |
| **SQL injection in message content** | High | Very Low | Parameterized queries only; JSONB escaping |
| **Prompt injection attacks** | Medium | Medium | Input validation; guardrails middleware; output sanitization |
| **Sensitive data in logs** | Medium | Medium | Log structure only, not full content; PII redaction |
| **DoS via large messages** | Medium | Low | Existing 32000 char limit; add message rate limiting |

## Operational Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **PostgreSQL storage exhaustion** | Medium | Low | Monitor database size; implement optional TTL if needed |
| **Memory leak in connection pool** | Medium | Low | Proper pool lifecycle management; monitoring |
| **Streaming memory accumulation** | Low | Low | Proper async generator cleanup; backpressure handling |
| **Agent producing no output** | Medium | Low | Timeout handling; fallback error response |

## Edge Cases Identified

### Tool Execution Edge Cases

1. **Both tools fail simultaneously**
   - Agent receives two error messages
   - Should respond explaining both services unavailable
   - Mitigation: Tool error handler provides clear context

2. **Tool returns partial/invalid data**
   - Tool validation catches error
   - Returns error JSON to agent
   - Agent can retry or explain to user
   - Mitigation: Tools already have robust error handling

3. **Tool takes too long**
   - Tool timeout (10s) triggers
   - Tool returns timeout error
   - Agent responds with service unavailable
   - Mitigation: Existing tool retry logic handles this

### Conversation Edge Cases

1. **First message in new session**
   - No existing conversation in PostgreSQL
   - Create new conversation entry
   - Start fresh message history
   - Mitigation: get_conversation creates if not exists

2. **Session_id doesn't exist in database**
   - Query returns no results
   - Treat as new conversation
   - Mitigation: Upsert pattern on save

3. **Message history at exact 20 message limit**
   - FIFO trim removes oldest message
   - Add new message
   - Mitigation: Trim before add, not after

### Streaming Edge Cases

1. **Client disconnects mid-stream**
   - Generator detects disconnect
   - Cleanup resources
   - Log partial delivery
   - Mitigation: Proper async generator exception handling

2. **Error during streaming**
   - Emit error event
   - Close stream gracefully
   - Mitigation: Try/except around stream iteration

3. **Multiple tool calls in one turn**
   - Stream tool_call events sequentially
   - Continue token streaming after tools complete
   - Mitigation: Handle in stream iteration logic

### Hallucination Edge Cases

1. **Agent claims tool data not in results**
   - Guardrails detect mismatch
   - Log warning
   - Still return response (soft validation)
   - Mitigation: Combined with prompt rules

2. **Agent invents tool that doesn't exist**
   - Not possible - tools are pre-registered
   - Model can only call registered tools
   - Mitigation: Static tool registration

3. **Agent paraphrases tool result inaccurately**
   - Difficult to detect automatically
   - Guardrails focus on presence, not accuracy
   - Mitigation: Prompt rules for accurate paraphrasing

---

## Mitigation Priority Matrix

```
                    High Impact
                        │
    ┌───────────────────┼───────────────────┐
    │                   │                   │
    │  gpt-5-mini       │  Breaking /chat   │
    │  availability     │  consumers        │
    │                   │                   │
    │  Session          │  PostgreSQL       │
    │  hijacking        │  failures         │
    │                   │                   │
Low ─┼───────────────────┼───────────────────┼─ High
Prob│                   │                   │Prob
    │  Tool API         │  LLM timeout      │
    │  rate limits      │  during tools     │
    │                   │                   │
    │  Storage          │  Context window   │
    │  exhaustion       │  exceeded         │
    │                   │                   │
    └───────────────────┼───────────────────┘
                        │
                    Low Impact
```

**Immediate Actions Required:**
1. Verify gpt-5-mini model availability (fallback to gpt-4o-mini)
2. Plan /chat endpoint migration communication
3. Implement PostgreSQL health checks
