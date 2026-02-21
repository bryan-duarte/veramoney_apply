<div align="center">

# VeraMoney Apply

**Production-Ready AI Assistant Platform with Multi-Agent Architecture**

*A technical assessment project demonstrating modern AI engineering practices for fintech environments*

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.129%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-1.2%2B-1C3C3C?logo=langchain&logoColor=white)](https://www.langchain.com/)
[![Code style: clean](https://img.shields.io/badge/code%20style-clean-8A2BE2)]()

[🚀 Quick Start](#-quick-start) • [📖 Documentation](#-api-documentation) • [🏗️ Architecture](#️-architecture) • [🔧 Configuration](#-configuration)

</div>

---

# Looms video

Part 1
https://www.loom.com/share/df00af7d80de4533867e09876cf3974e

Part 2
https://www.loom.com/share/083197cb72294cec854b1b910caa5c6f

---

> **⚡ Zero-Configuration Setup**
>
> Everything is automatic. The application connects to the backend seamlessly without manual configuration.
>
> **RAG Knowledge Base Auto-Population:**
> - On installation and first launch, the application checks if the knowledge base contains data
> - If empty, it automatically downloads the PDF documents from Cloudflare R2 storage links and populates the knowledge base
> - No manual intervention required — just start the application and the system self-initializes
>
> **Langfuse Auto-Configuration:**
> - On first startup, Langfuse automatically creates the organization, project, user and API keys
> - Full observability is enabled out of the box with zero manual setup
>
> **Langfuse Login Credentials:**
> - Email: `new_vera_teammate@vera.uy`
> - Password: `VeraM0neySecure2026`

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#️-architecture)
- [Prompt Architecture](#-prompt-architecture)
- [Design Trade-offs](#️-design-trade-offs)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [API Documentation](#-api-documentation)
- [Technology Stack](#️-technology-stack)
- [Project Structure](#-project-structure)
- [Docker Deployment](#-docker-deployment)
- [Observability](#-observability)
- [Langfuse Datasets](#-langfuse-datasets)
- [Security](#-security)

---

## 🎯 Overview

**VeraMoney Apply** is a technical assessment project for an AI Engineer position. It implements a production-ready AI-powered assistant service demonstrating:

<table>
<tr>
<td width="50%">

### Core Capabilities
- 🤖 **Multi-Agent Architecture** — Supervisor pattern with specialized workers
- 🔧 **Tool Integration** — Weather, stock prices, knowledge retrieval
- 📚 **RAG Pipeline** — ChromaDB-powered retrieval with citations
- 📡 **Streaming API** — Real-time SSE responses
- 📈 **Full Observability** — Langfuse tracing and prompt management

</td>
<td width="50%">

### Engineering Excellence
- ⚡ **Async-First** — 100% asynchronous I/O operations
- 🛡️ **Guardrails** — Hallucination detection and citation validation
- 🔐 **Production Security** — API keys, rate limiting, CORS
- 🐳 **Docker-Ready** — Complete containerized stack
- 📝 **Clean Code** — Type hints, Pydantic schemas, self-documenting

</td>
</tr>
</table>

---

## ✨ Features

### 🤖 Intelligent Multi-Agent System

```
┌─────────────────────────────────────────────────────────────┐
│                      SUPERVISOR AGENT                        │
│              Routes requests to specialists                  │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│    WEATHER    │ │    STOCK      │ │   KNOWLEDGE   │
│   SPECIALIST  │ │  SPECIALIST   │ │   SPECIALIST  │
│               │ │               │ │               │
│  WeatherAPI   │ │   Finnhub     │ │   ChromaDB    │
└───────────────┘ └───────────────┘ └───────────────┘
```

| Agent | Capability | Data Source |
|-------|------------|-------------|
| **Weather Specialist** | Current conditions, temperature, forecasts | WeatherAPI.com |
| **Stock Specialist** | Real-time prices, percentage changes | Finnhub API |
| **Knowledge Specialist** | Company history, regulations, policies | ChromaDB + RAG |


### 📡 Dual-Mode API

| Mode | Endpoint | Use Case |
|------|----------|----------|
| **Streaming** | `POST /chat` | Real-time token streaming, worker progress updates |
| **Batch** | `POST /chat/complete` | Complete responses, programmatic access |

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                │
│  ┌─────────────────┐              ┌─────────────────┐                   │
│  │   Chainlit UI   │              │   REST Clients  │                   │
│  │  (Port 8000)    │              │   (Any Port)    │                   │
│  └────────┬────────┘              └────────┬────────┘                   │
└───────────┼───────────────────────────────┼─────────────────────────────┘
            │        SSE Streaming          │
            ▼                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              API LAYER                                   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    FastAPI Application                           │   │
│  │  • X-API-Key Authentication  • Rate Limiting (60/min)          │   │
│  │  • SSE Streaming (/chat)     • Batch Endpoint (/chat/complete) │   │
│  │  • CORS Configuration        • Graceful Shutdown               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          AGENT LAYER                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │              SUPERVISOR + WORKER AGENTS                          │   │
│  │  Middleware: Logging → Error Handling → Guardrails → Citations  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                   │                                      │
│         ┌─────────────────────────┼─────────────────────────┐           │
│         ▼                         ▼                         ▼           │
│  ┌─────────────┐          ┌─────────────┐          ┌─────────────┐     │
│  │   Weather   │          │    Stock    │          │  Knowledge  │     │
│  │   Worker    │          │   Worker    │          │   Worker    │     │
│  └──────┬──────┘          └──────┬──────┘          └──────┬──────┘     │
│         │                        │                        │             │
│         ▼                        ▼                        ▼             │
│  [WeatherAPI]             [Finnhub]               [ChromaDB + RAG]      │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        INFRASTRUCTURE LAYER                              │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐               │
│  │  PostgreSQL   │  │   ChromaDB    │  │   Langfuse    │               │
│  │  (Memory)     │  │  (Vectors)    │  │(Observability)│               │
│  └───────────────┘  └───────────────┘  └───────────────┘               │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Agent Pattern** | Supervisor Multi-Agent | Clean delegation, context isolation, easier debugging |
| **Agent Framework** | LangChain v1 `create_agent` (The recommended method to create agents by LangChain) | Current API, middleware support, no deprecated patterns (Chains, create react agent, etc) |
| **Vector Store** | ChromaDB | Self-hosted, Docker-friendly, metadata filtering, free (The best part) |
| **Observability** | Langfuse v3 | LLM-native metrics, open-source, self-hostable (Much cheaper than LangSmith) |
| **Streaming** | Server-Sent Events | Simpler than WebSocket, fits request-response pattern, perfect for a good ux in the chat frontend |

---

## 🎭 Prompt Architecture

The multi-agent system uses a strict separation of responsibilities between the **Supervisor** and **Worker** prompts. This architecture ensures each prompt has a single, well-defined purpose with zero redundancy.

### Responsibility Separation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SUPERVISOR PROMPT                               │
│                                                                              │
│  Owns:                                                                       │
│  • ALL user-facing language (every word the user sees)                       │
│  • Request routing to workers                                                │
│  • Synthesizing structured results into natural language                     │
│  • Crafting friendly error messages from worker error types                  │
│  • Language detection and response language selection                        │
│                                                                              │
│  Never:                                                                      │
│  • Calls external APIs                                                       │
│  • Has domain-specific mappings (tickers, etc.)                              │
│  • Returns structured data                                                   │
│  • Shows error codes, JSON, or technical output                              │
│                                                                              │
│  Output: Natural language ONLY                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            ▼                       ▼                       ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│   WEATHER WORKER    │  │    STOCK WORKER     │  │  KNOWLEDGE WORKER   │
│                     │  │                     │  │                     │
│  Owns:              │  │  Owns:              │  │  Owns:              │
│  • Tool calls       │  │  • Tool calls       │  │  • Tool calls       │
│  • Data extraction  │  │  • Data extraction  │  │  • Data extraction  │
│  • Ticker mapping   │  │  • Citations        │  │                     │
│                     │  │                     │  │                     │
│  Returns:           │  │  Returns:           │  │  Returns:           │
│  Status + fields    │  │  Status + fields    │  │  Status + Sources   │
│                     │  │                     │  │                     │
│  On error returns:  │  │  On error returns:  │  │  On error returns:  │
│  ErrorType + Input  │  │  ErrorType + Input  │  │  ErrorType          │
│  (NOT full message) │  │  (NOT full message) │  │  (NOT full message) │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
```

### Worker Output Format

Workers return MINIMAL structured data. The supervisor crafts ALL user-facing text.

```
SUCCESS:
Status: success
[Domain-specific fields only]

ERROR:
Status: error
ErrorType: city_not_found | invalid_ticker | api_error
Input: [what user provided]
```

**Example flow:**

```
Worker returns:
  Status: error | ErrorType: city_not_found | Input: XYZ123

Supervisor transforms to:
  "I couldn't find weather for that location. Could you check the spelling?"
```

### Prompt File Locations

| Prompt | File | Langfuse Name |
|--------|------|---------------|
| Supervisor | `src/prompts/system.py` | `vera-supervisor-prompt` |
| Weather Worker | `src/prompts/workers.py` | `vera-weather-worker` |
| Stock Worker | `src/prompts/workers.py` | `vera-stock-worker` |
| Knowledge Worker | `src/prompts/workers.py` | `vera-knowledge-worker` |

### Key Principle

> **Workers return structured data. The supervisor owns ALL human language.**

This separation ensures:
- Zero redundancy between prompts
- Clear debugging (which layer failed?)
- Supervisor has full control over user experience
- Workers can be optimized independently for accuracy

---

## ⚖️ Design Trade-offs

This section documents the key architectural decisions, alternatives considered, and trade-offs accepted.

### 1. Supervisor Pattern vs. Router Pattern (StateGraph)

| Aspect | Supervisor (Chosen) | Router (StateGraph) |
|--------|---------------------|---------------------|
| **Implementation Complexity** | Low | Medium-High |
| **Parallel Execution** | Sequential only | Yes, parallel worker calls |
| **Latency for Multi-Source Queries** | Higher (sequential) | Lower (parallel) |
| **Debugging Ease** | Easy - clear delegation chain | Harder - concurrent state |
| **State Management** | Simpler | More complex |

**Decision:** Chose **Supervisor Pattern** for simplicity and debuggability in this demo.

**Trade-off Accepted:** Sequential execution means multi-source queries (e.g., "weather AND stock") take longer, but the code is significantly easier to maintain and debug in production.

**IMPORTANT:** If latency is going to be a key factor in a future real scenario, consider using the Router Pattern (StateGraph) for parallel execution.

---

### 2. Async-First Architecture

| Aspect | Async (Chosen) | Sync |
|--------|----------------|------|
| **Code Complexity** | Higher (async/await everywhere) | Lower |
| **Resource Efficiency** | Excellent | Good |
| **LLM API Compatibility** | Native (`ainvoke`, `astream`) | Requires wrappers |

**Decision:** Chose **100% Async** throughout the codebase.

**Trade-off Accepted:** Increased code complexity and learning curve, but essential for an I/O-bound application (LLM calls, HTTP requests, database queries).

---

### 3. Non-Blocking Guardrails vs. Hard Validation

| Aspect | Non-Blocking (Chosen) | Hard Validation |
|--------|----------------------|-----------------|
| **User Experience** | Response always returned | May fail mid-stream |
| **Hallucination Prevention** | Logging only | Blocks bad responses |
| **Production Safety** | Degraded but functional | May block legitimate responses |
| **Iterability** | Datasets for improvement | Harder to tune |

**Decision:** Chose **Non-Blocking Guardrails** that log warnings but don't block responses.

**Trade-off Accepted:** Some hallucinations may reach users, but:
1. Logs and dataset save the examples for future improvement
2. System remains available even when guardrails detect issues
3. False positives don't block legitimate responses

---

### 4. Tool-Wrapped Subagents (Agent as a tool) vs. Direct Tools

| Aspect | Tool-Wrapped (Chosen) | Direct Tools |
|--------|----------------------|--------------|
| **Abstraction Level** | High (semantic) | Low (mechanical) |
| **Error Isolation** | Worker handles own errors | Errors propagate to agent |
| **Model Cost** | Higher (multiple LLM calls) | Lower (single call) |
| **Specialization** | Domain-specific prompts | Generic handling |

**Decision:** Chose **Tool-Wrapped Subagents** where each worker has specialized prompts.

**Trade-off Accepted:** Higher token costs (each worker makes its own LLM call), but:
1. Better error isolation
2. Domain-specific prompts improve accuracy
3. Each worker can use cheaper models (`gpt-5-nano` vs `gpt-5-mini`)

---

## 🚀 Quick Start

### Prerequisites

<table>
<tr>
<td>

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-24%2B-2496ED?logo=docker&logoColor=white)
![uv](https://img.shields.io/badge/uv-0.1%2B-purple)

</td>
</tr>
</table>

### 30-Second Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/veramoney-apply.git
cd veramoney-apply

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
# OPENAI_API_KEY=sk-...
# API_KEY=your-secure-api-key

# Start all services (API, ChromaDB, Langfuse)
docker compose up -d

# Check service health
curl http://localhost:8000/health
```

### First Request

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "message": "What is the weather in Montevideo and the stock price of AAPL?",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

---

## 📦 Installation

### Docker

```bash
# Start full stack with observability
docker compose up -d

# Services available:
# - API:          http://localhost:8000
# - Chainlit UI:  http://localhost:8002
# - Langfuse:     http://localhost:3003
# - API Docs:     http://localhost:8000/docs
```

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

<table>
<tr>
<th colspan="3">🔑 Core Configuration</th>
</tr>
<tr>
<th>Variable</th>
<th>Required</th>
<th>Description</th>
</tr>
<tr>
<td><code>OPENAI_API_KEY</code></td>
<td>✅ Yes</td>
<td>OpenAI API key for LLM and embeddings</td>
</tr>
<tr>
<td><code>API_KEY</code></td>
<td>✅ Yes</td>
<td>API key for authenticating requests</td>
</tr>
<tr>
<td><code>ENVIRONMENT</code></td>
<td>❌ No</td>
<td>Application stage: development, qa, production</td>
</tr>
<tr>
<td><code>LOG_LEVEL</code></td>
<td>❌ No</td>
<td>Logging level (default: info)</td>
</tr>
</table>

<table>
<tr>
<th colspan="3">🌐 External APIs (Optional)</th>
</tr>
<tr>
<th>Variable</th>
<th>Default</th>
<th>Description</th>
</tr>
<tr>
<td><code>WEATHERAPI_KEY</code></td>
<td>None</td>
<td>WeatherAPI.com key for weather tool</td>
</tr>
<tr>
<td><code>FINNHUB_API_KEY</code></td>
<td>None</td>
<td>Finnhub key for stock price tool</td>
</tr>
</table>

<table>
<tr>
<th colspan="3">📊 Observability (Optional)</th>
</tr>
<tr>
<th>Variable</th>
<th>Default</th>
<th>Description</th>
</tr>
<tr>
<td><code>LANGFUSE_PUBLIC_KEY</code></td>
<td>None</td>
<td>Langfuse public key for tracing</td>
</tr>
<tr>
<td><code>LANGFUSE_SECRET_KEY</code></td>
<td>None</td>
<td>Langfuse secret key</td>
</tr>
<tr>
<td><code>LANGFUSE_HOST</code></td>
<td>localhost:3003</td>
<td>Langfuse server URL</td>
</tr>
</table>

### Feature Flags

| Flag | Computed From | Effect |
|------|---------------|--------|
| `docs_enabled` | `ENVIRONMENT != production` | OpenAPI documentation |
| `langfuse_enabled` | Both Langfuse keys present | Observability tracing |
| `weather_enabled` | `WEATHERAPI_KEY` present | Weather tool active |
| `stock_enabled` | `FINNHUB_API_KEY` present | Stock tool active |

---

## 📖 API Documentation

### Endpoints Overview

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/health` | ❌ | Health check for load balancers |
| `POST` | `/chat` | ✅ | Streaming chat with SSE |
| `POST` | `/chat/complete` | ✅ | Complete chat response |
| `GET` | `/docs` | ❌ | OpenAPI documentation (dev only) |
| `GET` | `/redoc` | ❌ | ReDoc documentation (dev only) |

### Chat Request Schema

```json
{
  "message": "What's the weather in Montevideo?",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `message` | string | 1-32,000 chars | User's message to the assistant |
| `session_id` | string | UUID format | Conversation thread identifier |

### Streaming Events (SSE)

```
event: token
data: {"content": "The"}

event: worker_started
data: {"worker": "ask_weather_agent", "request": "weather in Montevideo"}

event: worker_completed
data: {"worker": "ask_weather_agent", "response": "..."}

event: done
data: {}
```

| Event | Description |
|-------|-------------|
| `token` | Individual content chunk for real-time display |
| `worker_started` | Specialist agent began processing |
| `worker_completed` | Specialist agent finished |
| `tool_call` | Tool invocation (non-worker) |
| `tool_result` | Tool response (non-worker) |
| `done` | Stream completed |
| `error` | Error occurred |

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| `200` | Success |
| `400` | Invalid request body |
| `401` | Invalid or missing `X-API-Key` header |
| `429` | Rate limit exceeded (60 req/min default) |
| `500` | Internal server error |

---

## 🛠️ Technology Stack

<table>
<tr>
<th width="20%">Layer</th>
<th width="40%">Technology</th>
<th width="40%">Purpose</th>
</tr>
<tr>
<td><strong>Language</strong></td>
<td>

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)

</td>
<td>Type hints, async/await, pattern matching</td>
</tr>
<tr>
<td><strong>API Framework</strong></td>
<td>

![FastAPI](https://img.shields.io/badge/FastAPI-0.129%2B-009688?logo=fastapi&logoColor=white)

</td>
<td>Async endpoints, OpenAPI, dependency injection</td>
</tr>
<tr>
<td><strong>Agent Framework</strong></td>
<td>

![LangChain](https://img.shields.io/badge/LangChain-1.2%2B-1C3C3C)

</td>
<td>Agent creation, tools, middleware, streaming</td>
</tr>
<tr>
<td><strong>LLM Provider</strong></td>
<td>

![OpenAI](https://img.shields.io/badge/OpenAI-GPT--5-412991?logo=openai&logoColor=white)

</td>
<td>Chat completions, embeddings</td>
</tr>
<tr>
<td><strong>Vector Store</strong></td>
<td>

![ChromaDB](https://img.shields.io/badge/ChromaDB-1.5%2B-FF6B6B)

</td>
<td>Document embeddings, similarity search</td>
</tr>
<tr>
<td><strong>Memory Store</strong></td>
<td>

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%2B-4169E1?logo=postgresql&logoColor=white)

</td>
<td>Conversation persistence, LangGraph checkpointer</td>
</tr>
<tr>
<td><strong>Observability</strong></td>
<td>

![Langfuse](https://img.shields.io/badge/Langfuse-3.14%2B-000000)

</td>
<td>Tracing, prompt management, datasets</td>
</tr>
<tr>
<td><strong>UI</strong></td>
<td>

![Chainlit](https://img.shields.io/badge/Chainlit-2.0%2B-7C3AED)

</td>
<td>Conversational interface, SSE streaming</td>
</tr>
<tr>
<td><strong>Validation</strong></td>
<td>

![Pydantic](https://img.shields.io/badge/Pydantic-2.12%2B-E92063)

</td>
<td>Data contracts, schema validation</td>
</tr>
</table>

---

## 📁 Project Structure

```
veramoney-apply/
├── main.py                      # Application entry point
├── pyproject.toml               # Dependencies and project config
├── Dockerfile                   # Multi-stage production build
├── docker-compose.yml           # Full observability stack
│
├── src/
│   ├── api/                     # API Layer
│   │   ├── app.py               # FastAPI factory + lifespan
│   │   ├── schemas.py           # Request/response models
│   │   ├── core/                # Core infrastructure
│   │   │   ├── dependencies.py  # Dependency injection
│   │   │   ├── middleware.py    # Security headers
│   │   │   └── rate_limiter.py  # Rate limiting config
│   │   ├── endpoints/           # Route definitions
│   │   └── handlers/            # Business logic
│   │
│   ├── agent/                   # Agent Layer
│   │   ├── core/                # Agent factories
│   │   │   ├── factory.py       # Single agent factory
│   │   │   └── supervisor.py    # Multi-agent supervisor
│   │   ├── workers/             # Specialist workers
│   │   ├── middleware/          # Agent middleware
│   │   └── memory/              # Memory management
│   │
│   ├── tools/                   # Tools Layer
│   │   ├── weather/             # Weather tool
│   │   ├── stock/               # Stock price tool
│   │   └── knowledge/           # RAG knowledge tool
│   │
│   ├── rag/                     # RAG Pipeline
│   │   ├── pipeline.py          # Orchestration
│   │   ├── vectorstore.py       # ChromaDB manager
│   │   └── retriever.py         # Search with filtering
│   │
│   ├── observability/           # Observability Layer
│   │   ├── manager.py           # Langfuse client
│   │   ├── prompts.py           # Prompt management
│   │   └── datasets.py          # Dataset collection
│   │
│   ├── config/                  # Configuration Layer
│   │   └── settings.py          # Pydantic settings
│   │
│   └── chainlit/                # UI Layer
│       ├── app.py               # Chainlit entry point
│       └── handlers.py          # Event handlers
│
└── docs/                        # Documentation
    ├── challenge_tasks/         # Assessment requirements
    ├── reports/                 # Analysis reports
    └── knowledge_base/          # RAG documents
```

---

## 🐳 Docker Deployment

### Multi-Stage Build

The Dockerfile uses multi-stage builds for optimized images:

```bash
# Development (used by docker-compose.yml)
docker build --target development -t app:dev .
# Builds: base → deps → development (stops here)
# Skips: builder, runtime

# Production
docker build --target runtime -t app:prod .
# Builds: base → deps → builder → runtime (stops here)
# Skips: development
```

| Target | Use Case | Features |
|--------|----------|----------|
| `development` | Local dev | Hot reload, file watching, dev tools, runs as root |
| `runtime` | Production | Minimal image, non-root user, no dev tools |

**Development only:** `watchfiles`, `curl`, `--reload` flag, source code mount, root user

**Production only:** Non-root `appuser`, minimal runtime libs, no build tools (gcc, g++, make)

Docker Compose uses `target: development` by default for local development with hot reload.

### Available Services

| Service | Port | Description |
|---------|------|-------------|
| `app` | 8000 | FastAPI application |
| `chainlit` | 8002 | Conversational UI |
| `chromadb` | 8001 | Vector database |
| `postgres-memory` | 5433 | Agent memory store |
| `langfuse` | 3003 | Observability UI |

### Localhost URLs

| Service | URL | Description |
|---------|-----|-------------|
| **FastAPI App** | http://localhost:8000 | Main API backend |
| **API Docs (Swagger)** | http://localhost:8000/docs | OpenAPI documentation |
| **API Docs (ReDoc)** | http://localhost:8000/redoc | Alternative API docs |
| **Chainlit UI** | http://localhost:8002 | Conversational UI interface |
| **Langfuse** | http://localhost:3003 | Observability dashboard |

### Langfuse Login

The system automatically creates a Langfuse user on first startup.

| Field | Value |
|-------|-------|
| **Email** | `new_vera_teammate@vera.uy` |
| **Password** | `VeraM0neySecure2026` |

---

## 📊 Observability

### Langfuse Integration

The application includes comprehensive LLM observability:

| Feature | Description |
|---------|-------------|
| **Tracing** | Hierarchical traces for supervisor-worker patterns |
| **Token Tracking** | Input/output tokens per request |
| **Latency Metrics** | LLM and tool execution times |
| **Prompt Versioning** | A/B testing and rollback support |
| **Dataset Collection** | Automatic collection for evaluation |
| **Session Grouping** | Traces grouped by session for full conversation history |

### Session-Based Tracing

All traces are grouped by `session_id`, enabling full conversation inspection in Langfuse:

```
Langfuse UI → Sidebar → Sessions → Select session_id
```

This allows viewing the complete conversation flow for any user session, including all supervisor-worker interactions and tool calls.

### Trace Hierarchy

```
Trace: supervisor-{session_id}
├── Span: supervisor_model_call
│   └── Tokens: 245 input, 189 output
├── Span: tool_call (ask_weather_agent)
│   ├── Span: weather_worker_model_call
│   └── Span: tool_execution (get_weather)
├── Span: tool_call (ask_stock_agent)
│   ├── Span: stock_worker_model_call
│   └── Span: tool_execution (get_stock_price)
└── Span: tool_call (ask_knowledge_agent)
    ├── Span: knowledge_worker_model_call
    └── Span: tool_execution (search_knowledge)
```

---

## 📚 Langfuse Datasets

The application uses Langfuse datasets for automatic data collection and evaluation. Datasets store application events for analysis, testing, and prompt improvement.

### Configured Datasets

| Dataset | Purpose | Data Collected |
|---------|---------|----------------|
| **Chat Initial Message** | Captures the first user message in each conversation | User's initial query, session_id, timestamp |
| **Stock Agent Triggers** | Tracks queries that invoke the stock specialist agent | Original user question, parsed intent, ticker symbols |

### Usage

**Chat Initial Message Dataset:**
- Records every new conversation's first message
- Enables analysis of common user intents and query patterns
- Useful for identifying high-frequency topics

**Stock Agent Triggers Dataset:**
- Captures the exact question that triggered the stock sub-agent
- Helps understand how users phrase stock-related queries
- Supports evaluation of intent classification accuracy

### Accessing Datasets

Navigate to **Langfuse UI** → **Datasases** to view collected data:

```
http://localhost:3003/datasets
```

---

## 🔒 Security

### Authentication

```bash
# All API requests require X-API-Key header
curl -H "X-API-Key: your-secure-key" http://localhost:8000/chat
```

### Rate Limiting

| Scope | Default Limit | Configuration |
|-------|---------------|---------------|
| Per API Key | 60 requests/minute | `RATE_LIMIT_PER_MINUTE` |
| Per IP (fallback) | 60 requests/minute | Automatic fallback |

### Security Headers

| Header | Production Only | Purpose |
|--------|-----------------|---------|
| `X-Content-Type-Options` | ✅ Always | Prevent MIME sniffing |
| `Strict-Transport-Security` | ✅ Production | Force HTTPS |

### Best Practices

- ✅ All secrets from environment variables
- ✅ No hardcoded credentials (There are some exceptions because this is a demo)
- ✅ API documentation disabled in production
- ✅ Generic error messages (no stack traces)
- ✅ CORS with explicit origin list

---

<div align="center">

---

**Built for the Vera AI Platform Engineer Code Assessment**

[⬆ Back to Top](#veramoney-apply)

</div>
