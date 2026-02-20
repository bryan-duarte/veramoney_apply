# User Preferences & Decisions

## Configuration Preferences

- **Context Level**: Profundo (comprehensive exploration)
- **Participation Level**: Control pleno (all decisions validated)
- **Detail Level**: Pseudocode (guidelines only, no specific code)
- **Extras**: No tests, no documentation

---

## Q&A and Rationale

### Trace Architecture

**Q:** How should the session_id map to Langfuse trace structure?
**A:** session_id = trace_id (Recommended)
**Decision:** Each session_id becomes one Langfuse trace. All requests in a session are spans within that trace.
**Rejected:** Request-level traces (harder to see full conversation)

**Q:** What trace granularity do you want for agent operations?
**A:** Full tracing (Recommended)
**Decision:** Trace LLM calls, tool executions, RAG retrieval, and embedding generation.
**Rejected:** Tool-only or minimal tracing (incomplete visibility)

**Q:** How should Langfuse be integrated with the existing middleware stack?
**A:** CallbackHandler in agent config
**Decision:** Pass Langfuse CallbackHandler to create_agent() config. Standard LangChain pattern.
**Rejected:** Custom middleware (less standard, more maintenance)

---

### Dataset Configuration

**Q:** When should the USER_OPENING_MESSAGES dataset be created?
**A:** Auto-create on first message (Recommended)
**Decision:** Create dataset lazily on first opening message. No manual setup required.
**Rejected:** Startup creation (unnecessary if no messages)

**Q:** What defines an 'opening message' for the dataset?
**A:** First message per session (Recommended)
**Decision:** First user message in each session_id, even if user returns later.
**Rejected:** Brand-new sessions only (misses returning users)

**Q:** What should be stored in the USER_OPENING_MESSAGES dataset items?
**A:** Include message content, metadata, expected_tool_calls
**Decision:** Store user message text, session metadata, and expected tool calls for evaluation.
**Rejected:** Expected response (not applicable for opening messages)

**Q:** Should additional datasets be created for tool-specific evaluation?
**A:** STOCK_QUERIES dataset
**Decision:** Create STOCK_QUERIES dataset for stock tool testing.
**Rejected:** WEATHER_QUERIES, RAG_QUERIES (not requested)

**Q:** What should the STOCK_QUERIES dataset capture?
**A:** Dataset only (Recommended)
**Decision:** Add stock queries to dataset only. Manual evaluation later.
**Rejected:** Include expected price or full response (over-engineering)

---

### Performance & Reliability

**Q:** What flush strategy should be used for sending traces to Langfuse?
**A:** Background flush (SDK default) (Recommended)
**Decision:** Use Langfuse SDK's built-in background flushing. Balanced approach.
**Rejected:** Flush on every request (latency), flush on shutdown only (data loss risk)

**Q:** How should the application behave if Langfuse is unavailable?
**A:** Graceful: log and continue (Recommended)
**Decision:** App works normally, logs warning if Langfuse fails. No user impact.
**Rejected:** Fail fast (too strict), return error (poor UX)

**Q:** Should Langfuse scoring be implemented in this integration?
**A:** No scoring initially (Recommended)
**Decision:** Just collect traces and datasets for now. Simplicity first.
**Rejected:** User feedback endpoint, LLM-as-Judge (complexity)

---

### Prompt Management

**Q:** Should system prompts be managed through Langfuse?
**A:** Use Langfuse for prompts
**Decision:** Migrate to Langfuse prompt management with auto-creation at startup, code as fallback.
**User Note:** The prompts must be created and saved automatically when the app setup, save the current plain text prompt as a fallback only.
**Rejected:** Keep prompts in code only (no versioning)

**Q:** How should prompts be synced between code and Langfuse?
**A:** Create once, no updates (Recommended)
**Decision:** Create prompt at startup if missing, don't update if it exists. Safe default.
**Rejected:** Sync on startup (could overwrite Langfuse changes), version labels (complexity)

**Q:** What type should prompts use in Langfuse?
**A:** Chat-type prompts (IMPROVEMENT)
**Decision:** Use `type="chat"` instead of `type="text"` for proper LangChain integration with placeholders and variables.
**Rationale:** Enables `chat_history` placeholder, dynamic variable injection, and `get_langchain_prompt()` method.

**Q:** Should dynamic variables be injected into the prompt?
**A:** Yes - date, model, version (IMPROVEMENT)
**Decision:** Add `{{current_date}}`, `{{model_name}}`, `{{version}}` variables to system prompt.
**Rationale:** Agent needs to know today's date for context. Date format: "DD Month, YY" (e.g., "20 February, 26").

---

### RAG Tracing

**Q:** How should the RAG pipeline be traced in Langfuse?
**A:** Full RAG tracing (Recommended)
**Decision:** Trace embedding generation, similarity search, and retrieved chunks in knowledge tool.
**Rejected:** Tool-level only (incomplete), no RAG tracing (misses optimization opportunities)

---

### Configuration

**Q:** Should Langfuse keys be required or optional?
**A:** Optional: disabled if no keys (Recommended)
**Decision:** If keys are missing/None, Langfuse is disabled. Simplest approach.
**Rejected:** Required in production (blocks deployment), always required (development friction)

---

### Metadata & Tagging

**Q:** What metadata should be attached to each trace?
**A:** Include model name, tool names, RAG usage flag
**Decision:** Track which model, which tools used, and whether RAG was involved.
**Rejected:** Environment (redundant with Langfuse project)

**Q:** What tags should be applied to traces for filtering?
**A:** Tool-based tags
**Decision:** Tags like 'weather', 'stock', 'knowledge' based on tools used.
**Rejected:** Outcome tags (noisy), environment tags (redundant), minimal tags (less filterability)

---

### Module Organization

**Q:** How should the Langfuse integration code be organized in src/observability/?
**A:** Multi-module structure
**Decision:** Separate modules: client.py, handler.py, datasets.py, prompts.py.
**Rejected:** Single module (less organized), split client+middleware (artificial separation)

**Q:** What log level should Langfuse errors use?
**A:** Warning level (Recommended)
**Decision:** Log warnings when Langfuse operations fail. Minimal noise.
**Rejected:** Error level (too verbose), debug level (invisible in production)

**Q:** What naming convention should be used for trace/span names?
**A:** veramoney-* prefix (Recommended)
**Decision:** veramoney-chat, veramoney-tool-weather, etc. Clear service identification.
**Rejected:** Simple names (ambiguous), domain-prefixed (verbose)

---

### Documentation

**Q:** Should documentation be created for the Langfuse integration?
**A:** Plan documentation only
**Decision:** Document in the plan files only. Implementation is self-documenting.
**Rejected:** Update CLAUDE.md (not requested), dedicated README (overhead)
