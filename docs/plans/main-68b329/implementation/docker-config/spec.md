# Docker Configuration Implementation

## Overview

Add Chainlit as a separate service in the existing docker-compose.yml configuration.

## Files to Modify

| File | Changes |
|------|---------|
| `docker-compose.yml` | Add chainlit service |
| `Dockerfile` | Optional: Add chainlit to development stage |

## docker-compose.yml Changes

### New Service Definition

Add to `services:` section:

```yaml
chainlit:
  build:
    context: .
    dockerfile: Dockerfile
    target: development
  container_name: veramoney-chainlit
  restart: unless-stopped
  ports:
    - "${CHAINLIT_PORT:-8002}:8000"
  environment:
    - BACKEND_URL=http://app:8000
    - CHAINLIT_API_KEY=${API_KEY}
    - CHAINLIT_REQUEST_TIMEOUT=120.0
    - CHAINLIT_MAX_RETRIES=3
  depends_on:
    app:
      condition: service_healthy
  networks:
    - vera-network
  command: chainlit run src/chainlit/app.py --host 0.0.0.0 --port 8000
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 10s
```

### Configuration Notes

1. **Target Stage**: Uses `development` stage for hot reload during development
2. **Port Mapping**: Maps container 8000 to host ${CHAINLIT_PORT:-8002}
3. **Backend URL**: Uses docker service name `app` for internal networking
4. **API Key**: Shares `API_KEY` with backend service
5. **Depends On**: Waits for `app` health check before starting
6. **Network**: Uses existing `vera-network`

### Production Considerations

For production, create a dedicated Chainlit Dockerfile or use runtime stage with chainlit installed.

## Dockerfile Modifications (Optional)

### Development Stage

If chainlit is not in pyproject.toml dependencies, add to development stage:

```dockerfile
FROM deps AS development
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install watchfiles chainlit>=2.4.0
# ... rest unchanged
```

### Alternative: Separate Dockerfile

Create `Dockerfile.chainlit` for production:

```dockerfile
FROM python:3.11-slim-bookworm

WORKDIR /app

RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src/chainlit ./src/chainlit
COPY .chainlit ./.chainlit

EXPOSE 8000
CMD ["chainlit", "run", "src/chainlit/app.py", "--host", "0.0.0.0", "--port", "8000"]
```

## Network Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    vera-network (bridge)                     │
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────────┐  │
│  │   app    │    │ chainlit │    │  postgres-memory     │  │
│  │  :8000   │◄───│  :8000   │    │      :5432           │  │
│  └──────────┘    └──────────┘    └──────────────────────┘  │
│       ▲                │                                     │
│       │                │                                     │
│       └────────────────┘ HTTP/SSE                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Startup Order

1. postgres-memory (data layer)
2. app (backend - depends on postgres-memory)
3. chainlit (frontend - depends on app healthy)

## Verification

- [ ] `docker-compose up chainlit` starts successfully
- [ ] Chainlit can reach backend at http://app:8000
- [ ] Port 8002 is accessible from host
- [ ] Health check passes
- [ ] Logs show successful startup

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused to app | Check app health status; verify network |
| Port already in use | Change CHAINLIT_PORT in .env |
| Module not found | Verify chainlit is installed in container |
| API key invalid | Check API_KEY value matches backend |
