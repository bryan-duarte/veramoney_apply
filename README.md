# VeraMoney Apply

AI-powered service with LLM-based agents, tool integration, and retrieval-augmented generation (RAG) capabilities in a regulated fintech environment.

---

## Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| **Language** | Python | 3.11+ |
| **API Framework** | FastAPI | >=0.129.0 |
| **ASGI Server** | Uvicorn | >=0.41.0 |
| **Agent Framework** | LangChain | >=1.2.10 |
| **LLM Integration** | langchain-openai | >=1.1.10 |
| **Vector Database** | ChromaDB | >=1.5.0 |
| **Data Validation** | Pydantic | >=2.12.5 |
| **Observability** | Langfuse | >=3.14.3 |
| **Package Manager** | uv | Fast Python package installer |

---

## Project Structure

```
veramoney-apply/
├── main.py                    # Entry point for the application
├── pyproject.toml             # Project configuration and dependencies
├── Dockerfile                 # Multi-stage Docker build
├── docker-compose.yml         # Full observability stack
├── .env.example               # Environment variables template
│
├── src/
│   ├── api/                   # API layer (implemented)
│   │   ├── main.py            # FastAPI app factory with middleware
│   │   ├── dependencies.py    # Dependency injection
│   │   └── endpoints/
│   │       └── chat.py        # /chat endpoint
│   │
│   ├── agent/                 # Agent layer (pending)
│   │   └── multi_agent/
│   │       └── workers/
│   │
│   ├── tools/                 # Tools layer (pending)
│   │   ├── weather/
│   │   └── stock/
│   │
│   ├── rag/                   # RAG pipeline (pending)
│   │
│   ├── observability/         # Observability layer (pending)
│   │
│   └── config/                # Configuration layer (implemented)
│
└── docs/
    ├── challenge_tasks/       # Challenge requirements
    ├── plans/                 # Implementation plans
    └── reports/               # Analysis reports
```

---

## Implementation Status

| Layer | Status | Location |
|-------|--------|----------|
| **API Layer** | Implemented | `src/api/` |
| **Configuration** | Implemented | `src/config/` |
| **Agent Layer** | Pending | `src/agent/` |
| **Tools Layer** | Pending | `src/tools/` |
| **RAG Pipeline** | Pending | `src/rag/` |
| **Observability** | Pending | `src/observability/` |

---

## Quick Start

### 1. Install Dependencies

```bash
uv sync
source .venv/bin/activate
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and set the required values:

```bash
# REQUIRED
API_KEY=your-secret-api-key-here
OPENAI_API_KEY=sk-your-openai-key-here
```

### 3. Run the Application

```bash
# Option A: Using Python directly
python main.py

# Option B: Using uvicorn with hot reload (recommended)
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Run with Docker (Full Stack)

```bash
docker-compose up -d
docker-compose logs -f app
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/chat` | POST | Send message to AI assistant |

---

## Testing the Chat Endpoint

### Health Check

```bash
curl http://localhost:8000/health
```

### Chat Endpoint

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key-here" \
  -d '{
    "message": "What is the weather in Montevideo?",
    "session_id": "123e4567-e89b-12d3-a456-426614174000"
  }'
```

**Replace** `your-secret-api-key-here` with the value you set for `API_KEY` in your `.env` file.

### Request Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | `string` | **Yes** | User message (1-32000 characters) |
| `session_id` | `string` | No | UUID for conversation continuity |

### Response Format

```json
{
  "response": "The assistant's response text",
  "tool_calls": [
    {
      "tool": "weather",
      "input": {"city": "Montevideo"}
    }
  ]
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Invalid request body |
| 401 | Invalid or missing `X-API-Key` header |
| 429 | Rate limit exceeded (60 req/min default) |
| 500 | Internal server error |

---

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `API_KEY` | Secret API key for request authentication |
| `OPENAI_API_KEY` | OpenAI API key for LLM and embedding models |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | Deployment stage (development, qa, production) |
| `LOG_LEVEL` | `info` | Logging level |
| `APP_PORT` | `8000` | Server port |
| `CORS_ORIGINS` | `""` | Comma-separated allowed CORS origins |
| `RATE_LIMIT_PER_MINUTE` | `60` | Rate limit per API key |
| `OPENAI_MODEL` | `gpt-5-mini-2025-08-07` | Chat model name |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model name |

### Langfuse (Optional)

| Variable | Description |
|----------|-------------|
| `LANGFUSE_PUBLIC_KEY` | Langfuse public key |
| `LANGFUSE_SECRET_KEY` | Langfuse secret key |
| `LANGFUSE_HOST` | Langfuse server URL |

---

## Quick Test Script

```bash
#!/bin/bash
API_KEY="your-secret-api-key-here"
BASE_URL="http://localhost:8000"

echo "Testing health endpoint..."
curl -s "$BASE_URL/health" | jq .

echo -e "\nTesting chat endpoint..."
curl -s -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"message": "Hello, how are you?"}' | jq .
```

---

## API Documentation

Once the server is running, access the interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
