# RAG Implementation

## Overview

Add SSRF protection (H2) and convert magic strings to enum (L1).

## Files to Modify

- `src/rag/loader.py` - SSRF protection
- `src/rag/schemas.py` - Add PipelineStatus enum
- `src/rag/pipeline.py` - Use enum instead of strings

## Implementation Guidelines

### SSRF Protection (H2)

**Location**: `src/rag/loader.py`

**Add URL validation**:
```python
from urllib.parse import urlparse

from src.rag.document_configs import DOCUMENT_SOURCES

ALLOWED_DOMAINS: frozenset[str] = frozenset(
    {urlparse(source.url).netloc for source in DOCUMENT_SOURCES}
)

def validate_url(url: str) -> str:
    """
    Validate URL is in allowlist.

    Raises:
        ValueError: If URL is not allowed
    """
    parsed = urlparse(url)

    is_https = parsed.scheme == "https"
    if not is_https:
        raise ValueError(f"URL must use HTTPS: {url}")

    is_allowed_domain = parsed.netloc in ALLOWED_DOMAINS
    if not is_allowed_domain:
        raise ValueError(
            f"URL domain not in allowlist: {parsed.netloc}. "
            f"Allowed domains: {', '.join(sorted(ALLOWED_DOMAINS))}"
        )

    return url
```

**Update download_pdf_to_temp_file**:
```python
async def download_pdf_to_temp_file(url: str) -> Path:
    validated_url = validate_url(url)  # ADD THIS

    async for attempt in AsyncRetrying(...):
        with attempt:
            async with httpx.AsyncClient(timeout=DOWNLOAD_TIMEOUT_SECONDS) as http_client:
                response = await http_client.get(validated_url)
                ...
```

### Pipeline Status Enum (L1)

**Location**: `src/rag/schemas.py`

**Add enum**:
```python
from enum import StrEnum

class PipelineStatus(StrEnum):
    INITIALIZING = "initializing"
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"
    PARTIAL = "partial"
```

**Update RAGPipelineStatus**:
```python
class RAGPipelineStatus(BaseModel):
    status: PipelineStatus  # Changed from str
    document_count: int
    chunk_count: int
    errors: list[str]
```

### Update Pipeline

**Location**: `src/rag/pipeline.py`

**Replace magic strings**:
```python
from src.rag.schemas import PipelineStatus

# Before
self._status = RAGPipelineStatus(status="initializing", ...)

# After
self._status = RAGPipelineStatus(status=PipelineStatus.INITIALIZING, ...)
```

**All replacements**:
- `"initializing"` → `PipelineStatus.INITIALIZING`
- `"loading"` → `PipelineStatus.LOADING`
- `"ready"` → `PipelineStatus.READY`
- `"error"` → `PipelineStatus.ERROR`
- `"partial"` → `PipelineStatus.PARTIAL`

## Dependencies

- `urllib.parse` (stdlib)
- `enum` (stdlib)

## Integration Notes

- SSRF validation happens BEFORE any network request
- Allowlist is derived from existing document configs
- PipelineStatus is a StrEnum for JSON serialization compatibility
