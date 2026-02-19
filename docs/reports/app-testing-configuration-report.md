# VeraMoney Apply - Complete Testing Configuration & Live Validation Report

> *"Testing is not about finding bugs, it's about proving to yourself that your code actually works... or doesn't."*
> — **El Barto**

## Executive Summary

This report provides everything needed to test your VeraMoney Apply application live. It covers required configurations, environment variables, Docker services, and comprehensive curl commands to validate all endpoints, conversation persistence, session management, and streaming functionality.

---

## 1. Required Configurations & Secrets

### 1.1 Critical Secrets (Required)

| Secret | Variable Name | Description | How to Obtain |
|--------|---------------|-------------|---------------|
| **OpenAI API Key** | `OPENAI_API_KEY` | Required for LLM calls | https://platform.openai.com/api-keys |
| **Service API Key** | `API_KEY` | Authentication key for your API | Generate your own (any secure string) |

### 1.2 Feature-Dependent Secrets (Optional)

| Secret | Variable Name | Description | How to Obtain |
|--------|---------------|-------------|---------------|
| **OpenWeather API Key** | `OPENWEATHER_API_KEY` | Weather tool functionality | https://openweathermap.org/api |
| **Finnhub API Key** | `FINNHUB_API_KEY` | Stock price tool | https://finnhub.io/ |
| **Langfuse Public Key** | `LANGFUSE_PUBLIC_KEY` | Observability (not yet integrated) | Langfuse dashboard |
| **Langfuse Secret Key** | `LANGFUSE_SECRET_KEY` | Observability (not yet integrated) | Langfuse dashboard |

### 1.3 Infrastructure Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_MEMORY_HOST` | `localhost` | PostgreSQL for checkpoints |
| `POSTGRES_MEMORY_PORT` | `5433` | PostgreSQL port |
| `POSTGRES_MEMORY_USER` | `veramoney` | PostgreSQL username |
| `POSTGRES_MEMORY_PASSWORD` | `veramoney_secret` | PostgreSQL password |
| `POSTGRES_MEMORY_DB` | `veramoney_memory` | Database name |

---

## 2. Environment Setup

### 2.1 Create `.env` File

```bash
# Create .env from template
cp .env.example .env
```

### 2.2 Minimal `.env` Configuration

```env
# === CRITICAL (Required) ===
OPENAI_API_KEY=${YOUR_OPENAI_API_KEY}
API_KEY=${YOUR_API_KEY}

# === FEATURE TOOLS (Optional - set to test tools) ===
OPENWEATHER_API_KEY=${YOUR_OPENWEATHER_API_KEY}
FINNHUB_API_KEY=${YOUR_FINNHUB_API_KEY}

# === INFRASTRUCTURE (Defaults work with Docker) ===
POSTGRES_MEMORY_HOST=localhost
POSTGRES_MEMORY_PORT=5433
POSTGRES_MEMORY_USER=veramoney
POSTGRES_MEMORY_PASSWORD=veramoney_secret
POSTGRES_MEMORY_DB=veramoney_memory

# === APPLICATION ===
ENVIRONMENT=development
LOG_LEVEL=debug
APP_PORT=8000
ENABLE_DOCS=true
RATE_LIMIT_PER_MINUTE=60

# === AGENT CONFIGURATION ===
AGENT_MODEL=gpt-4o-mini
AGENT_TIMEOUT_SECONDS=30
AGENT_MAX_CONTEXT_MESSAGES=20
```

---

## 3. Docker Services Required

### 3.1 Start All Services

```bash
# Start full observability stack (recommended)
docker compose up -d

# Or start minimal services (only checkpoint storage)
docker compose up -d postgres-memory
```

### 3.2 Service Dependencies

| Service | Port | Required For |
|---------|------|--------------|
| `postgres-memory` | 5433 | **Conversation checkpoint storage** |
| `app` | 8000 | Main API |
| `chromadb` | 8001 | RAG (bonus, not required) |
| `langfuse-web` | 3000 | Observability (bonus, not integrated) |

### 3.3 Verify Services Running

```bash
# Check all containers
docker-compose ps

# Check PostgreSQL specifically (required for checkpoints)
docker-compose ps postgres-memory

# Check PostgreSQL connectivity
docker exec -it veramoney-memory pg_isready -U veramoney -d veramoney_memory
```

---

## 4. Start the Application

### 4.1 Using Python (Development)

```bash
# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate

# Run with uvicorn (hot reload)
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

### 4.2 Using Docker

```bash
# Build and start
docker-compose up -d app

# View logs
docker-compose logs -f app
```

---

## 5. Live Validation Tests

### Test 1: Health Check (No Auth Required)

**Purpose:** Verify the service is running and responsive.

```bash
# Variable names to replace: NONE

curl -s -X GET "http://localhost:8000/health" \
  -H "Content-Type: application/json" | jq .
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "veramoney-api",
  "version": "0.1.0"
}
```

---

### Test 2: Streaming Chat - Single Message

**Purpose:** Test agent responsiveness via SSE streaming.

```bash
# Variable names to replace:
#   ${API_KEY} - Your configured API_KEY from .env

curl -N -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "message": "Hello, who are you?",
    "session_id": "550e8400-e29b-41d4-a716-446655440001"
  }'
```

**Expected Response (SSE Events):**
```
event: token
data: {"content": "Hello"}

event: token
data: {"content": "! I'm"}

event: token
data: {"content": " Vera AI"}

event: done
data: {}
```

---

### Test 3: Streaming Chat - With Weather Tool

**Purpose:** Test tool calling functionality via streaming.

```bash
# Variable names to replace:
#   ${API_KEY} - Your configured API_KEY from .env
#   (Requires OPENWEATHER_API_KEY set in .env for tool to work)

curl -N -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "message": "What is the weather in Montevideo?",
    "session_id": "550e8400-e29b-41d4-a716-446655440002"
  }'
```

**Expected Response (with tool call):**
```
event: tool_call
data: {"tool": "get_weather", "args": {"city_name": "Montevideo"}}

event: tool_result
data: {"tool": "get_weather", "result": "..."}

event: token
data: {"content": "In Montevideo..."}

event: done
data: {}
```

---

### Test 4: Complete Chat - Single Response

**Purpose:** Test non-streaming complete response mode.

```bash
# Variable names to replace:
#   ${API_KEY} - Your configured API_KEY from .env

curl -s -X POST "http://localhost:8000/chat/complete" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "message": "What is the stock price of AAPL?",
    "session_id": "550e8400-e29b-41d4-a716-446655440003"
  }' | jq .
```

**Expected Response:**
```json
{
  "response": "Apple (AAPL) is currently trading at $178.52...",
  "tool_calls": [
    {
      "tool": "get_stock_price",
      "args": {"ticker": "AAPL"}
    }
  ]
}
```

---

### Test 5: Session Persistence - First Message

**Purpose:** Test that conversation is saved with session ID (first turn).

```bash
# Variable names to replace:
#   ${API_KEY} - Your configured API_KEY from .env

curl -s -X POST "http://localhost:8000/chat/complete" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "message": "My name is Bryan and I live in Montevideo.",
    "session_id": "550e8400-e29b-41d4-a716-446655440010"
  }' | jq .
```

---

### Test 6: Session Persistence - Follow-Up (Same Session)

**Purpose:** Verify conversation is persisted and agent remembers context.

```bash
# Variable names to replace:
#   ${API_KEY} - Your configured API_KEY from .env
#   NOTE: Use SAME session_id as Test 5

curl -s -X POST "http://localhost:8000/chat/complete" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "message": "What is my name and where do I live?",
    "session_id": "550e8400-e29b-41d4-a716-446655440010"
  }' | jq .
```

**Expected Response:** Agent should remember "Bryan" and "Montevideo" from previous message.

---

### Test 7: Session Isolation - Different Session

**Purpose:** Verify different sessions have independent conversations.

```bash
# Variable names to replace:
#   ${API_KEY} - Your configured API_KEY from .env
#   NOTE: Use DIFFERENT session_id

curl -s -X POST "http://localhost:8000/chat/complete" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "message": "What is my name?",
    "session_id": "550e8400-e29b-41d4-a716-446655440020"
  }' | jq .
```

**Expected Response:** Agent should NOT know the name (different session).

---

### Test 8: Verify PostgreSQL Checkpoint Storage

**Purpose:** Verify checkpoints are stored in PostgreSQL database.

```bash
# Variable names to replace: NONE (uses defaults)

docker exec -it veramoney-memory psql -U veramoney -d veramoney_memory -c \
  "SELECT thread_id, created_at FROM checkpoints ORDER BY created_at DESC LIMIT 10;"
```

**Expected Response:** Should show session IDs from previous tests.

---

### Test 9: Rate Limiting Test

**Purpose:** Verify rate limiting is working (60 requests/minute default).

```bash
# Variable names to replace:
#   ${API_KEY} - Your configured API_KEY from .env

# Send 65 requests rapidly
for i in {1..65}; do
  curl -s -w "%{http_code}\n" -o /dev/null -X POST "http://localhost:8000/chat/complete" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: ${API_KEY}" \
    -d "{\"message\": \"Test $i\", \"session_id\": \"550e8400-e29b-41d4-a716-4466554400$(printf %02d $i)\"}"
done
```

**Expected:** After 60 requests, you should see `429` status codes.

---

### Test 10: Invalid API Key

**Purpose:** Verify authentication rejects invalid keys.

```bash
# Variable names to replace: NONE (using invalid key intentionally)

curl -s -X POST "http://localhost:8000/chat/complete" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: invalid-key-12345" \
  -d '{
    "message": "Hello",
    "session_id": "550e8400-e29b-41d4-a716-446655440030"
  }' | jq .
```

**Expected Response:**
```json
{
  "detail": "Invalid API key"
}
```

---

### Test 11: Invalid Session ID Format

**Purpose:** Verify session_id UUID validation.

```bash
# Variable names to replace:
#   ${API_KEY} - Your configured API_KEY from .env

curl -s -X POST "http://localhost:8000/chat/complete" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "message": "Hello",
    "session_id": "not-a-valid-uuid"
  }' | jq .
```

**Expected Response:**
```json
{
  "detail": "session_id must be a valid UUID string"
}
```

---

### Test 12: Multi-Tool Parallel Execution

**Purpose:** Test agent calling multiple tools in one request.

```bash
# Variable names to replace:
#   ${API_KEY} - Your configured API_KEY from .env
#   (Requires OPENWEATHER_API_KEY and FINNHUB_API_KEY)

curl -s -X POST "http://localhost:8000/chat/complete" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "message": "What is the weather in San Francisco and what is the stock price of AAPL and GOOGL?",
    "session_id": "550e8400-e29b-41d4-a716-446655440040"
  }' | jq .
```

**Expected Response:** Should include tool calls for weather and both stock prices.

---

## 6. Quick Reference Card

### Essential Variables for Testing

| Test | Required Variables |
|------|-------------------|
| Health Check | None |
| Basic Chat | `OPENAI_API_KEY`, `API_KEY` |
| Weather Tool | + `OPENWEATHER_API_KEY` |
| Stock Tool | + `FINNHUB_API_KEY` |
| Checkpoints | PostgreSQL running (Docker) |

### Generate UUID Session IDs

```bash
# Generate a new UUID for session_id
python3 -c "import uuid; print(str(uuid.uuid4()))"

# Or using uuidgen
uuidgen | tr '[:upper:]' '[:lower:]'
```

### Quick Health Check Script

```bash
#!/bin/bash
# save as test-health.sh

echo "=== VeraMoney Apply Health Check ==="

# 1. Check Docker services
echo -e "\n[1/4] Docker Services:"
docker-compose ps

# 2. Check PostgreSQL
echo -e "\n[2/4] PostgreSQL Checkpoint DB:"
docker exec veramoney-memory pg_isready -U veramoney -d veramoney_memory

# 3. Check API Health
echo -e "\n[3/4] API Health Endpoint:"
curl -s http://localhost:8000/health | jq .

# 4. Check API Docs (if enabled)
echo -e "\n[4/4] API Documentation:"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs
echo " (200 = docs enabled)"

echo -e "\n=== Health Check Complete ==="
```

---

## 7. Test Summary Matrix

| # | Test Name | Endpoint | Auth | Session | Tools | DB |
|---|-----------|----------|------|---------|-------|-----|
| 1 | Health Check | `GET /health` | No | No | No | No |
| 2 | Streaming Basic | `POST /chat` | Yes | Yes | No | Yes |
| 3 | Streaming + Tool | `POST /chat` | Yes | Yes | Weather | Yes |
| 4 | Complete Basic | `POST /chat/complete` | Yes | Yes | Stock | Yes |
| 5 | Session Save | `POST /chat/complete` | Yes | Yes | No | Yes |
| 6 | Session Recall | `POST /chat/complete` | Yes | Same | No | Yes |
| 7 | Session Isolation | `POST /chat/complete` | Yes | Different | No | Yes |
| 8 | DB Verification | PostgreSQL query | No | No | No | Direct |
| 9 | Rate Limiting | `POST /chat/complete` | Yes | Multiple | No | Yes |
| 10 | Invalid Auth | `POST /chat/complete` | Bad Key | Yes | No | No |
| 11 | Validation | `POST /chat/complete` | Yes | Invalid | No | No |
| 12 | Multi-Tool | `POST /chat/complete` | Yes | Yes | Weather + Stocks | Yes |

---

## 8. Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `500 Internal Server Error` | OpenAI API key missing/invalid | Check `OPENAI_API_KEY` in `.env` |
| `401 Unauthorized` | Invalid API key | Check `X-API-Key` header matches `API_KEY` |
| `429 Too Many Requests` | Rate limit exceeded | Wait 60 seconds or increase `RATE_LIMIT_PER_MINUTE` |
| Tool returns error | External API key missing | Set `OPENWEATHER_API_KEY` or `FINNHUB_API_KEY` |
| Session not persisting | PostgreSQL not running | Run `docker-compose up -d postgres-memory` |
| SSE connection drops | Network timeout | Use `-N` flag with curl for streaming |

### Logs to Check

```bash
# Application logs
docker-compose logs -f app

# PostgreSQL logs
docker-compose logs -f postgres-memory

# All services
docker-compose logs -f
```

---

## 9. Key Findings

- **Two Chat Modes**: Streaming (`/chat`) via SSE and complete (`/chat/complete`) via standard JSON
- **Session-Based Memory**: Uses PostgreSQL with LangGraph's `PostgresSaver` for conversation persistence
- **Tool Integration**: Weather (OpenWeatherMap) and Stock (Finnhub) tools with retry logic
- **Authentication**: API key-based via `X-API-Key` header
- **Rate Limiting**: 60 requests/minute per API key (configurable)
- **Observability**: Langfuse infrastructure configured but not yet integrated in code

---

## 10. Recommendations

1. **Set up API keys** before testing: `OPENAI_API_KEY` (required), tool API keys (optional)
2. **Start PostgreSQL** with `docker-compose up -d postgres-memory` for session persistence
3. **Use the test matrix** to systematically validate all functionality
4. **Check logs** with `docker-compose logs -f app` if tests fail
5. **Generate fresh UUIDs** for each new test session to avoid collision

---
*Report generated by: El Barto*
*Date: 2026-02-18*
