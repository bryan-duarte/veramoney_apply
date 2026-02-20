# Langfuse v3 Testing & Evaluation Guide

> *"Testing LLMs is like nailing jelly to a wall - but at least Langfuse gives you a really good hammer."*
> — **El Barto**

## Executive Summary

Langfuse v3 provides a comprehensive testing and evaluation framework for LLM applications through three interconnected systems: **Scores API** for attaching evaluations to traces, **Datasets** for managing test cases, and **Experiments** for running systematic evaluations. The framework supports multiple evaluation paradigms including human feedback, rule-based checks, and LLM-as-a-judge patterns.

---

## 1. Testing Capabilities Overview

| Capability | Description | Languse Component |
|------------|-------------|-------------------|
| **Trace Scoring** | Attach numeric/categorical scores to traces | Scores API |
| **Dataset Management** | Create and version test case collections | Datasets API |
| **Experiment Runs** | Execute tasks against datasets with evaluators | Experiments API |
| **Batch Evaluation** | Evaluate existing traces in bulk | Batch Evaluation |
| **LLM-as-Judge** | Use LLMs to evaluate other LLM outputs | Custom Evaluators |
| **Regression Testing** | Compare experiment runs over time | Dataset Versioning |

---

## 2. Scores API

### 2.1 Score Types

| Type | Value Format | Use Case |
|------|-------------|----------|
| `NUMERIC` | `float` (0-1 recommended) | Quality, accuracy, confidence |
| `BOOLEAN` | `bool` | Pass/fail checks, safety gates |
| `CATEGORICAL` | `str` | Sentiment, classification, response type |

### 2.2 Attaching Scores to Traces

**Method 1: Via Trace Object**

```python
from langfuse import get_client

langfuse = get_client()

trace = langfuse.trace(
    name="chat-request",
    user_id="user-123",
    metadata={"environment": "production"}
)

trace.score(
    name="user-feedback",
    value=0.85,
    comment="User rated response quality as good"
)
```

**Method 2: Via Client with Trace ID**

```python
langfuse.score(
    trace_id="trace-abc123",
    name="accuracy",
    value=0.78,
    data_type="NUMERIC",
    comment="Human evaluator assessment"
)
```

**Method 3: Via `@observe` Decorator Context**

```python
from langfuse.decorators import observe, langfuse_context

@observe(as_type="trace")
async def process_chat_request(message: str) -> str:
    response = await llm_call(message)

    langfuse_context.update_current_trace_score(
        name="quality",
        value=0.9,
        comment="Automated quality check passed"
    )

    return response
```

### 2.3 Score Object Structure

```python
langfuse.score(
    trace_id="trace-abc123",      # Required: trace to score
    name="quality",               # Required: score identifier
    value=0.85,                   # Required: score value
    data_type="NUMERIC",          # Optional: NUMERIC|BOOLEAN|CATEGORICAL
    comment="Optional comment",   # Optional: explanation
    config_id="score-config-123"  # Optional: link to score config
)
```

---

## 3. Dataset Management

### 3.1 Creating Datasets

```python
from langfuse import Langfuse

langfuse = Langfuse()

dataset = langfuse.create_dataset(
    name="veramoney-agent-eval",
    description="Evaluation dataset for VeraMoney assistant",
    metadata={"category": "fintech", "version": "1.0"},
    input_schema={
        "type": "object",
        "properties": {
            "message": {"type": "string"},
            "session_id": {"type": "string"}
        },
        "required": ["message"]
    },
    expected_output_schema={
        "type": "object",
        "properties": {
            "response": {"type": "string"},
            "tool_calls": {"type": "array"}
        },
        "required": ["response"]
    }
)
```

### 3.2 Adding Dataset Items

```python
test_cases = [
    {
        "input": {"message": "What's the weather in Montevideo?"},
        "expected_output": {"response": "weather info here"},
        "metadata": {"category": "weather", "tools_expected": ["get_weather"]}
    },
    {
        "input": {"message": "What's the price of AAPL?"},
        "expected_output": {"response": "stock price here"},
        "metadata": {"category": "stocks", "tools_expected": ["get_stock_price"]}
    }
]

for i, case in enumerate(test_cases):
    langfuse.create_dataset_item(
        dataset_name="veramoney-agent-eval",
        id=f"veramoney-test-{i:03d}",  # Custom ID prevents duplicates
        input=case["input"],
        expected_output=case["expected_output"],
        metadata=case["metadata"]
    )
```

### 3.3 Linking to Source Traces

```python
langfuse.create_dataset_item(
    dataset_name="veramoney-agent-eval",
    input={"question": "What's the weather?"},
    expected_output={"answer": "Weather data"},
    source_trace_id="trace-abc123",      # Link to production trace
    source_observation_id="obs-xyz789"   # Link to specific observation
)
```

### 3.4 Dataset Versioning (Point-in-Time)

```python
from datetime import datetime, timezone

dataset_latest = langfuse.get_dataset("veramoney-agent-eval")

dataset_v1 = langfuse.get_dataset(
    "veramoney-agent-eval",
    version=datetime(2024, 1, 15, tzinfo=timezone.utc)
)
```

---

## 4. Experiment Runs

### 4.1 Basic Experiment Structure

```python
from langfuse.experiment import Evaluation

async def agent_task(*, item, **kwargs):
    message = item.input["message"]
    response = await my_agent.invoke(message)
    return response

def accuracy_evaluator(*, input, output, expected_output=None, **kwargs):
    if not expected_output:
        return Evaluation(name="accuracy", value=0, comment="No expected output")

    is_correct = expected_output["response"].lower() in output.lower()
    return Evaluation(
        name="accuracy",
        value=1.0 if is_correct else 0.0,
        comment="Contains expected answer" if is_correct else "Missing expected answer"
    )

dataset = langfuse.get_dataset("veramoney-agent-eval")

result = dataset.run_experiment(
    name="VeraMoney Agent Evaluation",
    description="Monthly evaluation of production model",
    task=agent_task,
    evaluators=[accuracy_evaluator],
    max_concurrency=5,
    metadata={"model": "gpt-4o-mini"}
)

print(result.format())
print(f"View in Langfuse: {result.dataset_run_url}")
```

### 4.2 Experiment Result Structure

```python
@dataclass
class ExperimentResult:
    name: str
    run_name: str
    description: Optional[str]
    item_results: List[ExperimentItemResult]
    run_evaluations: List[Evaluation]
    dataset_run_id: Optional[str]
    dataset_run_url: Optional[str]

for item_result in result.item_results:
    print(f"Input: {item_result.item}")
    print(f"Output: {item_result.output}")
    print(f"Trace ID: {item_result.trace_id}")
    for eval in item_result.evaluations:
        print(f"  {eval.name}: {eval.value}")
```

### 4.3 Run-Level Evaluators (Aggregate Metrics)

```python
def average_accuracy(*, item_results, **kwargs):
    accuracies = [
        eval_result.value
        for result in item_results
        for eval_result in result.evaluations
        if eval_result.name == "accuracy"
    ]
    avg = sum(accuracies) / len(accuracies) if accuracies else 0
    return Evaluation(
        name="average_accuracy",
        value=avg,
        comment=f"Average accuracy across {len(accuracies)} items"
    )

result = dataset.run_experiment(
    name="Full Evaluation",
    task=agent_task,
    evaluators=[accuracy_evaluator],
    run_evaluators=[average_accuracy]
)
```

---

## 5. LLM-as-Judge Evaluation

### 5.1 Basic LLM Evaluator

```python
from langfuse.experiment import Evaluation
from openai import AsyncOpenAI
import json

openai_client = AsyncOpenAI()

EVALUATION_PROMPT = """You are an impartial evaluator. Rate the following AI response on a scale of 0-1.

Original User Query: {query}
AI Response: {response}

Evaluate on:
1. Relevance to the query
2. Factual accuracy
3. Helpfulness
4. Clarity

Return JSON with: score (0-1), reasoning (string)"""

async def llm_judge_evaluator(*, input, output, expected_output=None, **kwargs) -> Evaluation:
    prompt = EVALUATION_PROMPT.format(query=input, response=output)

    completion = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    result = json.loads(completion.choices[0].message.content)

    return Evaluation(
        name="llm_judge_quality",
        value=result["score"],
        comment=result["reasoning"],
        metadata={"judge_model": "gpt-4o-mini"}
    )
```

### 5.2 Multi-Metric LLM Evaluator

```python
async def comprehensive_llm_evaluator(*, input, output, **kwargs) -> list[Evaluation]:
    prompt = f"""Evaluate this response on multiple dimensions.

Query: {input}
Response: {output}

Return JSON with scores (0-1) for:
- relevance
- accuracy
- helpfulness
- clarity
- safety"""

    completion = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    result = json.loads(completion.choices[0].message.content)

    return [
        Evaluation(name="relevance", value=result["relevance"]),
        Evaluation(name="accuracy", value=result["accuracy"]),
        Evaluation(name="helpfulness", value=result["helpfulness"]),
        Evaluation(name="clarity", value=result["clarity"]),
        Evaluation(name="safety", value=result["safety"])
    ]
```

---

## 6. Rule-Based Evaluation

### 6.1 Deterministic Evaluators

```python
import re

def response_length_evaluator(*, output, **kwargs) -> Evaluation:
    length = len(output)
    reasonable = 10 <= length <= 2000
    return Evaluation(
        name="reasonable_length",
        value=1.0 if reasonable else 0.0,
        comment=f"Response length: {length} chars"
    )

def keyword_coverage_evaluator(*, output, expected_keywords=None, **kwargs) -> Evaluation:
    if not expected_keywords:
        return Evaluation(name="keyword_coverage", value=1.0, comment="No keywords specified")

    found = [kw for kw in expected_keywords if kw.lower() in output.lower()]
    coverage = len(found) / len(expected_keywords)

    return Evaluation(
        name="keyword_coverage",
        value=coverage,
        comment=f"Found: {found}"
    )

def no_hallucination_evaluator(*, output, **kwargs) -> Evaluation:
    markers = [
        "i don't have access to",
        "i cannot browse",
        "i'm not able to access"
    ]
    has_marker = any(marker in output.lower() for marker in markers)

    return Evaluation(
        name="no_hallucination_markers",
        value=1.0 if not has_marker else 0.0,
        comment="Clean response" if not has_marker else "Contains limitation markers"
    )

def tool_call_evaluator(*, output, expected_tools=None, tool_calls=None, **kwargs) -> list[Evaluation]:
    evaluations = []

    if tool_calls:
        called_tools = {tc.get("name") for tc in tool_calls}

        if expected_tools:
            expected_set = set(expected_tools)
            coverage = len(called_tools & expected_set) / len(expected_set)
            evaluations.append(Evaluation(
                name="tool_coverage",
                value=coverage,
                comment=f"Called: {called_tools}, Expected: {expected_set}"
            ))

        tool_errors = sum(1 for tc in tool_calls if tc.get("error"))
        error_rate = tool_errors / len(tool_calls) if tool_calls else 0.0
        evaluations.append(Evaluation(
            name="tool_success_rate",
            value=1.0 - error_rate,
            comment=f"Errors: {tool_errors}/{len(tool_calls)}"
        ))

    return evaluations
```

---

## 7. Batch Evaluation

### 7.1 Evaluating Existing Traces

```python
from langfuse import Langfuse, EvaluatorInputs, Evaluation

langfuse = Langfuse()

def trace_mapper(trace) -> EvaluatorInputs:
    return EvaluatorInputs(
        input=trace.input,
        output=trace.output,
        expected_output=None,
        metadata={"trace_id": trace.id, "user_id": trace.user_id}
    )

def quality_evaluator(*, input, output, metadata=None, **kwargs):
    score = 0.5
    if len(str(output)) > 50:
        score += 0.2
    if input and str(input).lower() in str(output).lower():
        score += 0.3

    return Evaluation(
        name="quality_score",
        value=min(score, 1.0),
        comment=f"Quality assessment for trace {metadata.get('trace_id', 'unknown')}"
    )

result = langfuse.run_batched_evaluation(
    scope="traces",
    mapper=trace_mapper,
    evaluators=[quality_evaluator],
    filter='{"tags": ["production"]}',
    max_items=1000,
    verbose=True
)

print(f"Processed: {result.total_items_processed}")
print(f"Scores created: {result.total_scores_created}")
```

### 7.2 Batch Processing with Concurrency

```python
import asyncio

async def batch_evaluate_traces(
    trace_ids: list[str],
    evaluation_func,
    max_concurrency: int = 10
) -> dict:
    semaphore = asyncio.Semaphore(max_concurrency)

    async def evaluate_with_semaphore(trace_id: str):
        async with semaphore:
            try:
                return await evaluation_func(trace_id)
            except Exception as e:
                return {"trace_id": trace_id, "error": str(e)}

    tasks = [evaluate_with_semaphore(tid) for tid in trace_ids]
    results = await asyncio.gather(*tasks)

    return {
        "total": len(trace_ids),
        "results": results,
        "errors": [r for r in results if "error" in r]
    }
```

---

## 8. pytest Integration

### 8.1 Test Fixtures

```python
import pytest
from langfuse import get_client

@pytest.fixture
def langfuse_client():
    client = get_client()
    yield client
    client.flush()

@pytest.fixture
def sample_trace_id(langfuse_client):
    trace = langfuse_client.trace(
        name="test-trace",
        metadata={"test": True}
    )
    return trace.id

@pytest.fixture
def evaluation_thresholds():
    return {
        "quality": 0.7,
        "relevance": 0.8,
        "accuracy": 0.75
    }
```

### 8.2 Assertion Helpers

```python
def assert_trace_has_score(trace_id: str, score_name: str, min_value: float = 0.5):
    langfuse = get_client()
    trace = langfuse.fetch_trace(trace_id)

    scores = trace.scores if hasattr(trace, 'scores') else []
    matching = [s for s in scores if s.name == score_name]

    assert len(matching) > 0, f"No score '{score_name}' found for trace {trace_id}"

    actual = matching[0].value
    assert actual >= min_value, f"Score '{score_name}' value {actual} < {min_value}"
```

### 8.3 Parametrized Evaluation Tests

```python
TEST_CASES = [
    {
        "name": "weather_query",
        "query": "What's the weather in New York?",
        "expected_tools": ["get_weather"],
        "min_quality": 0.8
    },
    {
        "name": "stock_query",
        "query": "What's the price of AAPL?",
        "expected_tools": ["get_stock_price"],
        "min_quality": 0.8
    },
    {
        "name": "multi_tool_query",
        "query": "Compare weather in Miami and stock price of META",
        "expected_tools": ["get_weather", "get_stock_price"],
        "min_quality": 0.7
    }
]

@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", TEST_CASES, ids=[tc["name"] for tc in TEST_CASES])
async def test_agent_evaluation_cases(test_case):
    langfuse = get_client()
    trace = langfuse.trace(name=f"eval-{test_case['name']}")

    response = await agent_call(test_case["query"], trace_id=trace.id)

    quality = await llm_judge_evaluator(
        input=test_case["query"],
        output=response
    )

    langfuse.score(
        trace_id=trace.id,
        name=quality.name,
        value=quality.value,
        comment=quality.comment
    )

    assert quality.value >= test_case["min_quality"]
    langfuse.flush()
```

### 8.4 Test Suite Configuration

```python
import pytest
import os

@pytest.fixture(scope="session", autouse=True)
def setup_langfuse():
    os.environ.setdefault("LANGFUSE_PUBLIC_KEY", "pk-test-...")
    os.environ.setdefault("LANGFUSE_SECRET_KEY", "sk-test-...")
    os.environ.setdefault("LANGFUSE_HOST", "http://localhost:3000")

    langfuse = get_client()
    yield langfuse
    langfuse.flush()
```

---

## 9. User Feedback Integration

### 9.1 FastAPI Feedback Endpoint

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

router = APIRouter(prefix="/feedback", tags=["feedback"])

class FeedbackRequest(BaseModel):
    trace_id: str = Field(..., description="Langfuse trace ID from chat response")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 (poor) to 5 (excellent)")
    comment: str | None = Field(None, max_length=1000)

class FeedbackResponse(BaseModel):
    status: str
    trace_id: str

@router.post("", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest) -> FeedbackResponse:
    langfuse = get_client()

    normalized = request.rating / 5.0
    langfuse.score(
        trace_id=request.trace_id,
        name="user-satisfaction",
        value=normalized,
        comment=request.comment,
        data_type="NUMERIC"
    )

    return FeedbackResponse(status="recorded", trace_id=request.trace_id)
```

### 9.2 Chat Response with Trace ID

```python
class ChatResponse(BaseModel):
    response: str
    session_id: str
    trace_id: str  # Include trace_id for feedback

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    trace_id = str(uuid.uuid4())

    langfuse_handler = CallbackHandler(trace_id=trace_id)
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": request.message}]},
        config={"callbacks": [langfuse_handler]}
    )

    return ChatResponse(
        response=result["messages"][-1].content,
        session_id=request.session_id,
        trace_id=trace_id
    )
```

---

## 10. Regression Testing Pattern

### 10.1 Baseline Comparison

```python
from datetime import datetime, timezone

async def run_regression_test():
    langfuse = get_client()

    dataset_v1 = langfuse.get_dataset(
        "veramoney-agent-eval",
        version=datetime(2024, 1, 1, tzinfo=timezone.utc)
    )
    dataset_v2 = langfuse.get_dataset(
        "veramoney-agent-eval",
        version=datetime(2024, 6, 1, tzinfo=timezone.utc)
    )

    result_v1 = dataset_v1.run_experiment(
        name="Baseline v1",
        task=agent_task,
        evaluators=[accuracy_evaluator]
    )

    result_v2 = dataset_v2.run_experiment(
        name="Current v2",
        task=agent_task,
        evaluators=[accuracy_evaluator]
    )

    print(f"V1 Average: {result_v1.format()}")
    print(f"V2 Average: {result_v2.format()}")

    return result_v1, result_v2
```

### 10.2 CI/CD Integration

```python
import sys

async def ci_evaluation():
    result = await run_evaluation()

    avg_quality = sum(
        e.value for r in result.item_results for e in r.evaluations if e.name == "quality"
    ) / len(result.item_results)

    threshold = 0.75
    if avg_quality < threshold:
        print(f"FAIL: Average quality {avg_quality:.2f} < {threshold}")
        sys.exit(1)
    else:
        print(f"PASS: Average quality {avg_quality:.2f} >= {threshold}")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(ci_evaluation())
```

---

## 11. Recommended Module Structure

```
src/observability/
├── __init__.py
├── langfuse_client.py
├── callbacks.py
└── evaluation/
    ├── __init__.py
    ├── scores.py           # Score attachment functions
    ├── evaluators.py       # Reusable evaluator classes
    ├── datasets.py         # Dataset management
    └── pytest_fixtures.py  # Test utilities

tests/
├── evaluation/
│   ├── __init__.py
│   ├── conftest.py         # Langfuse test fixtures
│   ├── test_weather_eval.py
│   └── test_stock_eval.py
└── regression/
    ├── baseline.json       # Baseline results
    └── test_regression.py
```

---

## 12. Key Findings

| Finding | Implication |
|---------|-------------|
| **Automatic trace linking** | Experiments create traces automatically - no manual linking needed |
| **Run-level evaluators** | Aggregate metrics computed across all items in one run |
| **Point-in-time versioning** | Datasets can be retrieved at specific timestamps for reproducibility |
| **LLM-as-judge cost** | Model-based evaluation adds API costs and latency |
| **pytest async support** | Full async compatibility with `@pytest.mark.asyncio` |
| **Score configs** | Define thresholds and allowed values in Langfuse UI |

---

## 13. Implementation Checklist

### Phase 1: Basic Scoring

- [ ] Create `src/observability/evaluation/scores.py`
- [ ] Add feedback endpoint `/feedback`
- [ ] Include `trace_id` in chat responses
- [ ] Test user feedback collection

### Phase 2: Dataset Setup

- [ ] Create evaluation dataset in Langfuse
- [ ] Add test cases for weather and stock queries
- [ ] Link production traces as dataset items

### Phase 3: Evaluators

- [ ] Implement rule-based evaluators (length, keywords)
- [ ] Implement LLM-as-judge evaluator
- [ ] Create composite quality score

### Phase 4: Test Integration

- [ ] Add pytest fixtures for Langfuse
- [ ] Create parametrized evaluation tests
- [ ] Set up CI/CD regression pipeline

### Phase 5: Monitoring

- [ ] Configure score dashboard in Langfuse UI
- [ ] Set up alerts for quality degradation
- [ ] Document evaluation criteria

---

## 14. Technical Analysis

### Pros

| Benefit | Description |
|---------|-------------|
| **Unified Platform** | Observability + evaluation in one tool |
| **Automatic Tracing** | Experiments create traces automatically |
| **Flexible Evaluators** | Rule-based, LLM, and human evaluation |
| **Version Control** | Point-in-time dataset retrieval |
| **pytest Compatible** | Full async test support |
| **Real-time Dashboard** | Visual score tracking |

### Cons

| Limitation | Mitigation |
|------------|------------|
| **LLM evaluation cost** | Use smaller models (gpt-4o-mini) for judging |
| **Non-deterministic LLM scores** | Average multiple runs, use temperature=0 |
| **No built-in evaluators** | Create reusable evaluator library |
| **API latency** | Batch operations, async execution |

---

## 15. Sources

| Source | URL/Path | Credibility |
|--------|----------|-------------|
| Langfuse Python SDK v3.14.3 | Installed package | Primary - Official SDK |
| Langfuse Scores API | https://langfuse.com/docs/scores | Official Documentation |
| Langfuse Datasets | https://langfuse.com/docs/datasets | Official Documentation |
| Langfuse Evaluation | https://langfuse.com/docs/evaluation | Official Documentation |
| Project pyproject.toml | `pyproject.toml` | Project Configuration |
| Previous Report | `docs/reports/langfuse-observability-implementation-guide.md` | Project Documentation |

---

## 16. Final Verdict

**Recommendation:** Implement a three-tier evaluation strategy:
1. **Rule-based evaluators** for fast, deterministic checks (length, keywords, safety)
2. **LLM-as-judge** for nuanced quality assessment
3. **User feedback** for real-world quality signals

**Risk Level:** Low

**Confidence Level:** High - Based on direct SDK inspection and comprehensive documentation

---

*Report generated by: El Barto*
*Date: 2026-02-19*
