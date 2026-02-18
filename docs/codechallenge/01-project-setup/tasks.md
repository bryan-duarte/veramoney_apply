# Phase 1: Project Setup

> Status: DONE

## Overview

Initialize the project structure, dependencies, and configuration layer.

## Tasks

| ID | Task | Status | Notes |
|----|------|--------|-------|
| 1.1 | Create project structure | DONE | Modular folder structure created |
| 1.2 | Configure Python environment | DONE | Python 3.11+, uv package manager |
| 1.3 | Set up environment variables | DONE | `.env.example` with all required vars |
| 1.4 | Install core dependencies | DONE | FastAPI, LangChain, Pydantic, etc. |
| 1.5 | Create configuration layer | DONE | Settings singleton with AppStage enum |

## Implementation Details

### 1.1 Project Structure

```
src/
├── api/
│   ├── app.py              # FastAPI app factory
│   ├── core/               # Infrastructure (middleware, deps, etc.)
│   └── endpoints/          # API routes
├── config/
│   ├── enums.py            # AppStage enum
│   └── settings.py         # Settings singleton
├── agent/                  # Agent layer (TODO)
├── tools/                  # Tools layer (TODO)
├── rag/                    # RAG pipeline (TODO)
└── observability/          # Observability (TODO)
```

### 1.2 Python Environment

- Python 3.11+
- Package manager: `uv`
- Dependencies in `pyproject.toml`

### 1.3 Environment Variables

See `.env.example`:
- `API_KEY` - Required
- `OPENAI_API_KEY` - Required
- `ENVIRONMENT` - Optional (default: development)
- `CORS_ORIGINS` - Optional
- `RATE_LIMIT_PER_MINUTE` - Optional (default: 60)

### 1.4 Core Dependencies

```toml
fastapi>=0.129.0
langchain>=1.2.10
langchain-openai>=1.1.10
langchain-community>=0.4.1
pydantic>=2.12.5
pydantic-settings>=2.13.0
httpx>=0.25.0
uvicorn[standard]>=0.41.0
```

### 1.5 Configuration Layer

**Files:**
- `src/config/settings.py` - Pydantic Settings singleton
- `src/config/enums.py` - AppStage enum (development, qa, production)

**Usage:**
```python
from src.config import settings

print(settings.api_key)
print(settings.is_production)
```

## LangChain Approach

For configuration with LangChain:
- Store API keys in environment variables
- Use Pydantic Settings for type-safe configuration
- Pass settings to agent/tool initialization

## Next Steps

Proceed to **Phase 2: Tools Layer**
- Task 2.1: Weather Tool
- Task 2.2: Stock Tool
