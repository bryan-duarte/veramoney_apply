# Object-Oriented Programming Best Practices

## Table of Contents

1. [Dependency Injection](#1-dependency-injection)
2. [Helper Methods](#2-helper-methods)
3. [Static Methods](#3-static-methods)
4. [Class Methods](#4-class-methods)
5. [Properties](#5-properties)
6. [Composition Over Inheritance](#6-composition-over-inheritance)
7. [Single Responsibility](#7-single-responsibility)

---

## 1. Dependency Injection

### Pattern: Constructor Injection with Default Values

Use **constructor injection with optional parameters and default values**. This is the recommended approach - no external DI framework needed, fully testable, and self-documenting.

**Why this pattern:**
- No external dependencies required
- Easy to test (inject mocks directly)
- Self-documenting (dependencies visible in `__init__`)
- Works with any framework
- Follows KISS principle

```python
from typing import Optional

# WRONG: Hardcoded dependency (untestable)
class WeatherService:
    def __init__(self):
        self._client = httpx.AsyncClient()
        self._api_key = os.getenv("WEATHER_API_KEY")

# CORRECT: Injectable dependency with defaults
class WeatherService:
    def __init__(
        self,
        http_client: Optional[httpx.AsyncClient] = None,
        api_key: Optional[str] = None,
    ):
        self._client = http_client or httpx.AsyncClient(timeout=30)
        self._api_key = api_key or os.getenv("WEATHER_API_KEY")
```

### Multi-Dependency Classes

Chain dependencies through constructors. Each class declares what it needs.

```python
class WeatherService:
    def __init__(
        self,
        http_client: Optional[httpx.AsyncClient] = None,
        api_key: Optional[str] = None,
    ):
        self._client = http_client or httpx.AsyncClient(timeout=30)
        self._api_key = api_key or os.getenv("WEATHER_API_KEY")

class StockService:
    def __init__(
        self,
        http_client: Optional[httpx.AsyncClient] = None,
        api_key: Optional[str] = None,
    ):
        self._client = http_client or httpx.AsyncClient(timeout=30)
        self._api_key = api_key or os.getenv("STOCK_API_KEY")

class ConversationalAgent:
    def __init__(
        self,
        weather_service: Optional[WeatherService] = None,
        stock_service: Optional[StockService] = None,
        model: Optional[str] = None,
    ):
        self._weather_service = weather_service or WeatherService()
        self._stock_service = stock_service or StockService()
        self._model = model or "gpt-4.1"
```

### Shared Dependencies

When multiple services need the same instance (e.g., shared HTTP client):

```python
shared_client = httpx.AsyncClient(timeout=30)

agent = ConversationalAgent(
    weather_service=WeatherService(http_client=shared_client),
    stock_service=StockService(http_client=shared_client),
)
```

### Testing with Mocks

No patching or DI container manipulation needed.

```python
from unittest.mock import Mock, AsyncMock, MagicMock
import pytest

@pytest.mark.asyncio
async def test_weather_service_with_mock():
    mock_client = MagicMock(spec=httpx.AsyncClient)
    mock_client.get = AsyncMock(return_value=Mock(json=lambda: {"temp": 25}))

    service = WeatherService(
        http_client=mock_client,
        api_key="test-key",
    )

    result = await service.fetch_weather("London")
    assert result["temp"] == 25
    mock_client.get.assert_called_once()

@pytest.mark.asyncio
async def test_agent_with_mock_services():
    mock_weather = Mock(spec=WeatherService)
    mock_weather.get_weather = AsyncMock(return_value={"temp": 25, "city": "London"})

    mock_stock = Mock(spec=StockService)
    mock_stock.get_price = AsyncMock(return_value={"price": 178.52, "ticker": "AAPL"})

    agent = ConversationalAgent(
        weather_service=mock_weather,
        stock_service=mock_stock,
        model="test-model",
    )

    result = await agent.process("What's the weather in London and AAPL price?")

    mock_weather.get_weather.assert_called_once_with("London")
    mock_stock.get_price.assert_called_once_with("AAPL")
```

### Integration Tests (Real Dependencies)

For integration tests, use real services or defaults.

```python
@pytest.mark.asyncio
async def test_agent_integration():
    agent = ConversationalAgent()
    result = await agent.process("Hello")
    assert "response" in result
```

### Private Attributes Convention

Store injected dependencies as private attributes (underscore prefix).

```python
class Service:
    def __init__(
        self,
        repository: Optional[Repository] = None,
        logger: Optional[Logger] = None,
    ):
        self._repository = repository or Repository()
        self._logger = logger or Logger()

    async def process(self, data: dict) -> Result:
        self._logger.info("Processing")  # Use via self._logger
        return await self._repository.save(data)
```

### Anti-Patterns to Avoid

```python
# WRONG: Instantiating inside methods
class Service:
    async def fetch(self, url: str) -> dict:
        client = httpx.AsyncClient()  # Created every call
        return await client.get(url)

# CORRECT: Inject via constructor
class Service:
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self._client = client or httpx.AsyncClient()

    async def fetch(self, url: str) -> dict:
        return await self._client.get(url)

# WRONG: Using global state
class Service:
    async def fetch(self, url: str) -> dict:
        api_key = os.getenv("API_KEY")  # Hidden dependency
        ...

# CORRECT: Explicit dependency
class Service:
    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.getenv("API_KEY")

    async def fetch(self, url: str) -> dict:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        ...
```

### When to Consider a DI Framework

Only consider DI frameworks (dependency-injector, rodi) when:
- Large application with 50+ services
- Complex lifecycle management (singletons vs transients)
- Configuration from multiple sources (YAML, env, database)
- Plugin architecture needed

For most projects, the constructor-with-defaults pattern is sufficient and preferred.

---

## 2. Helper Methods

Break complex logic into small, well-named helper methods.

```python
# WRONG: All logic in one method
class PaymentProcessor:
    async def process_payment(self, payment: Payment) -> PaymentResult:
        if payment.amount <= 0:
            raise ValueError("Invalid amount")
        if payment.currency not in ["USD", "EUR"]:
            raise ValueError("Unsupported currency")
        # ... 30 more lines

# CORRECT: Extracted helpers
class PaymentProcessor:
    async def process_payment(self, payment: Payment) -> PaymentResult:
        self._validate_payment(payment)
        transaction_fee = self._calculate_transaction_fee(payment.amount)
        return await self._execute_transaction(payment, transaction_fee)

    def _validate_payment(self, payment: Payment) -> None:
        is_valid_amount = payment.amount > 0
        is_supported_currency = payment.currency in SUPPORTED_CURRENCIES
        # Guard clauses with named conditions

    def _calculate_transaction_fee(self, amount: Decimal) -> Decimal:
        return amount * TRANSACTION_FEE_PERCENTAGE + TRANSACTION_FEE_FIXED
```

---

## 3. Static Methods

Use `@staticmethod` for pure functions that don't need instance state.

```python
class PriceCalculator:
    def __init__(self, tax_rate: float):
        self.tax_rate = tax_rate

    @staticmethod
    def apply_discount(price: Decimal, discount_percent: float) -> Decimal:
        return price * (1 - discount_percent / 100)

    @staticmethod
    def calculate_tax(price: Decimal, tax_rate: float) -> Decimal:
        return price * Decimal(str(tax_rate))

    # Instance method combines static helpers with instance state
    def calculate_final_price(self, base_price: Decimal, discount_percent: float) -> Decimal:
        discounted = self.apply_discount(base_price, discount_percent)
        return discounted + self.calculate_tax(discounted, self.tax_rate)
```

---

## 4. Class Methods

Use `@classmethod` for factory methods and alternative constructors.

```python
class Configuration:
    def __init__(self, api_key: str, base_url: str, timeout: int):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout

    @classmethod
    def from_environment(cls) -> "Configuration":
        return cls(
            api_key=os.environ["API_KEY"],
            base_url=os.environ.get("API_BASE_URL", "https://api.example.com"),
            timeout=int(os.environ.get("API_TIMEOUT", "30"))
        )

    @classmethod
    def from_file(cls, file_path: str) -> "Configuration":
        with open(file_path) as config_file:
            data = json.load(config_file)
        return cls(**data)
```

---

## 5. Properties

Use `@property` for computed attributes and encapsulation.

```python
class BankAccount:
    def __init__(self, initial_balance: Decimal):
        self._balance = initial_balance
        self._transactions: list[Transaction] = []

    @property
    def balance(self) -> Decimal:
        return self._balance

    @property
    def is_overdrawn(self) -> bool:
        return self._balance < 0

    @property
    def transaction_count(self) -> int:
        return len(self._transactions)
```

---

## 6. Composition Over Inheritance

Prefer composition for code reuse. Use inheritance only for true "is-a" relationships.

```python
# WRONG: Deep inheritance
class BaseService:
    def log(self, message: str) -> None: ...

class DataService(BaseService):
    def fetch(self) -> dict: ...

class CachedDataService(DataService):
    def fetch(self) -> dict: ...

# CORRECT: Composition
class CachedDataFetcher:
    def __init__(
        self,
        fetcher: DataFetcher,
        cache: CacheLayer,
        logger: LoggingService | None = None
    ):
        self._fetcher = fetcher
        self._cache = cache
        self._logger = logger

    async def fetch(self, url: str) -> dict:
        cache_key = self._generate_cache_key(url)
        cached_result = await self._cache.get(cache_key)
        if cached_result:
            return cached_result
        result = await self._fetcher.fetch(url)
        await self._cache.set(cache_key, result)
        return result

    @staticmethod
    def _generate_cache_key(url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()
```

---

## 7. Single Responsibility

Each class should have one reason to change.

```python
# WRONG: God class
class UserManager:
    def create_user(self, data: dict) -> User: ...
    def send_welcome_email(self, user: User) -> None: ...
    def generate_report(self, user: User) -> Report: ...
    def validate_permissions(self, user: User) -> bool: ...

# CORRECT: Separated concerns
class UserRepository:
    async def create(self, data: dict) -> User: ...

class EmailService:
    async def send_welcome_email(self, user: User) -> None: ...

class UserService:
    def __init__(
        self,
        repository: UserRepository,
        email_service: EmailService,
    ):
        self._repository = repository
        self._email_service = email_service

    async def register_user(self, data: dict) -> User:
        user = await self._repository.create(data)
        await self._email_service.send_welcome_email(user)
        return user
```

---

## Checklist

- [ ] Dependencies injected via constructor, not instantiated inside
- [ ] Methods longer than 20 lines extracted to helpers
- [ ] Methods not using `self` converted to `@staticmethod`
- [ ] Alternative constructors use `@classmethod`
- [ ] Computed attributes use `@property`
- [ ] Inheritance depth ≤ 2 levels
- [ ] Each class has one responsibility
