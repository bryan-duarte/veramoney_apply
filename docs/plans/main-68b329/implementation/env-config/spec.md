# Environment Configuration Implementation

## Overview

Configure environment variables for Chainlit and update CORS settings for the backend.

## Files to Modify

| File | Changes |
|------|---------|
| `.env.example` | Add Chainlit variables, update CORS example |
| `pyproject.toml` | Add chainlit dependency |

## .env.example Changes

### New Variables Section

Add to `.env.example`:

```bash
# Chainlit Configuration
# ----------------------
# Port for Chainlit UI (default: 8002)
CHAINLIT_PORT=8002

# API key for Chainlit to authenticate with backend
# Must match API_KEY value above
CHAINLIT_API_KEY=your-api-key-here

# Backend URL (for non-Docker setups)
# CHAINLIT_BACKEND_URL=http://localhost:8000
```

### CORS Update

Update `CORS_ORIGINS` example to include Chainlit:

```bash
# CORS Origins (comma-separated)
# Include Chainlit URL for proxy pattern
CORS_ORIGINS=http://localhost:8002,http://localhost:3000
```

### Complete CORS Section

```bash
# CORS Configuration
# ------------------
# Comma-separated list of allowed origins for cross-origin requests
# For Chainlit integration, include the Chainlit URL
# Example: CORS_ORIGINS=http://localhost:8002,https://your-frontend.com
CORS_ORIGINS=
```

## pyproject.toml Changes

### Add Dependency

In `dependencies` section:

```toml
dependencies = [
    # ... existing dependencies ...
    "chainlit>=2.4.0",
]
```

### Alternative: Optional Dependency

If Chainlit should be optional:

```toml
[project.optional-dependencies]
chainlit = ["chainlit>=2.4.0"]
```

Install with: `uv sync --extra chainlit`

## Environment Variable Mapping

| Variable | Used By | Purpose |
|----------|---------|---------|
| `API_KEY` | Backend | Authenticate API requests |
| `CHAINLIT_API_KEY` | Chainlit | Same value as API_KEY |
| `CHAINLIT_PORT` | Docker | Host port mapping |
| `CORS_ORIGINS` | Backend | Allow Chainlit origin |
| `BACKEND_URL` | Chainlit (Docker) | Backend service URL |

## Configuration Checklist

For local development:
- [ ] Copy `.env.example` to `.env`
- [ ] Set `API_KEY` to a secure value
- [ ] Set `CHAINLIT_API_KEY` to same value as `API_KEY`
- [ ] Set `CORS_ORIGINS=http://localhost:8002`
- [ ] Run `uv sync` to install chainlit

For Docker deployment:
- [ ] Set `API_KEY` in `.env`
- [ ] `CHAINLIT_API_KEY` inherits from `API_KEY` in docker-compose
- [ ] Update `CORS_ORIGINS` to include Chainlit URL
- [ ] Run `docker-compose up -d`

## Validation

On Chainlit startup, validate:
- `CHAINLIT_API_KEY` is not empty
- Backend is reachable (optional)
- CORS is configured (warning if not)

## Security Notes

1. **Never commit `.env`** - Already in .gitignore
2. **API Key Rotation** - Change both `API_KEY` and `CHAINLIT_API_KEY` together
3. **Production CORS** - Use specific domain, not wildcards
4. **Docker Secrets** - Consider using Docker secrets for production API keys

## Example .env File

```bash
# Application
ENVIRONMENT=development
LOG_LEVEL=info
APP_PORT=8000

# Security
API_KEY=dev-secret-key-change-in-production
RATE_LIMIT_PER_MINUTE=60

# CORS - Include Chainlit URL
CORS_ORIGINS=http://localhost:8002

# OpenAI
OPENAI_API_KEY=sk-...

# Tool APIs
WEATHERAPI_KEY=...
FINNHUB_API_KEY=...

# Chainlit
CHAINLIT_PORT=8002
CHAINLIT_API_KEY=dev-secret-key-change-in-production

# PostgreSQL Memory
POSTGRES_MEMORY_HOST=localhost
POSTGRES_MEMORY_PORT=5433
POSTGRES_MEMORY_USER=veramoney
POSTGRES_MEMORY_PASSWORD=veramoney_secret
POSTGRES_MEMORY_DB=veramoney_memory
```
