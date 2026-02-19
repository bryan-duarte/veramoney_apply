---
name: langfuse_prompt_versioning
description: Langfuse prompt management and versioning for LLM applications. Use when working with Langfuse prompts, version control, deployment labels, rollbacks, caching, or integration with LangChain. Triggers include requests to "version prompts", "manage prompts with Langfuse", "implement prompt CMS", "A/B test prompts", "deploy prompts", or "integrate Langfuse with LangChain".
---

# Langfuse Prompt Versioning

Langfuse provides a Prompt CMS (Content Management System) for managing, versioning, and deploying prompts without code changes.

## Quick Start

### Initialize Client

```python
from langfuse import get_client

langfuse = get_client()
```

### Create/Update Prompt (Auto-Versioning)

Creating a prompt with an existing `name` automatically creates a new version:

```python
langfuse.create_prompt(
    name="movie-critic",
    type="text",
    prompt="As a {{criticlevel}} movie critic, do you like {{movie}}?",
    labels=["production"],
    config={"model": "gpt-4o", "temperature": 0.7},
)
```

### Fetch and Compile

```python
prompt = langfuse.get_prompt("movie-critic")
compiled = prompt.compile(criticlevel="expert", movie="Dune 2")
```

## Core Concepts

### Prompt Object

```json
{
  "name": "movie-critic",
  "type": "text",
  "prompt": "As a {{criticLevel}} movie critic, do you like {{movie}}?",
  "config": {"model": "gpt-4o", "temperature": 0.7},
  "version": 1,
  "labels": ["production", "latest"],
  "tags": ["movies"]
}
```

| Field | Description |
|-------|-------------|
| `name` | Unique identifier within project |
| `type` | `text` or `chat` |
| `prompt` | Template with `{{variables}}` |
| `config` | Optional JSON (model params, tools) |
| `version` | Auto-incremented integer |
| `labels` | Deployment targets (`production`, `staging`, `latest`) |
| `tags` | Categories for filtering |

### Deployment Labels

Labels control which version is served:

```python
# Get production version (default)
prompt = langfuse.get_prompt("movie-critic")

# Get specific version
prompt = langfuse.get_prompt("movie-critic", version=1)

# Get by label
prompt = langfuse.get_prompt("movie-critic", label="staging")
prompt = langfuse.get_prompt("movie-critic", label="latest")
```

Built-in labels:
- `production` - Default when fetching without label
- `latest` - Most recently created version
- Custom: `staging`, `tenant-1`, `experiment-a`

### Rollbacks

Reassign the `production` label to a previous version:

```python
langfuse.update_prompt(
    name="movie-critic",
    version=1,
    new_labels=["production"],
)
```

Or via Langfuse UI - drag-and-drop labels between versions.

## Chat Prompts

```python
langfuse.create_prompt(
    name="movie-critic-chat",
    type="chat",
    prompt=[
        {"role": "system", "content": "You are an {{criticlevel}} movie critic"},
        {"role": "user", "content": "Do you like {{movie}}?"},
    ],
    labels=["production"],
)

# Fetch and compile
chat_prompt = langfuse.get_prompt("movie-critic-chat", type="chat")
compiled = chat_prompt.compile(criticlevel="expert", movie="Dune 2")
```

## Caching

Prompts are cached client-side with no latency impact after first use:

```python
# Default: 60 seconds TTL
prompt = langfuse.get_prompt("movie-critic")

# Custom TTL (5 minutes)
prompt = langfuse.get_prompt("movie-critic", cache_ttl_seconds=300)

# Disable caching (development)
prompt = langfuse.get_prompt("movie-critic", cache_ttl_seconds=0, label="latest")
```

Cache behavior:
- **Hit**: Returns immediately, no network request
- **Expired TTL**: Returns stale immediately, refreshes in background
- **High Availability**: Never blocks on network

## Fallback for 100% Availability

```python
prompt = langfuse.get_prompt(
    "movie-critic",
    fallback="Do you like {{movie}}?"
)

if prompt.is_fallback:
    print("Using fallback prompt")
```

## LangChain Integration

```python
from langfuse import get_client
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

langfuse = get_client()

# Get prompt from Langfuse
langfuse_prompt = langfuse.get_prompt("movie-critic-chat", type="chat")

# Convert to LangChain format
langchain_prompt = ChatPromptTemplate.from_messages(
    langfuse_prompt.get_langchain_prompt()
)

# Add metadata for tracing linkage
langchain_prompt.metadata = {"langfuse_prompt": langfuse_prompt}

# Use in chain
chat_llm = ChatOpenAI()
chain = langchain_prompt | chat_llm
result = chain.invoke({"movie": "Dune 2", "criticlevel": "expert"})
```

## Tracing Integration

Link prompts to traces for performance tracking:

```python
from langfuse import observe, get_client

langfuse = get_client()

@observe(as_type="generation")
def generate_response():
    prompt = langfuse.get_prompt("movie-critic")
    langfuse.update_current_generation(prompt=prompt)
```

## Webhooks

Receive real-time notifications on prompt changes:

```python
import hmac
import hashlib

def verify_langfuse_signature(raw_body: str, signature_header: str, secret: str) -> bool:
    ts_pair, sig_pair = signature_header.split(",", 1)
    timestamp = ts_pair.split("=", 1)[1]
    received_sig_hex = sig_pair.split("=", 1)[1]

    message = f"{timestamp}.{raw_body}".encode("utf-8")
    expected_sig_hex = hmac.new(
        secret.encode("utf-8"), message, hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(
        bytes.fromhex(received_sig_hex),
        bytes.fromhex(expected_sig_hex)
    )
```

## Advanced Topics

For detailed information on:
- **A/B Testing**: See [references/ab_testing.md](references/ab_testing.md)
- **Message Placeholders**: See [references/placeholders.md](references/placeholders.md)
- **Prompt Composability**: See [references/composability.md](references/composability.md)

## Sources

- [Langfuse Prompt Management Documentation](https://langfuse.com/docs/prompts/get-started)
- [Langfuse A/B Testing](https://langfuse.com/docs/prompts/ab-testing)
