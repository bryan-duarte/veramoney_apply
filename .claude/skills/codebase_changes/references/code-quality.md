# Code Quality Standards

## Table of Contents

1. [Data Contracts](#1-data-contracts)
2. [Function Scope](#2-function-scope)
3. [Readability](#3-readability)
4. [KISS & YAGNI](#4-kiss--yagni)
5. [Reliability Patterns](#5-reliability-patterns)

---

## 1. Data Contracts

### Validate Once at Entry Point

```python
from pydantic import BaseModel

class UserRequest(BaseModel):
    email: str
    age: int

# Entry point - validate here only
async def create_user(raw_data: dict) -> User:
    validated = UserRequest(**raw_data)  # Validates once
    return await repository.create(validated)
```

### Trust Internal Objects

```python
# WRONG: Re-validating trusted objects
async def send_email(user: User) -> None:
    if user.email is None:  # Unnecessary - already validated
        raise ValueError("No email")

# CORRECT: Trust validated objects
async def send_email(user: User) -> None:
    await mailer.send(to=user.email, subject="Welcome")
```

### Strict Types

```python
# WRONG: Generic Any type
def process(data: Any) -> dict:
    return {"name": data.get("name")}

# CORRECT: Specific types
class InputData(BaseModel):
    name: str
    value: int

def process(data: InputData) -> dict:
    return {"name": data.name}
```

---

## 2. Function Scope

**Never nest functions.** Define at module scope or as class methods.

```python
# WRONG: Nested function
async def process_order(order: Order) -> Result:
    def calculate_total(items: list) -> Decimal:  # Nested!
        return sum(item.price for item in items)

    total = calculate_total(order.items)
    return Result(total=total)

# CORRECT: Module-level helper
def calculate_order_total(items: list[Item]) -> Decimal:
    return sum(item.price for item in items)

async def process_order(order: Order) -> Result:
    total = calculate_order_total(order.items)
    return Result(total=total)
```

---

## 3. Readability

### Guard Clauses

```python
# WRONG: Deeply nested
async def process(user: User) -> Result:
    if user.is_active:
        if user.has_permission:
            if user.quota > 0:
                return await do_work(user)
    return Result(error="Cannot process")

# CORRECT: Guard clauses
async def process(user: User) -> Result:
    if not user.is_active:
        return Result(error="User inactive")
    if not user.has_permission:
        return Result(error="No permission")
    if user.quota <= 0:
        return Result(error="Quota exceeded")
    return await do_work(user)
```

### Named Conditions

```python
# WRONG: Complex inline condition
if user.age >= 18 and user.is_verified and not user.is_blocked:
    return True

# CORRECT: Named boolean
is_eligible_user = (
    user.age >= MIN_AGE
    and user.is_verified
    and not user.is_blocked
)
if is_eligible_user:
    return True
```

### Semantic Naming

```python
# WRONG: Generic names
data = fetch()
result = process(data)
x = transform(result)

# CORRECT: Semantic names
user_profiles = fetch_user_profiles()
enriched_profiles = add_subscription_data(user_profiles)
active_subscribers = filter_active_subscribers(enriched_profiles)
```

### Constants Over Magic Numbers

```python
# WRONG
if user.age < 18:
    return False

# CORRECT
MIN_AGE = 18
is_under_age = user.age < MIN_AGE
if is_under_age:
    return False
```

---

## 4. KISS & YAGNI

### Decision Framework

When facing implementation choices:

1. **First:** Can standard library do this? → Use it
2. **Second:** Does a simple solution exist? → Use it
3. **Third:** Is abstraction genuinely necessary? → Only if explicitly required
4. **Never:** Build "just in case" or "for future extensibility"

### Red Flags

- Premature abstraction (base classes for single implementations)
- Over-engineering (design patterns where functions suffice)
- Speculative features ("we might need this")
- Configuration for configuration's sake

### Example

```python
# WRONG: Over-engineered
class DataProcessor(ABC):
    @abstractmethod
    def process(self, data: dict) -> dict: pass

class UserDataProcessor(DataProcessor):
    def process(self, data: dict) -> dict:
        return {"name": data.get("name", "").upper()}

# CORRECT: Simple function
def process_user_name(user_data: dict) -> dict:
    return {"name": user_data.get("name", "").upper()}
```

---

## 5. Reliability Patterns

### Retries with Backoff

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
async def fetch_with_retry(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
```

### Idempotency

```python
async def create_order(
    order_data: OrderData,
    idempotency_key: str
) -> Order:
    existing = await repository.find_by_idempotency_key(idempotency_key)
    if existing:
        return existing
    return await repository.create(order_data, idempotency_key)
```

### Circuit Breaker

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=30)
async def call_external_service(payload: dict) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(EXTERNAL_URL, json=payload)
        return response.json()
```

---

## Checklist

- [ ] Data validated once at entry point
- [ ] No nested function definitions
- [ ] Guard clauses instead of deep nesting
- [ ] Named boolean variables for complex conditions
- [ ] Semantic variable/function names
- [ ] Constants instead of magic numbers
- [ ] Simplest solution chosen
- [ ] No speculative abstractions
