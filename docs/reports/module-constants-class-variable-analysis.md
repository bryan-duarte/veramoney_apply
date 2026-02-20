# Module-Level Constants to Class Variables Analysis

> *"Constants at module level? How quaint. Let's give them a proper home."*
> — **El Barto**

## Executive Summary

Analyzed 60+ Python source files across 6 code regions for the pattern of module-level constants (underscore-prefixed `UPPER_CASE` variables) that could be converted to class variables. Found **31 constants** that can be safely converted to class attributes, and **23 constants** that should remain at module level due to cross-module usage or architectural constraints.

---

## Summary Table

| Region | CAN_CONVERT | KEEP_MODULE_LEVEL | Key Reason for KEEP |
|--------|-------------|-------------------|---------------------|
| **src/tools/** | 15 | 0 | — |
| **src/observability/** | 6 | 1 | Exported in `__init__.py` |
| **src/agent/** | 3 | 1 | Imported by multiple modules |
| **src/rag/** | 2 | 10 | Shared across functions/modules |
| **src/chainlit/** | 3 | 0 | — |
| **src/config/** | 2 | 0 | Function-local constants |
| **src/api/** | 0 | 11 | Static methods, Pydantic fields, cross-module |
| **TOTAL** | **31** | **23** | — |

---

## Detailed Findings: CAN_CONVERT (31 constants)

These constants are used exclusively within a single class and can be safely moved to class attributes.

### src/observability/manager.py (3 constants)

| Constant | Used By | Conversion |
|----------|---------|------------|
| `_MAX_INIT_RETRIES` | `LangfuseManager.initialize()` | `class LangfuseManager: MAX_INIT_RETRIES: int = 3` |
| `_INIT_RETRY_DELAY_SECONDS` | `LangfuseManager.initialize()` | `class LangfuseManager: INIT_RETRY_DELAY_SECONDS: int = 5` |
| `_HTTP_OK` | `LangfuseManager._check_auth()` | `class LangfuseManager: HTTP_OK: int = 200` |

### src/observability/prompts.py (1 constant)

| Constant | Used By | Conversion |
|----------|---------|------------|
| `PROMPT_TYPE` | `PromptManager` | `class PromptManager: PROMPT_TYPE: str = "text"` |

### src/observability/datasets.py (2 constants)

| Constant | Used By | Conversion |
|----------|---------|------------|
| `DATASET_USER_OPENING_MESSAGES` | `DatasetManager` | `class DatasetManager: USER_OPENING_MESSAGES: str = "..."` |
| `DATASET_STOCK_QUERIES` | `DatasetManager` | `class DatasetManager: STOCK_QUERIES: str = "..."` |

---

### src/tools/weather/client.py (7 constants)

| Constant | Used By | Conversion |
|----------|---------|------------|
| `WEATHERAPI_BASE_URL` | `WeatherAPIClient.get_current_weather()` | `class WeatherAPIClient: BASE_URL: str = "..."` |
| `DEFAULT_TIMEOUT_SECONDS` | `WeatherAPIClient.__init__()` | `class WeatherAPIClient: DEFAULT_TIMEOUT_SECONDS: int = 30` |
| `MAX_RETRIES` | `WeatherAPIClient._make_request()` | `class WeatherAPIClient: MAX_RETRIES: int = 3` |
| `INITIAL_RETRY_DELAY_SECONDS` | `WeatherAPIClient._make_request()` | `class WeatherAPIClient: INITIAL_RETRY_DELAY_SECONDS: float = 1.0` |
| `ERROR_CODE_LOCATION_NOT_FOUND` | `WeatherAPIClient._check_api_error()` | `class WeatherAPIClient: ERROR_LOCATION_NOT_FOUND: int = 1006` |
| `ERROR_CODE_INVALID_API_KEY` | `WeatherAPIClient._check_api_error()` | `class WeatherAPIClient: ERROR_INVALID_API_KEY: int = 1002` |
| `ERROR_CODE_QUOTA_EXCEEDED` | `WeatherAPIClient._check_api_error()` | `class WeatherAPIClient: ERROR_QUOTA_EXCEEDED: int = 2007` |

### src/tools/stock/client.py (4 constants)

| Constant | Used By | Conversion |
|----------|---------|------------|
| `FINNHUB_BASE_URL` | `FinnhubClient._make_request()` | `class FinnhubClient: BASE_URL: str = "..."` |
| `DEFAULT_TIMEOUT_SECONDS` | `FinnhubClient.__init__()` | `class FinnhubClient: DEFAULT_TIMEOUT_SECONDS: int = 30` |
| `MAX_RETRIES` | `FinnhubClient._make_request()` | `class FinnhubClient: MAX_RETRIES: int = 3` |
| `INITIAL_RETRY_DELAY_SECONDS` | `FinnhubClient._make_request()` | `class FinnhubClient: INITIAL_RETRY_DELAY_SECONDS: float = 1.0` |

### src/tools/stock/schemas.py (3 constants)

| Constant | Used By | Conversion |
|----------|---------|------------|
| `TICKER_MIN_LENGTH` | `StockInput.ticker` | `class StockInput: TICKER_MIN_LENGTH: int = 1` |
| `TICKER_MAX_LENGTH` | `StockInput.ticker` | `class StockInput: TICKER_MAX_LENGTH: int = 5` |
| `TICKER_PATTERN` | `StockInput.normalize_and_validate_ticker()` | `class StockInput: TICKER_PATTERN: str = r"^[A-Z]{1,5}$"` |

### src/tools/knowledge/schemas.py (2 constants)

| Constant | Used By | Conversion |
|----------|---------|------------|
| `QUERY_MIN_LENGTH` | `KnowledgeInput.query` | `class KnowledgeInput: QUERY_MIN_LENGTH: int = 3` |
| `QUERY_MAX_LENGTH` | `KnowledgeInput.query` | `class KnowledgeInput: QUERY_MAX_LENGTH: int = 500` |

---

### src/agent/middleware/tool_error_handler.py (1 constant)

| Constant | Used By | Conversion |
|----------|---------|------------|
| `TOOL_SERVICE_NAMES` | `tool_error_handler()` | Move inside function or define as function-local |

### src/agent/middleware/output_guardrails.py (1 constant)

| Constant | Used By | Conversion |
|----------|---------|------------|
| `PRICE_TOLERANCE` | `_check_stock_hallucination()` | Move inside function or define as function-local |

### src/agent/middleware/knowledge_guardrails.py (1 constant)

| Constant | Used By | Conversion |
|----------|---------|------------|
| `KNOWLEDGE_TOOL_NAME` | `_extract_knowledge_tool_results()` | Move inside function or define as function-local |

---

### src/rag/vectorstore.py (2 constants)

| Constant | Used By | Conversion |
|----------|---------|------------|
| `EMBEDDING_BATCH_SIZE` | `ChromaVectorStoreManager.add_documents()` | `class ChromaVectorStoreManager: EMBEDDING_BATCH_SIZE: int = 100` |
| `DEFAULT_RETRIEVAL_K` | `ChromaVectorStoreManager.similarity_search()` | `class ChromaVectorStoreManager: DEFAULT_RETRIEVAL_K: int = 3` |

---

### src/chainlit/handlers.py (3 constants)

| Constant | Used By | Conversion |
|----------|---------|------------|
| `TOOL_STOCK` | `ChainlitHandlers` | `class ChainlitHandlers: TOOL_STOCK: str = "stock_price"` |
| `TOOL_WEATHER` | `ChainlitHandlers` | `class ChainlitHandlers: TOOL_WEATHER: str = "get_weather"` |
| `TOOL_KNOWLEDGE` | `ChainlitHandlers` | `class ChainlitHandlers: TOOL_KNOWLEDGE: str = "search_knowledge"` |

---

### src/config/logging.py (2 constants)

| Constant | Used By | Conversion |
|----------|---------|------------|
| `_NOISY_LOGGERS` | `configure_logging()` | Move inside function |
| `_VALID_LOG_LEVELS` | `configure_logging()` | Move inside function |

---

## Detailed Findings: KEEP_MODULE_LEVEL (23 constants)

These constants must remain at module level due to cross-module usage, exports, or architectural constraints.

### Exported Constants (1)

| File | Constant | Reason |
|------|----------|--------|
| `src/observability/prompts.py` | `PROMPT_NAME_VERA_SYSTEM` | Re-exported in `__init__.py`, part of public API |

### Cross-Module Imports (1)

| File | Constant | Reason |
|------|----------|--------|
| `src/agent/core/prompts.py` | `VERA_FALLBACK_SYSTEM_PROMPT` | Imported by `src/agent/__init__.py` and `src/agent/core/__init__.py` |

### Shared Across Functions/Classes (10)

| File | Constant | Reason |
|------|----------|--------|
| `src/rag/pipeline.py` | `EXPECTED_DOCUMENT_COUNT` | Used by both `RAGPipeline` class and `initialize_rag_pipeline()` function |
| `src/rag/loader.py` | `MAX_DOWNLOAD_RETRIES` | Used by module-level function |
| `src/rag/loader.py` | `INITIAL_RETRY_DELAY_SECONDS` | Used by module-level function |
| `src/rag/loader.py` | `DOWNLOAD_TIMEOUT_SECONDS` | Shared between function and `DocumentLoader` class |
| `src/rag/splitter.py` | `TEXT_SEPARATORS` | Used by module-level function |
| `src/rag/document_configs.py` | `VERA_HISTORY_CHUNK_SIZE` | Used in `DOCUMENT_SOURCES` list |
| `src/rag/document_configs.py` | `VERA_HISTORY_CHUNK_OVERLAP` | Used in `DOCUMENT_SOURCES` list |
| `src/rag/document_configs.py` | `REGULATION_CHUNK_SIZE` | Used in `DOCUMENT_SOURCES` list |
| `src/rag/document_configs.py` | `REGULATION_CHUNK_OVERLAP` | Used in `DOCUMENT_SOURCES` list |
| `src/rag/document_configs.py` | `DOCUMENT_LANGUAGE` | Used in `DOCUMENT_SOURCES` list |

### Static Method Usage (3)

| File | Constant | Reason |
|------|----------|--------|
| `src/api/handlers/base.py` | `WEATHER_KEYWORDS` | Used by static method `infer_expected_tools()` |
| `src/api/handlers/base.py` | `STOCK_KEYWORDS` | Used by static method `infer_expected_tools()` |
| `src/api/handlers/base.py` | `KNOWLEDGE_KEYWORDS` | Used by static method `infer_expected_tools()` |

### Cross-Module Usage (1)

| File | Constant | Reason |
|------|----------|--------|
| `src/api/handlers/base.py` | `STOCK_TOOL_NAME` | Imported by `chat_complete.py` and `chat_stream.py` |

### Pydantic Field Validation (4)

| File | Constant | Reason |
|------|----------|--------|
| `src/api/endpoints/chat_complete.py` | `MESSAGE_MIN_LENGTH` | Used in Pydantic Field definition |
| `src/api/endpoints/chat_complete.py` | `MESSAGE_MAX_LENGTH` | Used in Pydantic Field definition |
| `src/api/endpoints/chat_stream.py` | `MESSAGE_MIN_LENGTH` | Used in Pydantic Field definition |
| `src/api/endpoints/chat_stream.py` | `MESSAGE_MAX_LENGTH` | Used in Pydantic Field definition |

### Module-Level Functions (3)

| File | Constant | Reason |
|------|----------|--------|
| `src/api/core/middleware.py` | `HSTS_MAX_AGE` | Used by middleware function |
| `src/api/app.py` | `_LOG_LEVEL` | Used for module-level logging setup |
| `src/api/app.py` | `OPENAPI_TAGS_METADATA` | Used by module-level function |

---

## Recommendations

### High Priority (Immediate Value)

1. **src/tools/** - All 15 constants can be converted. This provides the best ROI as these are client classes with clear encapsulation boundaries.

2. **src/observability/manager.py** - The 3 `_HTTP_*` and `_*_RETRIES` constants are classic candidates for class-level constants.

### Medium Priority

3. **src/rag/vectorstore.py** - 2 constants in `ChromaVectorStoreManager` improve encapsulation.

4. **src/chainlit/handlers.py** - 3 tool name constants logically belong to the handler class.

### Low Priority (Cosmetic)

5. **src/config/logging.py** and **src/agent/middleware/** - These are function-local constants that could simply be moved inside their functions rather than converted to class attributes.

---

## Conversion Pattern Example

**Before (current pattern):**
```python
_MAX_INIT_RETRIES = 3
_INIT_RETRY_DELAY_SECONDS = 5
_HTTP_OK = 200


class LangfuseManager:
    def __init__(self, settings: Settings):
        self._settings = settings
```

**After (recommended pattern):**
```python
class LangfuseManager:
    MAX_INIT_RETRIES: int = 3
    INIT_RETRY_DELAY_SECONDS: int = 5
    HTTP_OK: int = 200

    def __init__(self, settings: Settings):
        self._settings = settings
```

**Usage change:**
```python
# Before
for attempt in range(_MAX_INIT_RETRIES):

# After
for attempt in range(self.MAX_INIT_RETRIES):
# Or for classmethod/staticmethod:
for attempt in range(LangfuseManager.MAX_INIT_RETRIES):
```

---

*Report generated by: El Barto*
*Date: 2026-02-20*
