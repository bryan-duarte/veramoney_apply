# User Preferences & Decisions

## Configuration Preferences

| Preference | Selection |
|------------|-----------|
| **Context Level** | Profundo (comprehensive exploration) |
| **Participation Level** | Equilibrado (key decisions by user) |
| **Detail Level** | Pseudocode (guidelines only) |
| **Extras** | Neither (no tests or documentation tasks) |

---

## Q&A and Rationale

### Worker Architecture

#### Worker Location
**Q:** Where should the worker agents be located in the codebase structure?
**A:** `src/agent/workers/` (new directory)
**Decision:** Create a new `workers/` directory parallel to `agent/core/` for clean separation
**Rejected:** `multi_agent/workers/` (empty directory exists but workers/ is clearer); Co-location with tools (less separation)

#### Middleware Distribution
**Q:** How should middleware be distributed between supervisor and worker agents?
**A:** Supervisor only
**Decision:** Full middleware stack on supervisor (logging, error handler, output guardrails, knowledge guardrails); workers get minimal (just logging)
**Rejected:** Both levels (more overhead, complexity); Workers only (guardrails needed at top level)

#### Worker Memory
**Q:** Should worker agents have their own conversation memory/checkpointer?
**A:** No memory
**Decision:** Only supervisor has AsyncPostgresSaver checkpointer; workers are stateless per the subagents.md pattern
**Rejected:** Inherit supervisor (not needed for single-tool workers); Separate memory (over-engineering)

---

### Streaming & Observability

#### Streaming Behavior
**Q:** How should streaming work when supervisor delegates to worker agents?
**A:** Progress events
**Decision:** Worker progress events (tool calls, results) exposed to client through supervisor's stream
**Rejected:** Final response only (less visibility); Full streaming (more complex implementation)

#### Langfuse Tracing
**Q:** How should Langfuse tracing work for worker agents?
**A:** Nested traces
**Decision:** Each worker creates its own Langfuse trace with parent linkage to supervisor's trace
**Rejected:** Supervisor-level only (less detailed); Shared trace with spans (less isolation)

#### Worker Prompts
**Q:** How should worker agent system prompts be managed?
**A:** Langfuse-managed
**Decision:** Worker prompts managed via PromptManager, same as supervisor prompt; enables A/B testing and versioning
**Rejected:** Local constants (no versioning); Hybrid (more complexity for little gain)

---

### Error Handling & Models

#### Error Handling
**Q:** How should errors from worker agents be handled?
**A:** Graceful degradation
**Decision:** Worker errors wrapped in tool result message; supervisor handles gracefully with user-friendly message
**Rejected:** Bubble up to API (less helpful); Fallback to direct tool (adds complexity)

#### LLM Model
**Q:** What LLM model should worker agents use?
**A:** Smaller model: `gpt-5-nano-2025-08-07`
**Decision:** Workers use cheaper/smaller model for cost optimization since they handle simpler, domain-specific tasks
**Rejected:** Same as supervisor (no cost savings); Individually configurable (unnecessary flexibility)

#### Worker Tools
**Q:** Should worker agents have access to multiple tools or just their domain tool?
**A:** Single tool only
**Decision:** Each worker has exactly one tool matching its domain (weather worker -> get_weather tool)
**Rejected:** Multiple related tools (over-complicates); Shared tool access (defeats specialization purpose)

---

### API & Compatibility

#### Backward Compatibility
**Q:** Should we maintain backward compatibility with the single-agent approach?
**A:** Replace entirely
**Decision:** Remove single-agent code from AgentFactory, replace with supervisor pattern; cleaner codebase
**Rejected:** Dual mode via config (maintenance burden); New endpoint (code duplication)

#### API Response Detail
**Q:** What level of detail should the API response include about worker agent calls?
**A:** Include all levels
**Decision:** Response includes supervisor response + all worker tool calls for full visibility
**Rejected:** Supervisor only (hides useful debugging info); Client-configurable (unnecessary complexity)

---

## Decision Summary Table

| Category | Decision | Rationale |
|----------|----------|-----------|
| Worker Location | `src/agent/workers/` | Clean separation, follows existing patterns |
| Middleware | Supervisor only | Simpler, less overhead, guardrails at entry point |
| Worker Memory | None | Stateless workers, matches LangChain pattern |
| Streaming | Progress events | Good UX visibility without full streaming complexity |
| Langfuse | Nested traces | Detailed per-specialist traces with parent linkage |
| Worker Prompts | Langfuse-managed | Enables versioning and A/B testing |
| Error Handling | Graceful degradation | User-friendly, matches existing tool_error_handler |
| Worker Model | gpt-5-nano | Cost optimization for simple domain tasks |
| Worker Tools | Single tool | Focused specialists, no confusion |
| Backward Compat | Replace entirely | Cleaner codebase, no dead code |
| API Response | Include all levels | Full visibility for debugging |
