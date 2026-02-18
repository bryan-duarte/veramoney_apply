# VeraMoney AI Platform – Project Architecture Options

> *"Naming things is the hardest problem in computer science. Organizing them is the second."*
> — **El Barto**

## Executive Summary

This report analyzes five distinct folder structure patterns for the VeraMoney AI Platform Engineer challenge. The project requires building a conversational AI agent with tool integration (weather, stock prices), optional RAG pipeline, multi-agent patterns, and observability. Each architecture option is evaluated against Clean Code principles, Screaming Architecture philosophy, and the specific requirements of an LLM-powered fintech application.

---

## Project Requirements Summary

### Core Components Identified

| Component | Description | Complexity |
|-----------|-------------|------------|
| **Tools Layer** | Weather + Stock price retrieval tools | Medium |
| **Agent Layer** | Conversational agent with tool routing | High |
| **API Layer** | FastAPI REST endpoints | Low |
| **Configuration** | Environment variables, settings | Low |
| **RAG Pipeline** (Bonus) | Vector DB, embeddings, retrieval | High |
| **Multi-Agent** (Bonus) | Router + specialized agents | High |
| **Observability** (Bonus) | Logging, metrics, tracing | Medium |

### Architecture Expectations (from Challenge)

- Clear separation: Agent orchestration, Tool definitions, API layer, Configuration
- Modular project structure
- Environment variable usage for API keys
- Scalability thinking without over-engineering

---

## Option 1: Screaming Architecture (Feature-Based)

### Philosophy

*"The structure of the system should scream what the system does."* — Robert C. Martin

Folders are named after **business capabilities** and **use cases**, not technical layers. When you open the project, you immediately understand this is a system about weather queries, stock lookups, and conversations—not about "controllers" or "services."

### Structure

```
veramoney-apply/
├── src/
│   ├── vera_ai/                          # Main package (domain name)
│   │   │
│   │   ├── weather_lookup/               # Feature: Weather queries
│   │   │   ├── __init__.py
│   │   │   ├── tool.py                   # LangChain tool definition
│   │   │   ├── schemas.py                # Input/Output Pydantic models
│   │   │   ├── client.py                 # External API client
│   │   │   └── service.py                # Business logic
│   │   │
│   │   ├── stock_lookup/                 # Feature: Stock price queries
│   │   │   ├── __init__.py
│   │   │   ├── tool.py
│   │   │   ├── schemas.py
│   │   │   ├── client.py
│   │   │   └── service.py
│   │   │
│   │   ├── conversation/                 # Feature: Chat interactions
│   │   │   ├── __init__.py
│   │   │   ├── agent.py                  # Main conversational agent
│   │   │   ├── router.py                 # Intent routing logic
│   │   │   ├── context.py                # Conversation memory
│   │   │   └── prompts.py                # System prompts
│   │   │
│   │   ├── knowledge_retrieval/          # Feature: RAG (Bonus)
│   │   │   ├── __init__.py
│   │   │   ├── embedder.py
│   │   │   ├── retriever.py
│   │   │   ├── vector_store.py
│   │   │   └── citations.py
│   │   │
│   │   ├── api_server/                   # Feature: HTTP interface
│   │   │   ├── __init__.py
│   │   │   ├── app.py                    # FastAPI app factory
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   └── chat.py
│   │   │   └── schemas.py
│   │   │
│   │   ├── shared/                       # Cross-cutting concerns
│   │   │   ├── __init__.py
│   │   │   ├── config.py                 # Settings/configuration
│   │   │   ├── logging.py                # Observability
│   │   │   └── exceptions.py
│   │   │
│   │   └── __init__.py
│   │
├── tests/
│   ├── weather_lookup/
│   │   └── test_tool.py
│   ├── stock_lookup/
│   │   └── test_tool.py
│   ├── conversation/
│   │   └── test_agent.py
│   └── conftest.py
│
├── docs/
│   └── knowledge_base/                   # RAG documents
│
├── .env.example
├── pyproject.toml
├── Dockerfile
└── README.md
```

### Trade-offs

| Aspect | Pros | Cons |
|--------|------|------|
| **Discoverability** | Immediately clear what the system does | Requires understanding feature boundaries |
| **Modularity** | Features are self-contained, easy to extract | Shared code can create coupling |
| **Scaling** | Easy to add new features without touching others | Can lead to duplication across features |
| **Testing** | Tests mirror feature structure naturally | Integration tests span multiple features |
| **Team Scaling** | Teams can own entire features | Requires discipline to avoid cross-feature dependencies |
| **LLM Context** | Clear feature boundaries help with code navigation | May obscure architectural patterns |

### Verdict

**Best for:** Projects where business capabilities are stable and well-defined. Excellent for this challenge since the features (weather, stock, conversation) are discrete and well-bounded.

**Risk:** If features need to share significant logic, the `shared/` folder can become a dumping ground.

---

## Option 2: Clean Architecture (Layered)

### Philosophy

Dependency inversion is king. The inner layers (domain, use cases) know nothing about outer layers (frameworks, external services). This creates a system that is independent of UI, frameworks, databases, and external agencies.

### Structure

```
veramoney-apply/
├── src/
│   └── vera_ai/
│       │
│       ├── domain/                       # Core: Entities & Business Rules
│       │   ├── __init__.py
│       │   ├── entities/
│       │   │   ├── __init__.py
│       │   │   ├── weather.py
│       │   │   ├── stock.py
│       │   │   └── conversation.py
│       │   ├── value_objects/
│       │   │   ├── __init__.py
│       │   │   ├── city.py
│       │   │   └── ticker.py
│       │   └── exceptions.py
│       │
│       ├── application/                  # Core: Use Cases & Orchestration
│       │   ├── __init__.py
│       │   ├── use_cases/
│       │   │   ├── __init__.py
│       │   │   ├── get_weather.py
│       │   │   ├── get_stock_price.py
│       │   │   └── chat.py
│       │   ├── ports/                    # Interfaces (protocols)
│       │   │   ├── __init__.py
│       │   │   ├── weather_provider.py
│       │   │   ├── stock_provider.py
│       │   │   ├── llm_gateway.py
│       │   │   └── vector_store.py
│       │   └── dtos/                     # Data Transfer Objects
│       │       ├── __init__.py
│       │       └── chat_dto.py
│       │
│       ├── infrastructure/               # Outer: Implementations
│       │   ├── __init__.py
│       │   ├── adapters/
│       │   │   ├── __init__.py
│       │   │   ├── openweather_adapter.py    # Implements weather_provider
│       │   │   ├── alphavantage_adapter.py   # Implements stock_provider
│       │   │   ├── langchain_adapter.py      # Implements llm_gateway
│       │   │   └── chroma_adapter.py         # Implements vector_store
│       │   ├── persistence/
│       │   │   ├── __init__.py
│       │   │   └── session_store.py
│       │   └── config/
│       │       ├── __init__.py
│       │       └── settings.py
│       │
│       ├── presentation/                 # Outer: Entry Points
│       │   ├── __init__.py
│       │   └── api/
│       │       ├── __init__.py
│       │       ├── app.py
│       │       ├── routes/
│       │       │   └── chat.py
│       │       └── schemas.py
│       │
│       └── __init__.py
│
├── tests/
│   ├── unit/
│   │   ├── domain/
│   │   └── application/
│   ├── integration/
│   │   └── infrastructure/
│   └── conftest.py
│
├── docs/
├── .env.example
├── pyproject.toml
└── README.md
```

### Trade-offs

| Aspect | Pros | Cons |
|--------|------|------|
| **Testability** | Domain logic is trivially testable (no mocks for internal) | More test setup for outer layers |
| **Dependency Management** | Dependencies point inward, enforceable by tools | Can feel like over-engineering for small projects |
| **Framework Independence** | Can swap FastAPI for Flask, LangChain for raw API | Abstraction layers add indirection |
| **Long-term Maintenance** | Core logic is protected from external changes | Initial development is slower |
| **LLM Context** | Clear separation of concerns | More files to understand the flow |
| **Challenge Fit** | Shows architectural sophistication | May appear over-engineered for 6-10 hour project |

### Verdict

**Best for:** Systems expected to evolve significantly, swap external providers, or require rigorous testing of business rules in isolation.

**Risk:** For this specific challenge, the abstraction may be perceived as over-engineering. Use only if you can justify each layer's necessity.

---

## Option 3: Hexagonal Architecture (Ports & Adapters)

### Philosophy

Similar to Clean Architecture but emphasizes the **application core** surrounded by **adapters** that translate between the outside world and the inside. The core defines **ports** (interfaces) that **adapters** implement.

### Structure

```
veramoney-apply/
├── src/
│   └── vera_ai/
│       │
│       ├── core/                         # Hexagon Core
│       │   ├── __init__.py
│       │   ├── domain/
│       │   │   ├── __init__.py
│       │   │   ├── models.py             # Pydantic models for all entities
│       │   │   └── services/
│       │   │       ├── __init__.py
│       │   │       ├── weather_service.py
│       │   │       ├── stock_service.py
│       │   │       └── chat_service.py
│       │   │
│       │   ├── ports/                    # Interfaces (driving & driven)
│       │   │   ├── __init__.py
│       │   │   ├── inbound/              # Driving ports (APIs use these)
│       │   │   │   ├── __init__.py
│       │   │   │   └── chat_port.py
│       │   │   └── outbound/             # Driven ports (core uses these)
│       │   │       ├── __init__.py
│       │   │       ├── llm_port.py
│       │   │       ├── weather_port.py
│       │   │       ├── stock_port.py
│       │   │       └── vector_store_port.py
│       │   │
│       │   └── use_cases/
│       │       ├── __init__.py
│       │       └── chat_use_case.py
│       │
│       ├── adapters/                     # Hexagon Adapters
│       │   ├── __init__.py
│       │   ├── inbound/                  # Driving adapters
│       │   │   ├── __init__.py
│       │   │   └── fastapi_adapter/
│       │   │       ├── __init__.py
│       │   │       ├── app.py
│       │   │       └── routes.py
│       │   │
│       │   └── outbound/                 # Driven adapters
│       │       ├── __init__.py
│       │       ├── langchain_adapter/
│       │       │   ├── __init__.py
│       │       │   ├── agent.py
│       │       │   └── tools.py
│       │       ├── openweather_adapter/
│       │       │   ├── __init__.py
│       │       │   └── client.py
│       │       ├── stock_adapter/
│       │       │   ├── __init__.py
│       │       │   └── client.py
│       │       └── chroma_adapter/
│       │           ├── __init__.py
│       │           └── store.py
│       │
│       ├── configuration/
│       │   ├── __init__.py
│       │   ├── settings.py
│       │   └── container.py              # Dependency injection wiring
│       │
│       └── __init__.py
│
├── tests/
│   ├── core/
│   ├── adapters/
│   └── conftest.py
│
├── docs/
├── .env.example
├── pyproject.toml
└── README.md
```

### Trade-offs

| Aspect | Pros | Cons |
|--------|------|------|
| **Explicit Boundaries** | Very clear what is core vs adapter | More directories to navigate |
| **Swappability** | Trivial to swap LangChain for another framework | Requires defining all ports upfront |
| **Testing** | Core tested in isolation with mock ports | More test infrastructure needed |
| **Dependency Injection** | Natural fit for DI containers | DI adds complexity |
| **Visual Clarity** | Diagrams map directly to folder structure | Can feel ceremonial |
| **Challenge Fit** | Demonstrates advanced architectural thinking | Most complex option |

### Verdict

**Best for:** Projects where external dependencies are likely to change (e.g., switching from OpenAI to Bedrock, or LangChain to direct API calls).

**Risk:** The ceremony of defining ports for every external dependency may be overkill for a 6-10 hour challenge.

---

## Option 4: Package by Component (Hybrid)

### Philosophy

A pragmatic middle ground. Organize by **coarse-grained components** where each component contains its own vertical slice of functionality. Less granular than Screaming Architecture but more feature-oriented than Clean Architecture.

### Structure

```
veramoney-apply/
├── src/
│   └── vera_ai/
│       │
│       ├── tools/                        # Component: All tools
│       │   ├── __init__.py
│       │   ├── base.py                   # Base tool class/protocol
│       │   ├── weather/
│       │   │   ├── __init__.py
│       │   │   ├── tool.py
│       │   │   ├── schemas.py
│       │   │   └── client.py
│       │   └── stock/
│       │       ├── __init__.py
│       │       ├── tool.py
│       │       ├── schemas.py
│       │       └── client.py
│       │
│       ├── agent/                        # Component: Agent orchestration
│       │   ├── __init__.py
│       │   ├── conversational.py
│       │   ├── router.py
│       │   ├── prompts.py
│       │   ├── memory.py
│       │   └── multi_agent/              # Bonus: Multi-agent
│       │       ├── __init__.py
│       │       ├── supervisor.py
│       │       └── workers/
│       │           ├── __init__.py
│       │           ├── weather_agent.py
│       │           └── stock_agent.py
│       │
│       ├── rag/                          # Component: RAG Pipeline
│       │   ├── __init__.py
│       │   ├── embedder.py
│       │   ├── retriever.py
│       │   ├── store.py
│       │   └── citations.py
│       │
│       ├── api/                          # Component: HTTP API
│       │   ├── __init__.py
│       │   ├── app.py
│       │   ├── routes.py
│       │   ├── dependencies.py
│       │   └── schemas.py
│       │
│       ├── observability/                # Component: Monitoring
│       │   ├── __init__.py
│       │   ├── logging.py
│       │   ├── metrics.py
│       │   └── tracing.py
│       │
│       ├── config/                       # Component: Configuration
│       │   ├── __init__.py
│       │   └── settings.py
│       │
│       └── __init__.py
│
├── tests/
│   ├── tools/
│   ├── agent/
│   ├── rag/
│   ├── api/
│   └── conftest.py
│
├── docs/
│   └── knowledge_base/
│
├── .env.example
├── pyproject.toml
├── Dockerfile
└── README.md
```

### Trade-offs

| Aspect | Pros | Cons |
|--------|------|------|
| **Balance** | Not too granular, not too flat | May not scream "what" as loudly |
| **Scalability** | Components can grow independently | Component boundaries may blur |
| **Team Scaling** | Teams can own components | Cross-component changes more common |
| **Simplicity** | Fewer top-level directories | Less strict dependency direction |
| **LLM Context** | Moderate number of files to understand | Requires knowing component purposes |
| **Challenge Fit** | Aligns well with challenge structure | Less "architecturally pure" |

### Verdict

**Best for:** Teams that want organization without ceremony. Pragmatic choice that maps directly to the challenge's component breakdown.

**Risk:** Less architectural purity. Dependency direction is not enforced by structure.

---

## Option 5: Minimalist (Layer-First with Feature Folders)

### Philosophy

Start simple. Add structure only when complexity demands it. Avoid premature organization. This is the "you aren't gonna need it" approach to architecture.

### Structure

```
veramoney-apply/
├── src/
│   └── vera_ai/
│       │
│       ├── tools/                        # All tools, flat
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── weather.py
│       │   └── stock.py
│       │
│       ├── agent/                        # Agent logic
│       │   ├── __init__.py
│       │   ├── __init__.py
│       │   ├── agent.py
│       │   ├── prompts.py
│       │   └── memory.py
│       │
│       ├── rag/                          # RAG (if implemented)
│       │   ├── __init__.py
│       │   └── retriever.py
│       │
│       ├── api/                          # FastAPI
│       │   ├── __init__.py
│       │   ├── main.py
│       │   └── schemas.py
│       │
│       ├── config.py                     # Single config file
│       │
│       └── __init__.py
│
├── tests/
│   ├── test_tools.py
│   ├── test_agent.py
│   └── test_api.py
│
├── docs/
├── .env.example
├── pyproject.toml
└── README.md
```

### Trade-offs

| Aspect | Pros | Cons |
|--------|------|------|
| **Simplicity** | Minimal cognitive overhead | Scales poorly |
| **Speed** | Fastest to implement | Technical debt accumulates |
| **Discoverability** | Fewer places to look | Harder to find related code as project grows |
| **Refactoring** | Easy to restructure early | Painful to restructure later |
| **Challenge Fit** | Meets requirements with minimal ceremony | May signal lack of architectural thinking |
| **YAGNI Compliance** | No over-engineering | May under-engineer |

### Verdict

**Best for:** Prototypes, proof-of-concepts, or when requirements are highly uncertain.

**Risk:** The challenge explicitly evaluates "architecture" and "scalability thinking." This option may signal insufficient architectural consideration.

---

## Option 6: Domain-Driven Design (Bounded Contexts)

### Philosophy

Organize around **bounded contexts**—distinct areas of the business with their own models and logic. For this project, contexts might be: Market Data (stocks), Environmental Data (weather), and Conversation.

### Structure

```
veramoney-apply/
├── src/
│   └── vera_ai/
│       │
│       ├── contexts/                     # Bounded Contexts
│       │   │
│       │   ├── market_data/              # Context: Stock/Financial data
│       │   │   ├── domain/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── stock.py
│       │   │   │   └── ticker.py
│       │   │   ├── application/
│       │   │   │   ├── __init__.py
│       │   │   │   └── stock_service.py
│       │   │   ├── infrastructure/
│       │   │   │   ├── __init__.py
│       │   │   │   └── stock_client.py
│       │   │   └── __init__.py
│       │   │
│       │   ├── environmental_data/       # Context: Weather data
│       │   │   ├── domain/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── weather.py
│       │   │   │   └── location.py
│       │   │   ├── application/
│       │   │   │   ├── __init__.py
│       │   │   │   └── weather_service.py
│       │   │   ├── infrastructure/
│       │   │   │   ├── __init__.py
│       │   │   │   └── weather_client.py
│       │   │   └── __init__.py
│       │   │
│       │   └── conversation/             # Context: Chat/Agent
│       │       ├── domain/
│       │       │   ├── __init__.py
│       │       │   ├── message.py
│       │       │   └── session.py
│       │       ├── application/
│       │       │   ├── __init__.py
│       │       │   ├── agent.py
│       │       │   └── router.py
│       │       ├── infrastructure/
│       │       │   ├── __init__.py
│       │       │   ├── langchain_agent.py
│       │       │   └── memory_store.py
│       │       └── __init__.py
│       │
│       ├── shared_kernel/                # Shared across contexts
│       │   ├── __init__.py
│       │   ├── config.py
│       │   ├── logging.py
│       │   └── exceptions.py
│       │
│       ├── api/                          # Anti-corruption layer
│       │   ├── __init__.py
│       │   ├── app.py
│       │   └── routes.py
│       │
│       └── __init__.py
│
├── tests/
│   ├── market_data/
│   ├── environmental_data/
│   ├── conversation/
│   └── conftest.py
│
├── docs/
├── .env.example
├── pyproject.toml
└── README.md
```

### Trade-offs

| Aspect | Pros | Cons |
|--------|------|------|
| **Domain Alignment** | Structure mirrors business domains | Overkill for simple domains |
| **Future Scaling** | Contexts can become microservices | Significant upfront design |
| **Team Autonomy** | Teams can own contexts | Integration complexity |
| **Model Isolation** | Each context has its own models | Duplication across contexts |
| **Challenge Fit** | Shows DDD sophistication | Likely over-engineered for scope |

### Verdict

**Best for:** Complex domains with multiple teams and potential for microservices extraction.

**Risk:** For this challenge, DDD is almost certainly over-engineering unless you're specifically trying to demonstrate DDD knowledge.

---

## Comparative Analysis

### Quick Reference Matrix

| Option | Screams "What" | Complexity | Scalability | Challenge Fit | Recommended For |
|--------|---------------|------------|-------------|---------------|-----------------|
| **1. Screaming Architecture** | ★★★★★ | Medium | High | ★★★★★ | This challenge |
| **2. Clean Architecture** | ★★☆☆☆ | High | Very High | ★★★☆☆ | Enterprise systems |
| **3. Hexagonal** | ★★☆☆☆ | Very High | Very High | ★★☆☆☆ | Provider-agnostic systems |
| **4. Package by Component** | ★★★★☆ | Low-Medium | Medium-High | ★★★★★ | Pragmatic teams |
| **5. Minimalist** | ★★☆☆☆ | Very Low | Low | ★★☆☆☆ | Prototypes only |
| **6. DDD Bounded Contexts** | ★★★★☆ | Very High | Very High | ★★☆☆☆ | Complex domains |

### Decision Framework

```
                    Is this a prototype?
                           │
                    ┌──────┴──────┐
                    │ Yes         │ No
                    ▼             ▼
            [Option 5:     Does business domain
             Minimalist]    have clear boundaries?
                                  │
                           ┌──────┴──────┐
                           │ Yes         │ No
                           ▼             ▼
                    [Option 1 or 4]  Will providers change
                    (Screaming or     frequently?
                    Component)             │
                                   ┌──────┴──────┐
                                   │ Yes         │ No
                                   ▼             ▼
                           [Option 2 or 3]  [Option 4:
                            (Clean or        Component]
                            Hexagonal]
```

---

## Recommendations

### Primary Recommendation: Option 1 (Screaming Architecture)

**Rationale:**

1. **Challenge Alignment**: The evaluator wants to see what the system does at a glance. Screaming Architecture delivers this immediately.

2. **Clean Code Compliance**: Each feature is self-contained, follows Single Responsibility Principle, and has clear boundaries.

3. **Right-Sized Complexity**: Not over-engineered (like Hexagonal or DDD) but not under-organized (like Minimalist).

4. **Bonus Task Friendly**: Adding RAG (`knowledge_retrieval/`) or Multi-Agent (`multi_agent/` within `conversation/` or separate feature) fits naturally.

5. **Evaluates Well**: Shows architectural thinking without appearing to over-complicate a 6-10 hour project.

### Alternative Recommendation: Option 4 (Package by Component)

Choose this if:
- You prefer fewer top-level directories
- Your team has existing conventions around "components"
- You want faster initial navigation with slightly less architectural purity

### Not Recommended for This Challenge

- **Option 2 (Clean Architecture)**: Risk of appearing over-engineered
- **Option 3 (Hexagonal)**: Too much ceremony for the scope
- **Option 5 (Minimalist)**: May signal insufficient architectural thinking
- **Option 6 (DDD)**: Almost certainly over-engineered

---

## Implementation Guidance

### If You Choose Screaming Architecture (Option 1)

1. **Start with core features**: `weather_lookup/`, `stock_lookup/`, `conversation/`
2. **Add API early**: `api_server/` to validate the contract
3. **Wire dependencies through `shared/`**: Config, logging, exceptions
4. **Add bonuses as new features**: `knowledge_retrieval/` for RAG

### Critical Files to Create First

```
src/vera_ai/
├── __init__.py
├── shared/
│   ├── __init__.py
│   └── config.py              # Pydantic Settings
├── weather_lookup/
│   ├── __init__.py
│   ├── tool.py
│   └── schemas.py
├── stock_lookup/
│   ├── __init__.py
│   ├── tool.py
│   └── schemas.py
└── api_server/
    ├── __init__.py
    └── app.py
```

---

## Key Findings

1. **Screaming Architecture is the best fit** for this specific challenge, balancing clarity, modularity, and right-sized complexity.

2. **Clean Architecture and Hexagonal** are architecturally superior but risk appearing over-engineered for a 6-10 hour assessment.

3. **Minimalist approaches** may under-signal architectural competence to evaluators.

4. **The challenge explicitly evaluates architecture**—structure should demonstrate thoughtful design without unnecessary complexity.

5. **Feature-based organization** (Screaming/Component) aligns naturally with the discrete tools and agents required.

---

## Recommendations Summary

| Priority | Option | Use Case |
|----------|--------|----------|
| 1st Choice | **Screaming Architecture** | Best overall for this challenge |
| 2nd Choice | Package by Component | If you prefer fewer top-level dirs |
| 3rd Choice | Clean Architecture | If you want to showcase advanced patterns (risky) |
| Avoid | Minimalist, DDD, Hexagonal | Under/over-engineered for scope |

---

*Report generated by: El Barto*
*Date: 2026-02-17*
