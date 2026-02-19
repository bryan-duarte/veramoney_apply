# A/B Testing with Langfuse Prompts

A/B testing allows you to compare different prompt versions in production to measure their impact on quality, cost, and latency.

## Overview

Langfuse supports A/B testing through:
1. **Labels** - Assign different labels (e.g., `prod-a`, `prod-b`) to different versions
2. **Dynamic routing** - Route users to different prompt versions based on logic
3. **Metrics tracking** - Compare performance via Langfuse Tracing

## Implementation Patterns

### Pattern 1: Label-Based Routing

```python
import random
from langfuse import get_client

langfuse = get_client()

def get_prompt_for_user(user_id: str) -> str:
    # Consistent routing based on user ID
    variant = "prod-a" if hash(user_id) % 2 == 0 else "prod-b"

    prompt = langfuse.get_prompt("movie-critic", label=variant)
    return prompt

# Create variants
langfuse.create_prompt(
    name="movie-critic",
    type="text",
    prompt="As a harsh critic, rate {{movie}} from 1-10.",
    labels=["prod-a"],
)

langfuse.create_prompt(
    name="movie-critic",
    type="text",
    prompt="As a lenient critic, rate {{movie}} from 1-10.",
    labels=["prod-b"],
)
```

### Pattern 2: Percentage-Based Rollout

```python
def get_prompt_with_rollout(rollout_percentage: int = 50) -> str:
    if random.randint(1, 100) <= rollout_percentage:
        return langfuse.get_prompt("movie-critic", label="prod-new")
    return langfuse.get_prompt("movie-critic", label="production")
```

### Pattern 3: Feature Flag Integration

```python
def get_prompt_with_feature_flag(user_id: str, feature_flags: dict) -> str:
    if feature_flags.get("new_prompt_enabled", False):
        if user_id in feature_flags.get("new_prompt_allowlist", []):
            return langfuse.get_prompt("movie-critic", label="staging")

    return langfuse.get_prompt("movie-critic", label="production")
```

## Metrics Comparison

Link prompts to traces to compare metrics:

```python
from langfuse import observe, get_client

langfuse = get_client()

@observe()
def generate_movie_review(movie: str, variant: str):
    prompt = langfuse.get_prompt("movie-critic", label=variant)

    langfuse.update_current_observation(
        metadata={"prompt_variant": variant, "prompt_version": prompt.version}
    )

    # Your LLM call here
    return llm_response
```

In Langfuse UI, you can then:
1. Filter traces by `prompt_variant` metadata
2. Compare scores, latency, and token usage across variants
3. View aggregate metrics per prompt version

## Best Practices

1. **Consistent routing** - Use user ID hashing for consistent experiences
2. **Sample size** - Run tests long enough for statistical significance
3. **Single variable** - Change only one aspect per variant
4. **Rollback ready** - Keep previous version labeled for quick rollback
5. **Monitor metrics** - Track quality scores, not just usage

## Gradual Rollout Workflow

```python
# Week 1: 10% traffic to new version
langfuse.update_prompt(name="movie-critic", version=2, new_labels=["prod-10pct"])

# Week 2: 50% traffic
langfuse.update_prompt(name="movie-critic", version=2, new_labels=["prod-50pct"])

# Week 3: 100% traffic (promote to production)
langfuse.update_prompt(name="movie-critic", version=2, new_labels=["production"])
```
