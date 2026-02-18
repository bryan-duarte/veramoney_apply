# FastAPI Security Hardening Plan

> "Security is not a product, but a process." — Bruce Schneier
> "Also, `allow_origins=['*']` is how you discover your API is now everyone's API." — El Barto

## Overview

**Request**: Improve the security of the current FastAPI implementation for a closed-feature API that will connect to a frontend.

**Created**: 2026-02-17

## What

Implement comprehensive security controls for the FastAPI API layer, including:

1. **API Key Authentication** - Simple, single-tenant authentication via X-API-Key header
2. **Rate Limiting** - Per-API-key rate limits (60 requests/minute) using slowapi
3. **CORS Hardening** - Allowlist-based CORS configuration from environment variables
4. **Input Validation** - Length constraints (1-32000 chars for message, UUID format for session_id)
5. **Security Headers** - Minimal essential headers (X-Content-Type-Options, Strict-Transport-Security)
6. **Error Sanitization** - Generic error messages to clients, full details in logs only
7. **Request Limits** - 60-second timeout, 1MB max body size

## Why

The current API implementation has critical security vulnerabilities:

| Vulnerability | Severity | Current State |
|--------------|----------|---------------|
| No Authentication | CRITICAL | Open to all |
| CORS Wildcard | CRITICAL | `allow_origins=["*"]` |
| No Rate Limiting | HIGH | Vulnerable to abuse |
| Unbounded Input | HIGH | No length limits |
| No Security Headers | MEDIUM | Missing X-Content-Type-Options |
| Error Information Leakage | MEDIUM | Stack traces exposed |
| API Docs Exposed | LOW | `/docs` always accessible |

Since this is a **closed feature** connecting to a **frontend**, we need proper authentication and protection against abuse while keeping implementation simple.

## Impact

### Files Modified
- `src/api/main.py` - Add middleware, disable docs, configure CORS
- `src/api/endpoints/chat.py` - Add auth dependency, input validation
- `src/api/dependencies.py` - Add API key validation, settings
- `src/config/__init__.py` - Create security settings
- `pyproject.toml` - Add security dependencies
- `.env.example` - Document required environment variables
- `.gitignore` - Add `.env` exclusion

### New Dependencies
- `slowapi>=0.1.9` - Rate limiting
- `secure>=0.3` - Security headers
- `pydantic-settings>=2.0` - Environment configuration

### Architecture Changes
- Add `SecurityMiddleware` layer
- Add `get_api_key` dependency for authentication
- Add `RateLimiter` middleware
- Move settings to proper `config/` module
