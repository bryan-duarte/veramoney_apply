# Langfuse Self-Hosted Architecture Report

**Date:** 2026-02-18
**Langfuse Version:** v3.153.0
**Purpose:** Technical reference for self-hosted Langfuse deployment

---

## Executive Summary

Langfuse v3 requires **ClickHouse as a mandatory dependency** for all self-hosted deployments. The application will not start without a valid ClickHouse connection. There is no PostgreSQL-only mode available.

---

## Architecture Overview

### Required Services

| Service | Image | Purpose | Required |
|---------|-------|---------|----------|
| `langfuse-web` | `langfuse/langfuse:3` | Main web application | Yes |
| `langfuse-worker` | `langfuse/langfuse-worker:3` | Background job processing | Yes |
| `postgres` | `postgres:17` | Metadata storage | Yes |
| `clickhouse` | `clickhouse/clickhouse-server` | Observability data storage | Yes |
| `redis` | `redis:7` | Job queue and caching | Yes |
| `minio` | MinIO or S3-compatible | Event blob storage | Yes |

### Data Storage Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Langfuse v3 Architecture                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐     ┌──────────────┐                      │
│  │  langfuse-web│     │langfuse-worker│                     │
│  └──────┬───────┘     └──────┬───────┘                      │
│         │                    │                               │
│         ▼                    ▼                               │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐ │
│  │   PostgreSQL │     │   ClickHouse │     │    Redis     │ │
│  │              │     │              │     │              │ │
│  │ • Users      │     │ • Traces     │     │ • Job Queue  │ │
│  │ • Projects   │     │ • Observations│    │ • Caching    │ │
│  │ • Prompts    │     │ • Scores     │     │              │ │
│  │ • API Keys   │     │ • Analytics  │     │              │ │
│  │ • Config     │     │ • Sessions   │     │              │ │
│  └──────────────┘     └──────────────┘     └──────────────┘ │
│                              │                               │
│                              ▼                               │
│                       ┌──────────────┐                      │
│                       │   MinIO/S3   │                      │
│                       │              │                      │
│                       │ • Event blobs│                      │
│                       │ • File storage│                     │
│                       └──────────────┘                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## ClickHouse Role in Langfuse

### Tables and Purpose

| Table | Purpose | Key Data |
|-------|---------|----------|
| `traces` | LLM trace storage | id, timestamp, name, user_id, metadata, input, output, session_id, tags |
| `observations` | Individual observations | trace_id, type (SPAN/GENERATION/EVENT), start_time, end_time, input, output, usage_details, cost_details, model_parameters |
| `scores` | Evaluation scores | trace_id, observation_id, name, value, source, comment, data_type |
| `blob_storage_file_log` | S3 event log | File references for event ingestion |
| `event_log` | Event processing log | Internal event queue |

### Functionality Powered by ClickHouse

1. **Trace and observation queries** - All LLM call data retrieval
2. **Usage analytics** - Token counts, costs, model usage statistics
3. **Session management** - Conversation history and context
4. **Evaluation storage** - Scores, comments, and feedback
5. **Dashboard metrics** - Performance charts, aggregations, trends

---

## Required Environment Variables

### ClickHouse Configuration (Mandatory)

```bash
CLICKHOUSE_URL=http://clickhouse:8123
CLICKHOUSE_MIGRATION_URL=clickhouse://clickhouse:9000
CLICKHOUSE_USER=clickhouse
CLICKHOUSE_PASSWORD=clickhouse
CLICKHOUSE_DB=default
CLICKHOUSE_CLUSTER_ENABLED=false
CLICKHOUSE_CLUSTER_NAME=default
```

### Optional ClickHouse Variables

```bash
CLICKHOUSE_READ_ONLY_URL=         # For read replicas
CLICKHOUSE_EVENTS_READ_ONLY_URL=  # For events read replicas
```

### Complete Required Environment

```bash
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/postgres
SALT=<generate-with-openssl-rand-hex-32>
ENCRYPTION_KEY=<64-char-hex-string>
NEXTAUTH_SECRET=<generate-with-openssl-rand-hex-32>
NEXTAUTH_URL=http://localhost:3000

CLICKHOUSE_URL=http://clickhouse:8123
CLICKHOUSE_MIGRATION_URL=clickhouse://clickhouse:9000
CLICKHOUSE_USER=clickhouse
CLICKHOUSE_PASSWORD=clickhouse
CLICKHOUSE_CLUSTER_ENABLED=false

LANGFUSE_S3_EVENT_UPLOAD_BUCKET=langfuse
LANGFUSE_S3_EVENT_UPLOAD_REGION=auto
LANGFUSE_S3_EVENT_UPLOAD_ACCESS_KEY_ID=minio
LANGFUSE_S3_EVENT_UPLOAD_SECRET_ACCESS_KEY=miniosecret
LANGFUSE_S3_EVENT_UPLOAD_ENDPOINT=http://minio:9000
LANGFUSE_S3_EVENT_UPLOAD_FORCE_PATH_STYLE=true
LANGFUSE_S3_EVENT_UPLOAD_PREFIX=events/

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_AUTH=myredissecret
```

---

## Minimal Docker Compose Configuration

```yaml
services:
  langfuse-worker:
    image: docker.io/langfuse/langfuse-worker:3
    restart: always
    depends_on:
      postgres:
        condition: service_healthy
      minio:
        condition: service_healthy
      redis:
        condition: service_healthy
      clickhouse:
        condition: service_healthy
    environment: &langfuse-env
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/postgres
      SALT: "change-me-generate-with-openssl-rand-hex-32"
      ENCRYPTION_KEY: "0000000000000000000000000000000000000000000000000000000000000000"
      NEXTAUTH_SECRET: "change-me-generate-with-openssl-rand-hex-32"
      NEXTAUTH_URL: http://localhost:3000
      CLICKHOUSE_MIGRATION_URL: clickhouse://clickhouse:9000
      CLICKHOUSE_URL: http://clickhouse:8123
      CLICKHOUSE_USER: clickhouse
      CLICKHOUSE_PASSWORD: clickhouse
      CLICKHOUSE_CLUSTER_ENABLED: "false"
      LANGFUSE_S3_EVENT_UPLOAD_BUCKET: langfuse
      LANGFUSE_S3_EVENT_UPLOAD_REGION: auto
      LANGFUSE_S3_EVENT_UPLOAD_ACCESS_KEY_ID: minio
      LANGFUSE_S3_EVENT_UPLOAD_SECRET_ACCESS_KEY: miniosecret
      LANGFUSE_S3_EVENT_UPLOAD_ENDPOINT: http://minio:9000
      LANGFUSE_S3_EVENT_UPLOAD_FORCE_PATH_STYLE: "true"
      LANGFUSE_S3_EVENT_UPLOAD_PREFIX: events/
      REDIS_HOST: redis
      REDIS_PORT: 6379
      REDIS_AUTH: myredissecret

  langfuse-web:
    image: docker.io/langfuse/langfuse:3
    restart: always
    depends_on:
      postgres:
        condition: service_healthy
      minio:
        condition: service_healthy
      redis:
        condition: service_healthy
      clickhouse:
        condition: service_healthy
    ports:
      - "3000:3000"
    environment:
      <<: *langfuse-env
      LANGFUSE_INIT_PROJECT_PUBLIC_KEY: pk-your-key
      LANGFUSE_INIT_PROJECT_SECRET_KEY: sk-your-key

  clickhouse:
    image: docker.io/clickhouse/clickhouse-server
    restart: always
    user: "101:101"
    environment:
      CLICKHOUSE_DB: default
      CLICKHOUSE_USER: clickhouse
      CLICKHOUSE_PASSWORD: clickhouse
    volumes:
      - langfuse_clickhouse_data:/var/lib/clickhouse
    healthcheck:
      test: wget --no-verbose --tries=1 --spider http://localhost:8123/ping || exit 1
      interval: 5s
      timeout: 5s
      retries: 10

  postgres:
    image: docker.io/postgres:17
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 3s
      timeout: 3s
      retries: 10
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: postgres
    volumes:
      - langfuse_postgres_data:/var/lib/postgresql/data

  redis:
    image: docker.io/redis:7
    restart: always
    command: >
      --requirepass myredissecret
      --maxmemory-policy noeviction
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 3s
      timeout: 10s
      retries: 10

  minio:
    image: cgr.dev/chainguard/minio
    restart: always
    entrypoint: sh
    command: -c 'mkdir -p /data/langfuse && minio server --address ":9000" --console-address ":9001" /data'
    environment:
      MINIO_ROOT_USER: minio
      MINIO_ROOT_PASSWORD: miniosecret
    volumes:
      - langfuse_minio_data:/data
    healthcheck:
      test: ["CMD", "mc", "ready", "local"]
      interval: 1s
      timeout: 5s
      retries: 5

volumes:
  langfuse_postgres_data:
  langfuse_clickhouse_data:
  langfuse_minio_data:
```

---

## Resource Requirements

### Minimum Requirements

| Service | CPU | RAM | Storage |
|---------|-----|-----|---------|
| langfuse-web | 0.5 | 512MB | - |
| langfuse-worker | 0.5 | 512MB | - |
| postgres | 0.5 | 512MB | 10GB |
| clickhouse | 1 | 2GB | 20GB (SSD) |
| redis | 0.25 | 256MB | 1GB |
| minio | 0.25 | 256MB | 10GB |

### Production Recommendations

| Service | CPU | RAM | Storage |
|---------|-----|-----|---------|
| langfuse-web | 2 | 2GB | - |
| langfuse-worker | 2 | 2GB | - |
| postgres | 2 | 4GB | 50GB SSD |
| clickhouse | 4 | 8GB | 100GB SSD |
| redis | 1 | 1GB | 5GB |
| minio | 1 | 1GB | 100GB |

---

## Official References

| Source | URL |
|--------|-----|
| Official docker-compose.yml | https://github.com/langfuse/langfuse/blob/main/docker-compose.yml |
| Environment schema (source) | https://github.com/langfuse/langfuse/blob/main/packages/shared/src/env.ts |
| Self-hosting docs | https://langfuse.com/docs/deployment/self-host |
| Local deployment | https://langfuse.com/self-hosting/local |
| GitHub repository | https://github.com/langfuse/langfuse |

---

## Key Findings

1. **ClickHouse is mandatory** - No fallback mode exists
2. **No PostgreSQL-only mode** - ClickHouse stores all observability data
3. **6 services required** - web, worker, postgres, clickhouse, redis, minio
4. **Health checks are critical** - Use `condition: service_healthy` for dependencies
5. **S3-compatible storage required** - MinIO or external S3 for event blobs

---

## Alternatives Considered

| Option | Viable? | Notes |
|--------|---------|-------|
| Remove ClickHouse | No | Application won't start |
| PostgreSQL-only mode | No | Not available in v3 |
| External ClickHouse | Yes | Can use managed ClickHouse services |
| External S3 instead of MinIO | Yes | Configure AWS S3, GCS, or Azure Blob |
| Langfuse Cloud | Yes | Managed service, no infrastructure needed |
