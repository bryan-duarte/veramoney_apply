# Docker Setup

> Status: DONE
> Priority: BONUS

## Overview

Containerize the application for production deployment.

## Current Status

| ID | Task | Status | Notes |
|----|------|--------|-------|
| D1 | Create Dockerfile | DONE | Multi-stage build |
| D2 | Create docker-compose.yml | DONE | Full stack with Langfuse, ChromaDB |
| D3 | Configure environment | DONE | Env vars, volumes, ports |
| D4 | Document Docker usage | DONE | In README.md |

## Files

```
veramoney-apply/
├── Dockerfile              # Multi-stage build
├── docker-compose.yml      # Full stack orchestration
├── .dockerignore           # Exclude files from build
└── .env.example            # Environment template
```

## Dockerfile

Multi-stage build for optimized image size:

```dockerfile
# Build stage
FROM python:3.11-slim-bookworm AS builder
# Install dependencies with uv

# Runtime stage
FROM python:3.11-slim-bookworm AS runtime
# Copy only necessary files
# Run as non-root user

CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Docker Compose Services

| Service | Port | Purpose |
|---------|------|---------|
| app | 8000 | FastAPI application |
| chromadb | 8001 | Vector database |
| langfuse-server | 3000 | Observability UI |
| langfuse-worker | - | Background jobs |
| postgres | 5432 | Langfuse database |
| clickhouse | 8123 | Langfuse analytics |
| redis | 6379 | Langfuse cache |
| minio | 9000 | Object storage |

## Commands

```bash
# Build image
docker build -t veramoney-api .

# Run single container
docker run -p 8000:8000 --env-file .env veramoney-api

# Start full stack
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up -d --build
```

## Environment Variables

Required in `.env`:
- `API_KEY`
- `OPENAI_API_KEY`
- `ENVIRONMENT`

Optional:
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`

## Health Check

The Dockerfile includes a health check:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

## Production Considerations

- [ ] Add resource limits
- [ ] Configure log aggregation
- [ ] Set up SSL/TLS termination
- [ ] Add backup volumes for databases
- [ ] Configure horizontal scaling
