# User Preferences & Decisions

## Configuration Preferences

| Preference | Selection |
|------------|-----------|
| **Context Level** | Profundo (comprehensive exploration) |
| **Participation Level** | Control pleno (user validates all decisions) |
| **Detail Level** | Pseudocode (guidelines only, no specific code) |
| **Optional Tasks** | Neither (no tests or documentation tasks) |

---

## Q&A and Rationale

### Agent Architecture

#### Agent Implementation Pattern
**Q:** Which agent implementation pattern should we use?
**A:** Agent with Middleware
**Decision:** Use `create_agent()` with middleware for error handling, logging, and request/response processing
**Rejected:** Basic Agent (too simple), Custom Graph (over-engineering)

#### Module Structure
**Q:** How should the agent module files be organized?
**A:** Nested Structure
**Decision:** Create subdirectories for `/core`, `/memory`, `/middleware` under `src/agent/`
**Rejected:** Flat structure (harder to maintain), Single file (poor separation)

#### Dependency Injection Pattern
**Q:** How should the agent be injected into the chat endpoint?
**A:** Per-Request Agent
**Decision:** Create `get_agent()` dependency that returns agent instance per request with session context
**Rejected:** Singleton (shared state issues), Fresh instance (no connection pooling)

---

### Memory Management

#### Memory Type
**Q:** What type of conversation memory should the agent use?
**A:** PostgreSQL persistence with session_id
**Decision:** Use PostgreSQL for persistent memory storage, leveraging session_id for conversation threading
**Rejected:** In-Memory (no persistence), Redis (overkill for this use case)

#### PostgreSQL Implementation
**Q:** How should we implement PostgreSQL for persistent memory?
**A:** New PostgreSQL Service
**Decision:** Create new PostgreSQL service in docker-compose dedicated to agent memory
**Rejected:** Reuse existing (contamination risk), InMemorySaver first (migration overhead)

#### Memory Schema
**Q:** What fields should be stored in the PostgreSQL memory schema?
**A:** Basic
**Decision:** Store session_id, messages (JSONB), created_at, updated_at
**Rejected:** Extended (not needed), Full audit trail (overhead)

#### PostgreSQL Schema Approach
**Q:** What PostgreSQL schema approach should be used?
**A:** Simple Table
**Decision:** Single `conversations` table with JSONB column for messages
**Rejected:** LangGraph PostgresSaver (complex setup), Normalized schema (query overhead)

#### Session Expiration
**Q:** How long should conversation sessions be kept?
**A:** No expiration
**Decision:** Sessions persist indefinitely for true long-term memory
**Rejected:** 1 hour, 24 hours (undesired cleanup)

#### Session ID Handling
**Q:** How should the agent handle missing session_id?
**A:** Require session_id
**Decision:** Return 400 error if session_id not provided in request
**Rejected:** Auto-generate (user control), Allow anonymous (no persistence)

#### Context Window Limit
**Q:** What is the maximum number of messages to keep?
**A:** 20 messages
**Decision:** Keep last 20 messages for ~8000 tokens context
**Rejected:** 10 (too short), 50 (token limit risk)

#### Message Trimming Strategy
**Q:** Which messages should be trimmed when exceeding limit?
**A:** FIFO - Trim Oldest
**Decision:** Remove oldest messages first, keeping most recent context
**Rejected:** LIFO (loses recent context), Keep boundaries (complex)

---

### LLM Configuration

#### Model Selection
**Q:** Which OpenAI model should be the default?
**A:** gpt-5-mini
**Decision:** Use gpt-5-mini as specified (verify availability at implementation)
**Rejected:** gpt-4o-mini, gpt-4o

#### Timeout
**Q:** What timeout should we configure for LLM API calls?
**A:** 30 seconds
**Decision:** 30 second timeout for API calls including tool execution
**Rejected:** 60 seconds (too long), 15 seconds (may timeout with tools)

#### Max Tokens
**Q:** What maximum tokens should we set for responses?
**A:** No limit
**Decision:** Let model decide based on context and query complexity
**Rejected:** 1000, 2000 (artificial constraints)

#### Temperature
**Q:** What temperature should we configure?
**A:** Default (don't modify)
**Decision:** Use provider's default temperature setting
**Rejected:** 0.1, 0.3, 0.7 (unnecessary customization)

---

### System Prompt & Persona

#### Agent Identity
**Q:** What should be the agent's name/identity?
**A:** Vera AI
**Decision:** Use "Vera AI" as the assistant name in system prompt
**Rejected:** Vera, Assistant, Custom

#### Tone & Style
**Q:** What tone/style should the agent use?
**A:** Professional
**Decision:** Clear and efficient responses, respectful but not overly casual
**Rejected:** Friendly (too casual), Technical (too jargon-heavy)

#### Missing Tools Response
**Q:** How should the agent respond to topics without relevant tools?
**A:** Answer Without Tools
**Decision:** Use general knowledge to answer when no tools are relevant
**Rejected:** Natural decline, List capabilities

---

### Tool Handling

#### Tool Failure Handling
**Q:** How should the agent handle tool execution failures?
**A:** Natural error messaging with service name
**Decision:** Agent says "I'm having trouble with [service name]..." naturally
**Rejected:** Generic message, Fail fast

#### Tool Error Detail Level
**Q:** What detail should tool error handler include?
**A:** Service Name
**Decision:** Include service name like "Weather service unavailable"
**Rejected:** Generic (too vague), Detailed with suggestion (verbose)

#### Parallel Tool Execution
**Q:** Should the agent execute multiple tool calls in parallel?
**A:** Agent Decides
**Decision:** Let the LLM decide when parallel execution is appropriate
**Rejected:** Force parallel, Sequential only

---

### Hallucination Prevention

#### Prevention Strategy
**Q:** What strategy should we use to prevent hallucination?
**A:** Combined Approach
**Decision:** Both prompt rules AND output guardrails middleware
**Rejected:** Prompt rules only, Guardrails only

#### Guardrails Checks
**Q:** What checks should output guardrails perform?
**A:** Tool Result Verification
**Decision:** Verify that tool results are actually used, not hallucinated
**Rejected:** Relevance check, Format validation, Citation verification (separately)

---

### Response Format

#### Response Style
**Q:** What format should agent responses use?
**A:** Natural citations (in-text references)
**Decision:** Include citations naturally like "According to weather data..."
**Rejected:** Plain text, Structured JSON

#### Citations Format
**Q:** How should citations be presented?
**A:** In-text References
**Decision:** Natural phrasing integrated into response text
**Rejected:** Inline markers, Footnotes style

---

### Streaming Configuration

#### Streaming Protocol
**Q:** What streaming protocol should be used?
**A:** Server-Sent Events (SSE)
**Decision:** Standard HTTP streaming with incremental updates
**Rejected:** NDJSON, WebSocket

#### Stream Events
**Q:** What events should be streamed?
**A:** Token Chunks, Tool Call Events, Error Events
**Decision:** Stream tokens as generated, emit tool call notifications, emit errors
**Rejected:** Final response (defeats purpose)

#### Streaming Integration
**Q:** How should streaming be integrated?
**A:** Replace Default
**Decision:** Replace `/chat` with streaming, add `/chat/complete` for batch
**Rejected:** Add new endpoint, Content negotiation

---

### Middleware Components

#### Included Middleware
**Q:** Which middleware components should be included?
**A:** Tool Error Handler, Output Guardrails, Request/Response Logging
**Decision:** Three middleware components for production-ready agent
**Rejected:** Context trimming (handled by memory store)

#### Error Logging Detail
**Q:** How detailed should error logging be?
**A:** Detailed
**Decision:** Include tool inputs, outputs, and timing for debugging
**Rejected:** Minimal, Basic only

---

### Observability

#### Langfuse Integration
**Q:** Should we integrate Langfuse observability?
**A:** Skip for Now
**Decision:** No Langfuse integration in this phase, can be added later
**Rejected:** Basic tracing, Enhanced metrics
