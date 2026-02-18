# User Preferences & Decisions

## 👤 Configuration Preferences

- **Context Level**: Profundo (Comprehensive exploration with 8-12+ parallel tasks)
- **Participation Level**: Control pleno (User validates ALL design decisions)
- **Detail Level**: Pseudocode (Guidelines and lineaments only, no specific code proposals)
- **Extras**: Neither (No tests or documentation tasks included)

## 💬 Q&A and Rationale

### 🏷️ Authentication Strategy

**Q:** Since this is a closed feature with a frontend, which authentication method should we implement?

**A:** API Key

**Decision:** Use simple API Key authentication via `X-API-Key` header. No login UI needed, suitable for single-tenant architecture.

**Rejected:** JWT (overkill for single-tenant), OAuth2 (too complex), No Auth (insecure for closed feature)

---

### 🏷️ User System Architecture

**Q:** Should the API support multiple user accounts or is it single-tenant?

**A:** Single-tenant (one client app)

**Decision:** The API serves a single frontend client. Simplifies auth model - one API key validates all requests.

**Rejected:** Multi-user (adds complexity not needed), Public (contradicts closed feature requirement)

---

### 🏷️ CORS Configuration

**Q:** How should CORS be configured for the frontend connection?

**A:** Allowlist from environment

**Decision:** Load allowed origins from environment variable (`CORS_ORIGINS`). Supports multiple domains (dev + production).

**Rejected:** Single origin (too rigid), Permissive (insecure)

---

### 🏷️ Rate Limiting Implementation

**Q:** Should we implement rate limiting?

**A:** Yes, enforce limits

**Decision:** Implement rate limiting using slowapi. Protects against abuse and controls LLM API costs.

**Rejected:** Monitor only (doesn't prevent abuse), No rate limiting (unsafe)

---

### 🏷️ Rate Limiting Strategy

**Q:** How should rate limiting be applied?

**A:** Per API key limit

**Decision:** Rate limits tracked per API key, not per IP. Better for future multi-client extensibility.

**Rejected:** Global per-IP (doesn't account for legitimate shared IPs), Tiered (unnecessary complexity)

---

### 🏷️ Rate Limit Values

**Q:** What rate limit values should we use?

**A:** Conservative (60/min)

**Decision:** 60 requests per minute per API key. Balance between usability and protection.

**Rejected:** Moderate (higher risk), Custom per endpoint (unnecessary for MVP)

---

### 🏷️ Input Validation Limits

**Q:** What input validation limits should we apply?

**A:** Custom: message: 1-32000 chars, session_id: UUID format if provided

**Decision:**
- `message`: min_length=1, max_length=32000 (supports longer prompts)
- `session_id`: Optional, must be valid UUID format if provided

**Rejected:** Standard (too restrictive), Strict (hurts UX for longer prompts)

---

### 🏷️ Security Headers

**Q:** Should we add HTTP security headers middleware?

**A:** Minimal headers only

**Decision:** Add essential headers only:
- `X-Content-Type-Options: nosniff`
- `Strict-Transport-Security` (if HTTPS/production)

**Rejected:** Full security headers (unnecessary for API-only), None (missing basic protection)

---

### 🏷️ Error Handling

**Q:** How should error messages be handled for security?

**A:** Sanitized responses

**Decision:** Return generic error messages to clients. Log full details internally for debugging.

**Rejected:** Semi-detailed (still leaks info), Verbose (security risk)

---

### 🏷️ API Documentation Access

**Q:** Should API documentation (/docs, /redoc) be accessible?

**A:** Disable docs and redoc generally

**Decision:** Disable `/docs` and `/redoc` endpoints entirely. API is closed-feature, no public documentation needed.

**Rejected:** Environment-based (adds config complexity), Protected by auth (unnecessary), Always accessible (information disclosure)

---

### 🏷️ API Key Storage

**Q:** Where should API keys be stored and validated?

**A:** Environment variables

**Decision:** Store API key in `.env` file, load via pydantic-settings. Simple, standard approach for single-tenant.

**Rejected:** Hashed (overkill for single key), Multiple keys (not needed for single-tenant)

---

### 🏷️ API Key Header

**Q:** How should clients pass the API key?

**A:** X-API-Key header

**Decision:** Use `X-API-Key` custom header. Simple and widely understood.

**Rejected:** Authorization Bearer (implies OAuth/JWT semantics)

---

### 🏷️ Dependencies

**Q:** Which security-related dependencies should we add?

**A:** Essential only

**Decision:** Add only:
- `slowapi>=0.1.9` - Rate limiting
- `secure>=0.3` - Security headers
- `pydantic-settings>=2.0` - Environment configuration
- `httpx>=0.25` - Async HTTP client (for future tools)

**Rejected:** Include security tooling (adds dev complexity), Minimal (missing essential packages)

---

### 🏷️ Request Timeout

**Q:** How should request timeouts be implemented?

**A:** Do not add this, just ignore

**Decision:** No timeout implementation. LLM calls may take variable time; let them complete naturally.

**Rejected:** Middleware timeout, Per-operation timeout, Both combined

---

### 🏷️ Request Body Size

**Q:** How should request body size limits be enforced?

**A:** Pydantic validation only

**Decision:** No middleware for size limits. Rely on Pydantic `max_length=32000` on message field.

**Rejected:** Header check only, Header + body validation

---

### 🏷️ Rate Limit Key Function

**Q:** What should be used as the rate limiting key?

**A:** API key as key

**Decision:** Use the API key value as the rate limit identifier. Tied to authenticated client, more accurate than IP.

**Rejected:** IP address (shared IPs issue), Hybrid (too complex)

---

### 🏷️ Middleware Order

**Q:** What order should the middleware be executed?

**A:** Standard security order

**Decision:** CORS → Rate Limit → Security Headers → Auth. Standard security layer ordering.

**Rejected:** Rate limit first, Agent decides

---

### 🏷️ API Key Dependency Type

**Q:** Should the API key validation dependency be sync or async?

**A:** Sync function

**Decision:** `def get_api_key()` - simple string comparison, no I/O needed. Sync is fine for in-memory validation.

**Rejected:** Async function (unnecessary for simple comparison)

---

### 🏷️ Global Exception Handler

**Q:** Should we add a global async exception handler?

**A:** Yes, global handler

**Decision:** Add `@app.exception_handler(Exception)` to catch all unhandled exceptions, log details, return generic message.

**Rejected:** FastAPI default, HTTP only handler

---

### 🏷️ Health Endpoint Protection

**Q:** Should the /health endpoint be protected or public?

**A:** Public, no protection

**Decision:** `/health` endpoint has no auth and no rate limit. For load balancers and monitoring systems.

**Rejected:** Protected with API key, Auth only no rate limit

---

## Summary of All Decisions

| Category | Decision |
|----------|----------|
| Authentication | API Key via X-API-Key header |
| Architecture | Single-tenant |
| CORS | Allowlist from environment |
| Rate Limiting | 60/min per API key |
| Input Validation | Pydantic: 1-32000 chars, UUID session_id |
| Security Headers | Minimal (nosniff, HSTS) |
| Error Handling | Sanitized responses |
| API Docs | Disabled entirely |
| Key Storage | Environment variables |
| HTTP Client | httpx (async, added now) |
| Request Timeout | Not implemented |
| Request Size | Pydantic validation only |
| Middleware Order | CORS → Rate Limit → Security Headers |
| API Key Dep | Sync function |
| Exception Handler | Global async handler |
| Health Endpoint | Public (no auth, no rate limit) |
