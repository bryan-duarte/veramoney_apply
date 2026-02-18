# Technical Assessment – AI Platform Engineer

**Estimated time:** 6–10 hours
**Type:** Take-home exercise

---

## 1. Overview

The goal of this technical assessment is to evaluate your ability to design and implement a small AI-powered system using:

- LLM-based agents
- Tool integration
- Retrieval-augmented generation (RAG)
- Structured reasoning
- Production-oriented architecture

This exercise simulates a simplified version of how AI systems are built at Vera in a regulated fintech environment. You are not expected to train models. You are expected to orchestrate intelligent systems on top of existing LLM providers.

---

## 2. Scenario

You are building a minimal AI service for Vera. The system must expose an API that allows a client to interact with a conversational AI agent capable of:

- Answering general questions
- Retrieving weather information
- Retrieving stock prices
- Using tools when necessary
- *(Optional) Grounding responses using an internal knowledge base*

---

## 3. Technical Requirements

### Stack Requirements

| Component          | Requirement                                      |
|--------------------|--------------------------------------------------|
| Language           | Python (required)                                |
| LLM Provider       | OpenAI, AWS Bedrock, or equivalent               |
| Agent Framework    | LangChain (or similar orchestration framework)   |
| API                | REST-based (FastAPI recommended)                 |
| Vector DB          | FAISS, Chroma, or similar *(if RAG implemented)* |

---

## 4. Core Tasks (Mandatory)

### Task 1 – Weather Tool

Create a tool that allows the agent to retrieve current weather information.

**Requirements:**

- The tool must accept a city name
- It must return structured JSON
- It must be invocable through tool/function calling
- You may use a public API or mock the response

**We want to see:**

- Proper tool schema definition
- Clear separation between tool logic and agent logic
- Structured output handling
- Correct reasoning flow (agent → tool → final response)

---

### Task 2 – Stock Price Tool

Create a tool that retrieves the current stock price of a ticker symbol.

**Requirements:**

- Input: Stock ticker (e.g., `AAPL`)
- Output: Structured JSON including price and timestamp
- Must be callable by the agent
- You may use a public API or mock data

**We want to see:**

- Clean tool abstraction
- Correct argument validation
- Proper handling of tool outputs in the final response

---

### Task 3 – Conversational Agent with Tool Usage

Build a conversational agent capable of:

- Understanding user intent
- Deciding whether to:
  - Respond directly
  - Call the Weather tool
  - Call the Stock tool
- Handling multi-turn conversation

**The agent must:**

- Use structured tool/function calling
- Avoid hallucinating tool results
- Properly integrate tool outputs into the final answer
- Maintain conversation context across turns

**We are evaluating:**

- Prompt design
- Context management strategy
- Tool routing logic
- Behavioral consistency
- Hallucination mitigation

---

## 5. Architecture Expectations

**We expect:**

- Clear separation between:
  - Agent orchestration
  - Tool definitions
  - API layer
  - Configuration layer
- Modular project structure
- Environment variable usage for API keys
- Clear reasoning about design decisions

**Bonus:**

- Docker-ready setup

---

## 6. Bonus Tasks (Optional – Strongly Valued)

### Bonus 1 – Retrieval-Augmented Generation (RAG)

Add a simple RAG pipeline.

**Requirements:**

- Create a small knowledge base (3–10 documents) about:
  - Vera
  - Fintech regulations
  - Internal policies (mocked)
- Generate embeddings
- Store them in a vector database
- Retrieve relevant documents when appropriate
- Inject retrieved context into the prompt
- Include clear citations in responses

**We want to evaluate:**

- Retrieval strategy
- Context injection discipline
- Citation formatting
- Hallucination reduction
- Grounded vs non-grounded reasoning

---

### Bonus 2 – Multi-Agent Pattern (MCP-style)

Implement a minimal multi-agent architecture.

**Examples:**

- A Router Agent that decides which specialized agent to call
- Separate:
  - Weather Agent
  - Stock Agent
  - Knowledge Agent
- A supervisor or router pattern

**We want to see:**

- Clean orchestration
- Clear responsibility boundaries
- Structured decision-making
- Reasoning transparency

---

### Bonus 3 – Observability & Evaluation

Implement basic observability mechanisms:

- **Log:**
  - Tool calls
  - Latency
  - Token usage
- *Optional: Integrate Langfuse Telemetry (or similar)*

**We are evaluating:**

- Production mindset
- Cost awareness
- Debuggability
- Versioning of prompts

---

## 7. What We Are Evaluating

### We are NOT evaluating:

- UI quality
- Design polish
- Fancy frontend

### We ARE evaluating:

#### Agent Design

- Understanding of LLM orchestration
- Correct tool usage patterns
- Control over model behavior
- Ability to reduce hallucinations

#### Architecture

- Clean modular structure
- Separation of concerns
- Scalability thinking

#### AI Reliability Thinking

- Structured outputs
- Prompt discipline
- Grounded reasoning
- Consistency across turns

#### Engineering Maturity

- Code readability
- Clear documentation
- Error handling
- Thoughtful trade-offs

---

## 8. Deliverables

Please submit:

- GitHub repository (or zip)
- README including:
  - Setup instructions
  - How to run the API
  - Example requests
  - Architecture explanation
  - Design trade-offs
- *(Optional) Short Loom (5–10 min) explaining your system design*

---

## 9. Example API Interaction

**Example request:**

```http
POST /chat
Content-Type: application/json
```

```json
{
  "message": "What's the weather in Montevideo and the price of AAPL?"
}
```

**Expected behavior:**

1. Agent identifies need for:
   - Weather tool
   - Stock tool
2. Calls both tools
3. Integrates structured outputs
4. Returns a clear, grounded response

---

## 10. Time Expectation

| Scope            | Estimated Time |
|------------------|----------------|
| Core tasks       | 6–8 hours      |
| With bonuses     | 8–12 hours     |

**We value:**

- Clarity over complexity
- Correctness over over-engineering
- Architecture over hacks

> **Note:** If something is unclear, document your assumptions and proceed.
