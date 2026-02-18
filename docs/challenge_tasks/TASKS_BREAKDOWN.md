# Code Challenge - Tasks Breakdown

A structured breakdown of all requirements into executable tasks.

---

## Phase 1: Project Setup

| ID  | Task                                    | Description                                             |
|-----|-----------------------------------------|---------------------------------------------------------|
| 1.1 | Create project structure                | Set up modular folder structure                         |
| 1.2 | Configure Python environment            | Python 3.11+, virtual environment, dependencies         |
| 1.3 | Set up environment variables            | `.env` file for API keys (OpenAI/Bedrock)               |
| 1.4 | Install core dependencies               | FastAPI, LangChain, LLM SDK, etc.                       |
| 1.5 | Create configuration layer              | Centralized config management                           |

---

## Phase 2: Tools Layer

### Task 1: Weather Tool

| ID    | Task                              | Description                                          |
|-------|-----------------------------------|------------------------------------------------------|
| 2.1.1 | Create tool schema definition     | Define input schema (city name) and output schema    |
| 2.1.2 | Implement weather fetch logic     | Call public API or create mock response              |
| 2.1.3 | Return structured JSON            | Temperature, conditions, humidity, etc.              |
| 2.1.4 | Make tool invocable               | Register as function-calling tool                    |

**Output Example:**
```json
{
  "city": "Montevideo",
  "temperature": "22°C",
  "conditions": "Partly cloudy",
  "humidity": "65%"
}
```

---

### Task 2: Stock Price Tool

| ID    | Task                              | Description                                          |
|-------|-----------------------------------|------------------------------------------------------|
| 2.2.1 | Create tool schema definition     | Define input schema (ticker symbol) and output       |
| 2.2.2 | Implement stock fetch logic       | Call public API or create mock data                  |
| 2.2.3 | Validate ticker argument          | Ensure valid ticker format                           |
| 2.2.4 | Return structured JSON            | Price, timestamp, change, etc.                       |
| 2.2.5 | Make tool invocable               | Register as function-calling tool                    |

**Output Example:**
```json
{
  "ticker": "AAPL",
  "price": 178.52,
  "currency": "USD",
  "timestamp": "2024-01-15T14:30:00Z",
  "change": "+2.34"
}
```

---

## Phase 3: Agent Layer

### Task 3: Conversational Agent

| ID    | Task                              | Description                                          |
|-------|-----------------------------------|------------------------------------------------------|
| 3.1   | Design system prompt              | Define agent behavior, capabilities, and constraints |
| 3.2   | Implement intent recognition      | Agent understands what user wants                    |
| 3.3   | Implement tool routing logic      | Decide: respond directly OR call tool                |
| 3.4   | Register tools with agent         | Connect Weather and Stock tools                      |
| 3.5   | Implement tool execution          | Call tools and capture results                       |
| 3.6   | Integrate tool outputs            | Inject tool results into final response              |
| 3.7   | Implement context management      | Maintain conversation history across turns           |
| 3.8   | Prevent hallucination             | Ensure agent only uses real tool results             |

**Agent Decision Flow:**
```
User Message
    │
    ▼
┌─────────────────┐
│ Intent Analysis │
└────────┬────────┘
         │
    ┌────┴────┬────────────┐
    ▼         ▼            ▼
 Weather   Stock      General
  Tool     Tool      Response
    │         │            │
    └────┬────┴────────────┘
         ▼
┌─────────────────┐
│ Final Response  │
└─────────────────┘
```

---

## Phase 4: API Layer

| ID  | Task                              | Description                                          |
|-----|-----------------------------------|------------------------------------------------------|
| 4.1 | Create FastAPI application        | Initialize FastAPI app                               |
| 4.2 | Create `/chat` endpoint           | POST endpoint for conversation                       |
| 4.3 | Define request schema             | `{ "message": string, "session_id"?: string }`      |
| 4.4 | Define response schema            | `{ "response": string, "tool_calls"?: array }`      |
| 4.5 | Implement session management      | Track conversation context per session               |
| 4.6 | Add error handling                | Graceful error responses                             |
| 4.7 | Add API documentation             | OpenAPI/Swagger docs                                 |

**API Example:**

Request:
```http
POST /chat
Content-Type: application/json

{
  "message": "What's the weather in Montevideo and the price of AAPL?",
  "session_id": "user-123"
}
```

Response:
```json
{
  "response": "In Montevideo, it's currently 22°C and partly cloudy. Apple (AAPL) is trading at $178.52 USD.",
  "tool_calls": [
    {"tool": "weather", "input": {"city": "Montevideo"}},
    {"tool": "stock_price", "input": {"ticker": "AAPL"}}
  ]
}
```

---

## Phase 5: Architecture & Quality

| ID  | Task                              | Description                                          |
|-----|-----------------------------------|------------------------------------------------------|
| 5.1 | Separate agent orchestration      | Agent logic in its own module                        |
| 5.2 | Separate tool definitions         | Tools in dedicated module                            |
| 5.3 | Separate API layer                | FastAPI routes in dedicated module                   |
| 5.4 | Separate configuration            | Config in dedicated module                           |
| 5.5 | Add logging                       | Log requests, tool calls, errors                     |
| 5.6 | Add error handling                | Try-catch, graceful degradation                      |

---

## Bonus Tasks (Optional)

### Bonus 1: RAG Pipeline

| ID    | Task                              | Description                                          |
|-------|-----------------------------------|------------------------------------------------------|
| B1.1  | Create knowledge documents        | 3-10 documents about Vera, fintech, policies         |
| B1.2  | Generate embeddings               | Use OpenAI embeddings or similar                     |
| B1.3  | Set up vector database            | FAISS or Chroma                                      |
| B1.4  | Store embeddings                  | Index documents in vector DB                         |
| B1.5  | Implement retrieval logic         | Similarity search for relevant docs                  |
| B1.6  | Inject context into prompt        | Add retrieved docs to system prompt                  |
| B1.7  | Add citations to responses        | Reference source documents in output                 |

---

### Bonus 2: Multi-Agent Pattern

| ID    | Task                              | Description                                          |
|-------|-----------------------------------|------------------------------------------------------|
| B2.1  | Create Router Agent               | Decides which specialized agent to use               |
| B2.2  | Create Weather Agent              | Specialized for weather queries                      |
| B2.3  | Create Stock Agent                | Specialized for stock queries                        |
| B2.4  | Create Knowledge Agent            | Specialized for RAG queries                          |
| B2.5  | Implement orchestration           | Router calls appropriate agent                       |

**Multi-Agent Flow:**
```
User Message
    │
    ▼
┌─────────────────┐
│  Router Agent   │
└────────┬────────┘
         │
    ┌────┼────┬────────────┐
    ▼    ▼    ▼            ▼
Weather Stock Knowledge General
Agent  Agent Agent       Agent
    │    │    │            │
    └────┼────┴────────────┘
         ▼
┌─────────────────┐
│ Final Response  │
└─────────────────┘
```

---

### Bonus 3: Observability

| ID    | Task                              | Description                                          |
|-------|-----------------------------------|------------------------------------------------------|
| B3.1  | Log tool calls                    | Which tool, input, output, duration                  |
| B3.2  | Log latency metrics               | Request/response time                                |
| B3.3  | Log token usage                   | Input/output tokens per request                      |
| B3.4  | (Optional) Integrate Langfuse     | Or similar telemetry platform                        |
| B3.5  | Version prompts                   | Track prompt changes over time                       |

---

## Bonus: Docker Setup

| ID    | Task                              | Description                                          |
|-------|-----------------------------------|------------------------------------------------------|
| D1    | Create Dockerfile                 | Containerize the application                         |
| D2    | Create docker-compose.yml         | Orchestrate services (app, vector DB, etc.)          |
| D3    | Configure environment             | Env vars, volumes, ports                             |
| D4    | Document Docker usage             | Build and run instructions                           |

---

## Deliverables Checklist

| ID  | Item                              | Description                                          |
|-----|-----------------------------------|------------------------------------------------------|
| ✓   | GitHub repository                 | Public or shared repo                                |
| ✓   | README.md                         | Full documentation                                   |
| ✓   | Setup instructions                | How to install and configure                         |
| ✓   | Run instructions                  | How to start the API                                 |
| ✓   | Example requests                  | curl or Postman examples                             |
| ✓   | Architecture explanation          | Diagram and description                              |
| ✓   | Design trade-offs                 | Explain decisions made                               |
| ○   | Loom video (optional)             | 5-10 min system walkthrough                          |

---

## Suggested Folder Structure

```
veramoney-apply/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py
│   │   └── conversational_agent.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base_tool.py
│   │   ├── weather_tool.py
│   │   └── stock_tool.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── routes.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   └── utils/
│       ├── __init__.py
│       └── logger.py
├── tests/
│   ├── __init__.py
│   ├── test_tools.py
│   ├── test_agents.py
│   └── test_api.py
├── docs/
│   └── knowledge_base/        # RAG documents
├── .env.example
├── requirements.txt
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Execution Order (Recommended)

1. **Phase 1** → Project setup
2. **Phase 2.1** → Weather tool
3. **Phase 2.2** → Stock tool
4. **Phase 3** → Conversational agent
5. **Phase 4** → API layer
6. **Phase 5** → Architecture cleanup
7. **Bonus tasks** → In any order (RAG, Multi-Agent, Observability, Docker)
8. **Deliverables** → README, documentation
