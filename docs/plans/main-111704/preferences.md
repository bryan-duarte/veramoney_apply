# User Preferences & Decisions

## Configuration Preferences

- **Context Level**: Profundo (8-12+ parallel exploration tasks)
- **Participation Level**: Equilibrado (8-15 questions, agent decides implementation details)
- **Detail Level**: Pseudocode (guidelines/lineaments only, no specific code proposals)
- **Extras**: No tests, no documentation tasks

## Q&A and Rationale

### Dependency Injection Pattern

**Q:** How should we handle the current global singleton pattern (memory store, knowledge client, Langfuse)?

**A:** Manual DI with optional constructor injection

**Decision:** Use constructor injection pattern with optional defaults:
```python
class MyService:
    def __init__(self, dependency: Dependency = None):
        self._dependency = dependency or DefaultDependency()
```

**Rejected:** Full DI library (dependency-injector) - adds complexity without benefit for this project size.

**Benefits:**
- No DI framework required
- Easy to test (inject mocks)
- Self-documenting (clear dependencies in __init__)
- Works with any framework

---

### Tool Pattern

**Q:** How should tools be migrated to OOP?

**A:** Keep Current Structure (client class + @tool function)

**Decision:** Maintain the current pattern where each tool has:
- A client class (WeatherAPIClient, FinnhubClient)
- A @tool decorated function (get_weather, get_stock_price)
- Schema classes for validation

**Rejected:** BaseTool abstract class - would require custom LangChain integration, adds complexity.

---

### Endpoint Refactoring

**Q:** How should chat endpoints be refactored?

**A:** Base Handler Class

**Decision:** Create `ChatHandlerBase` class with shared logic:
- Session initialization
- Memory store access
- Langfuse client access
- Tool inference
- Dataset collection

**Rejected:** Service functions (less OOP), Full endpoint classes (too much boilerplate).

---

### API Client Inheritance

**Q:** Should we create a base class for WeatherAPIClient and FinnhubClient?

**A:** Keep Separate Clients

**Decision:** Maintain separate client classes without inheritance. They already share similar patterns but have domain-specific error handling.

**Rejected:** BaseAPIClient (over-abstraction for 2 clients), Generic APIClient (loses domain specificity).

---

### RAG Pipeline

**Q:** How should the 152-line RAG pipeline function be migrated?

**A:** Class with Methods

**Decision:** Create `RAGPipeline` class with:
- `initialize()` - Set up vector store
- `load_documents()` - Download and chunk documents
- `get_retriever()` - Return configured retriever
- `get_status()` - Return pipeline status

**Rejected:** Pipeline Steps (over-engineering), Keep Function (no improvement).

---

### Agent Middleware

**Q:** Should middleware be migrated to classes?

**A:** Keep Decorators (Recommended)

**Decision:** Maintain current LangChain decorator pattern:
- `@wrap_model_call` for logging_middleware
- `@wrap_tool_call` for tool_error_handler
- `@after_model` for guardrails

**Rejected:** Class-based middleware - LangChain requires decorator pattern.

---

## Design Constraints

1. **No Logic Changes**: Methods must stay functionally identical
2. **Async-First**: All I/O remains async (no synchronous code)
3. **No Comments**: Self-documenting code only
4. **Preserve LangChain Integration**: @tool and middleware decorators unchanged
5. **No External DI Framework**: Use manual constructor injection
