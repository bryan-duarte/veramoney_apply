---
name: codebase_changes
description: |
  Mandatory code quality standards for all codebase modifications. Use this skill BEFORE making ANY code changes. Enforces async-first architecture, strict data contracts, OOP best practices, error management, and clean code principles. Triggers on: code modifications, refactoring, new feature implementation, bug fixes, file creation, or any write operation to the codebase.
---

# Codebase Changes

All code modifications must follow these standards. Read the applicable reference file for detailed patterns.

## Quick Reference

| Topic | Reference File |
|-------|----------------|
| Async patterns | [async-patterns.md](references/async-patterns.md) |
| Error management | [error-management.md](references/error-management.md) |
| OOP best practices | [oop-patterns.md](references/oop-patterns.md) |
| Database patterns | [database-patterns.md](references/database-patterns.md) |
| Code quality | [code-quality.md](references/code-quality.md) |

## Core Principles

### 1. Async-First (MANDATORY)

All code must be asynchronous. This is an I/O-bound application.

- All functions: `async def`
- All I/O: `await`
- Libraries: `httpx` (not `requests`), async DB drivers
- LangChain: `ainvoke()`, `astream()`

### 2. Strict Data Contracts

- Define Pydantic schemas for all external data
- Validate once at entry point
- Trust validated objects internally
- Never use `Any` type

### 3. Self-Documenting Code

- No comments unless absolutely necessary
- Semantic variable/function names
- Named boolean conditions for complex logic
- Constants over magic numbers

### 4. Function Structure

- No nested functions
- Small, single-purpose functions
- Guard clauses over deep nesting
- Extract complex logic to helpers

### 5. OOP Patterns

- Dependency injection with default values
- Helper methods for clarity
- `@staticmethod` for pure functions
- `@classmethod` for factories
- Composition over inheritance
- Single responsibility per class

### 6. Error Management

- Return structured state (`status`, `data`, `errors`)
- Never "log and forget"
- Caller must check status

### 7. KISS & YAGNI

- Simplest solution first
- No speculative abstractions
- Standard library when possible
- No "for future extensibility"

## Pre-Commit Checklist

Before finalizing any code change:

- [ ] All functions are `async def`
- [ ] External data has Pydantic schema
- [ ] No nested function definitions
- [ ] Variables have semantic names (no `data`, `x`, `temp`)
- [ ] Complex conditions use named booleans
- [ ] Magic numbers replaced with constants
- [ ] Dependencies injected, not hardcoded
- [ ] Error paths return structured state
- [ ] Chosen simplest implementation approach

## When to Read Reference Files

- **async-patterns.md**: Converting sync to async, choosing async libraries
- **error-management.md**: Implementing error handling, designing result types
- **oop-patterns.md**: Creating classes, designing object relationships
- **database-patterns.md**: Query optimization, eager loading, bulk operations
- **code-quality.md**: Readability improvements, guard clauses, KISS/YAGNI decisions

## Python Best Practices Summary

```python
# Naming conventions
MAX_RETRIES = 3                    # UPPER_SNAKE for constants
user_email_addresses: list[str]    # snake_case for variables
async def fetch_user_profiles()    # snake_case for functions
class UserRepository:              # PascalCase for classes
 _calculate_internal_fee()         # _prefix for private methods

# Type hints (Python 3.11+)
def process(items: list[str]) -> dict[str, int]:
user: User | None = None
result: AsyncGenerator[Item, None]

# Dependency injection
class Service:
    def __init__(self, client: HttpClient | None = None):
        self._client = client or HttpClient()

# Structured error returns
@dataclass
class Result[T]:
    status: Literal["success", "failed"]
    data: T | None = None
    errors: list[str] = field(default_factory=list)
```
