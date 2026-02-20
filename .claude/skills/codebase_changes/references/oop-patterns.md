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

Inject dependencies via constructor with default values for testability.

```python
# WRONG: Hardcoded dependency
class WeatherService:
    def __init__(self):
        self.client = httpx.AsyncClient()

# CORRECT: Injectable dependency
class WeatherService:
    def __init__(self, http_client: httpx.AsyncClient | None = None):
        self._client = http_client or httpx.AsyncClient()
```

**Testing:**
```python
async def test_weather_service():
    mock_client = MagicMock(spec=httpx.AsyncClient)
    service = WeatherService(http_client=mock_client)
    # Test without patching
```

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
