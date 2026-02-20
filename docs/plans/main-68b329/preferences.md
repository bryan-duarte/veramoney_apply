# User Preferences & Decisions

## Configuration Preferences

| Preference | Selection | Notes |
|------------|-----------|-------|
| **Context Level** | Profundo | Comprehensive exploration with 8-12+ parallel tasks |
| **Participation Level** | Equilibrado | Moderate - 8-15 questions, key decisions by user |
| **Detail Level** | Pseudocode | Guidelines only, no specific code proposals |
| **Extras** | None | No tests or documentation included |

## Q&A and Rationale

### Session Management

**Q:** How should Chainlit manage session_id for the backend API?

**A:** cl.context.session.thread_id (Recommended)

**Decision:** Use Chainlit's built-in `cl.context.session.thread_id` as the `session_id` when calling the FastAPI backend. This provides automatic conversation continuity.

**Rejected:** New UUID generation (no persistence), User-provided (friction)

---

### Tool Visualization

**Q:** How should tool calls be visualized in the Chainlit UI?

**A:** Minimal (name only)

**Decision:** Show tool name with `cl.Step` but do not display input arguments or output details. Simple visual indication that a tool is being called.

**Rejected:** Full visualization (too detailed for proxy pattern), Token only (no tool context)

---

### Deployment Strategy

**Q:** How should Chainlit be deployed alongside the FastAPI backend?

**A:** Separate Docker service (Recommended)

**Decision:** Add Chainlit as a new service in `docker-compose.yml` with independent port (8002). Allows independent scaling and deployment.

**Rejected:** Local only (not production-ready), Mount on FastAPI (shared resources)

---

### Error Handling UI

**Q:** How should Chainlit handle API errors (401, 429, 500) in the UI?

**A:** Inline message with retry (Recommended)

**Decision:** Display human-readable error messages inline in the chat (not technical). Provide retry mechanism for transient errors.

**Rejected:** System message (less visible), Minimal feedback (poor UX)

---

### Module Location

**Q:** Where should the Chainlit application code be located?

**A:** src/chainlit/ (Recommended)

**Decision:** Create new `src/chainlit/` module following existing project structure patterns.

**Rejected:** Root level (inconsistent), src/api/chainlit/ (wrong layer)

---

### CORS Configuration

**Q:** How should CORS be configured for Chainlit-FastAPI communication?

**A:** Auto-configure CORS (Recommended)

**Decision:** Update `.env.example` with `CHAINLIT_URL` template for `CORS_ORIGINS`. User must uncomment/configure for their deployment.

**Rejected:** Manual (error-prone), Wildcard (insecure for production)

---

### Request Timeout

**Q:** What timeout should Chainlit use when waiting for the FastAPI backend?

**A:** 120 seconds (Recommended)

**Decision:** 120 second timeout for SSE stream. Sufficient for most agent responses including multi-tool calls.

**Rejected:** 180s (overly long), 300s (timeout hell)

---

### Welcome Experience

**Q:** What should the user see when starting a new Chainlit chat session?

**A:** Welcome message and Suggested prompts

**Decision:** Display welcome message explaining Vera capabilities, plus 3-4 suggested prompts (weather, stocks, combined) for easy interaction.

**Rejected:** Empty start (confusing), Welcome only (no guidance)

---

### API Key Management

**Q:** How should Chainlit obtain the API key for backend authentication?

**A:** Shared env variable (Recommended)

**Decision:** Use `CHAINLIT_API_KEY` environment variable in Chainlit service, with same value as backend `API_KEY`. Configure in docker-compose.

**Rejected:** Read from backend .env (coupling), User-provided (friction)

---

### Network Failure Handling

**Q:** How should Chainlit handle transient network failures?

**A:** Auto-retry with backoff

**Decision:** Implement automatic retry with exponential backoff (3 attempts, starting at 1s). Show connecting/retrying status to user.

**Rejected:** Manual retry button (more clicks), No retry (poor reliability)
