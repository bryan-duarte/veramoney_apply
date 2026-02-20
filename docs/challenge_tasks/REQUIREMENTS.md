# VeraMoney Apply - Complete Requirements

**Assessment Type:** Take-home exercise
**Role:** AI Platform Engineer
**Estimated Time:** 6-10 hours (core), 8-12 hours (with bonuses)

---

## 1. Technical Stack Requirements

| Component | Requirement |
|-----------|-------------|
| **Language** | Python (required) |
| **LLM Provider** | OpenAI, AWS Bedrock, or equivalent |
| **Agent Framework** | LangChain (or similar orchestration framework) |
| **API Framework** | REST-based (FastAPI recommended) |
| **Vector Database** | FAISS, Chroma, or similar (if RAG implemented) |

---

## 2. Core Tasks (Mandatory)

### 2.1 Weather Tool

| Requirement ID | Description |
|----------------|-------------|
| WT-01 | Tool must accept a city name as input |
| WT-02 | Tool must return structured JSON output |
| WT-03 | Tool must be invocable through tool/function calling |
| WT-04 | Can use public API or mock the response |
| WT-05 | Proper tool schema definition |
| WT-06 | Clear separation between tool logic and agent logic |
| WT-07 | Structured output handling |
| WT-08 | Correct reasoning flow: agent → tool → final response |

### 2.2 Stock Price Tool

| Requirement ID | Description |
|----------------|-------------|
| ST-01 | Input: Stock ticker symbol (e.g., `AAPL`) |
| ST-02 | Output: Structured JSON including price and timestamp |
| ST-03 | Tool must be callable by the agent |
| ST-04 | Can use public API or mock data |
| ST-05 | Clean tool abstraction |
| ST-06 | Correct argument validation |
| ST-07 | Proper handling of tool outputs in the final response |

### 2.3 Conversational Agent

| Requirement ID | Description |
|----------------|-------------|
| CA-01 | Understanding user intent |
| CA-02 | Decision making: respond directly OR call Weather tool OR call Stock tool |
| CA-03 | Handling multi-turn conversation |
| CA-04 | Use structured tool/function calling |
| CA-05 | Avoid hallucinating tool results |
| CA-06 | Properly integrate tool outputs into the final answer |
| CA-07 | Maintain conversation context across turns |
| CA-08 | Good prompt design |
| CA-09 | Context management strategy |
| CA-10 | Tool routing logic |
| CA-11 | Behavioral consistency |
| CA-12 | Hallucination mitigation |

---

## 3. Architecture Requirements

| Requirement ID | Description |
|----------------|-------------|
| AR-01 | Clear separation between agent orchestration, tool definitions, API layer, and configuration layer |
| AR-02 | Modular project structure |
| AR-03 | Environment variable usage for API keys (never hardcoded) |
| AR-04 | Clear reasoning about design decisions |
| AR-05 | Docker-ready setup (bonus) |

---

## 4. Bonus Tasks (Strongly Valued)

### 4.1 Retrieval-Augmented Generation (RAG)

| Requirement ID | Description |
|----------------|-------------|
| RAG-01 | Create a small knowledge base (3-10 documents) |
| RAG-02 | Knowledge base topics: Vera, Fintech regulations, Internal policies (mocked) |
| RAG-03 | Generate embeddings |
| RAG-04 | Store embeddings in a vector database |
| RAG-05 | Retrieve relevant documents when appropriate |
| RAG-06 | Inject retrieved context into the prompt |
| RAG-07 | Include clear citations in responses |
| RAG-08 | Retrieval strategy |
| RAG-09 | Context injection discipline |
| RAG-10 | Citation formatting |
| RAG-11 | Hallucination reduction |
| RAG-12 | Grounded vs non-grounded reasoning |

### 4.2 Multi-Agent Pattern (MCP-style)

| Requirement ID | Description |
|----------------|-------------|
| MA-01 | Router Agent that decides which specialized agent to call |
| MA-02 | Weather Agent (specialized) |
| MA-03 | Stock Agent (specialized) |
| MA-04 | Knowledge Agent (specialized) |
| MA-05 | Supervisor or router pattern |
| MA-06 | Clean orchestration |
| MA-07 | Clear responsibility boundaries |
| MA-08 | Structured decision-making |
| MA-09 | Reasoning transparency |

### 4.3 Observability & Evaluation

| Requirement ID | Description |
|----------------|-------------|
| OBS-01 | Log tool calls |
| OBS-02 | Log latency |
| OBS-03 | Log token usage |
| OBS-04 | Optional: Integrate Langfuse Telemetry (or similar) |
| OBS-05 | Production mindset |
| OBS-06 | Cost awareness |
| OBS-07 | Debuggability |
| OBS-08 | Versioning of prompts |

---

## 5. Evaluation Criteria

### 5.1 NOT Evaluated
- UI quality
- Design polish
- Fancy frontend

### 5.2 IS Evaluated

#### Agent Design
| Criterion | Description |
|-----------|-------------|
| ED-01 | Understanding of LLM orchestration |
| ED-02 | Correct tool usage patterns |
| ED-03 | Control over model behavior |
| ED-04 | Ability to reduce hallucinations |

#### Architecture
| Criterion | Description |
|-----------|-------------|
| ED-05 | Clean modular structure |
| ED-06 | Separation of concerns |
| ED-07 | Scalability thinking |

#### AI Reliability Thinking
| Criterion | Description |
|-----------|-------------|
| ED-08 | Structured outputs |
| ED-09 | Prompt discipline |
| ED-10 | Grounded reasoning |
| ED-11 | Consistency across turns |

#### Engineering Maturity
| Criterion | Description |
|-----------|-------------|
| ED-12 | Code readability |
| ED-13 | Clear documentation |
| ED-14 | Error handling |
| ED-15 | Thoughtful trade-offs |

---

## 6. Deliverables

| Requirement ID | Description |
|----------------|-------------|
| DEL-01 | GitHub repository (or zip) |
| DEL-02 | README with setup instructions |
| DEL-03 | README with how to run the API |
| DEL-04 | README with example requests |
| DEL-05 | README with architecture explanation |
| DEL-06 | README with design trade-offs |
| DEL-07 | Optional: Short Loom video (5-10 min) explaining system design |

---

## 7. API Specification

### Chat Endpoint

```
POST /chat
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "What's the weather in Montevideo and the price of AAPL?"
}
```

**Expected Behavior:**
1. Agent identifies need for Weather tool and Stock tool
2. Calls both tools
3. Integrates structured outputs
4. Returns a clear, grounded response

---

## 8. System Capabilities

The system must expose an API that allows clients to interact with a conversational AI agent capable of:

| Capability | Priority |
|------------|----------|
| Answering general questions | Mandatory |
| Retrieving weather information | Mandatory |
| Retrieving stock prices | Mandatory |
| Using tools when necessary | Mandatory |
| Grounding responses using internal knowledge base | Optional (Bonus) |

---

## Summary Statistics

| Category | Count |
|----------|-------|
| Technical Stack Requirements | 5 |
| Weather Tool Requirements | 8 |
| Stock Tool Requirements | 7 |
| Conversational Agent Requirements | 12 |
| Architecture Requirements | 5 |
| RAG Bonus Requirements | 12 |
| Multi-Agent Bonus Requirements | 9 |
| Observability Bonus Requirements | 8 |
| Deliverables | 7 |
| Evaluation Criteria | 15 |
| **Total Requirements** | **88** |
