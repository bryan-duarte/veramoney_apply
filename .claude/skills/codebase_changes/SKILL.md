---
name: codebase_changes
description: Use this skill in all the codebase changes, no exceptions.
model: opus
---

# Codebase Changes

## Instructions

1.  **Async-First Architecture (MANDATORY):** This application is I/O bound. ALL code MUST be asynchronous using Python's `asyncio`. No synchronous code is allowed.
    - All functions must be `async def`
    - All I/O operations must use `await`
    - Use async libraries: `httpx` (not `requests`), async DB drivers
    - LangChain: use `ainvoke()`, `astream()` instead of `invoke()`, `stream()`

2.  **Define Strict Data Contracts:** For any data entering the system (from an API, database, or message queue), define a strict schema (e.g., Pydantic model, Data Transfer Object). Specify exact data types (`int`, `bool`, `str`) for all fields. Do not use generic types like `Any`.

3.  **Validate Once, at the Entry Point:** Instantiate your schema object immediately when external data is received. This is the **only** place where validation should occur.

4.  **Handle Validation Errors at the Boundary:** Wrap schema instantiation in a `try...except` block to catch validation failures. If validation fails, reject the data immediately. Do not allow invalid data to penetrate the application's core logic.

5.  **Trust Internal Objects:** Once an object is successfully created from a schema, trust it. Do not perform `null` or type checks on its properties later in the code. The object's existence guarantees its validity according to the defined contract.

6.  **Use Named Boolean Validation:** Avoid using `if` statements with complex, hard-to-understand conditions. Use a named boolean variable to validate the condition.

7.  **Avoid Magic Numbers:** Do not use magic numbers in the code; use constants instead.

8.  **Self-Documenting Code:** Avoid adding unnecessary comments. The code should be self-explanatory. Only add comments if absolutely necessary for complex logic.

9.  **Tests on Request:** Do not write tests unless explicitly asked by the user.

**To-Do Checklist:**
- [ ] Review your code. Are you validating the same variable in multiple places? Consolidate this logic into a single schema validation at the start.
- [ ] Replace manual type conversions (e.g., `int(variable)`) inside `try...except` blocks with data schema type declarations.
- [ ] Remove any `if data["key"] is not None:` checks if that key is a required field in your schema.

---

### 2. Error Management: Errors Are State, Not Just Logs

**Objective:** Build predictable systems that are transparent about failures, making them easier to debug and monitor.

**Instructions:**

1.  **Model Errors Explicitly:** Do not just log an error and continue. An error is critical information. The function's return value must reflect it.

2.  **Return Structured State:** Functions that can fail should return an object including a status field (e.g., `status: "SUCCESS" | "FAILED"`) and a field for error details (e.g., `errors: list`).

3.  **Error-Based Control Flow:** The calling code must check the returned `status`. If `FAILED`, it must react accordingly (e.g., return an HTTP 500 error, enqueue a retry, or abort the process).

4.  **Eliminate "Log and Forget":** An `except` block containing only `logging.error(...)` that allows the program to continue is a bug. The `except` block must update the state to be returned.

**To-Do Checklist:**
- [ ] Identify `except` blocks that only log an error. Modify them to update a state variable that will be returned.
- [ ] Refactor functions that return data on success and `None` on failure. Ensure they return a state object like `{ "status": ..., "data": ..., "errors": ... }`.

---

### 3. Function Scope: Do Not Nest Functions

**Objective:** Ensure functions are testable, reusable, and predictable by avoiding hidden state capture and complex scopes.

**Instructions:**

1.  Define functions only at module scope or as class/static methods. Do not declare functions inside other functions or methods.
2.  Extract inner logic to a top-level helper (using a descriptive name, prefixing with `_` if internal) or a `@staticmethod`/`@classmethod`.
3.  Pass all dependencies via explicit parameters. Never rely on closures capturing outer variables.
4.  Keep validators and hooks free of nested definitions; place shared utilities at module scope.

**To-Do Checklist:**
- [ ] Refactor any nested `def` into top-level helpers or static/class methods.
- [ ] Replace closures with explicit parameters to remove hidden state.
- [ ] Adjust unit tests for extracted helpers to preserve behavior.

---

### 4. Code Structure: Optimize for Readability

**Objective:** Write code that is easy for other developers to read, understand, and modify safely.

**Instructions:**

1.  **Write Small, Single-Purpose Functions:** A function should do one thing. Its name should accurately describe what it does. If you cannot find a simple, descriptive name, the function is likely doing too much.

2.  **Use Guard Clauses to Reduce Nesting:** Instead of nesting `if` statements, check for invalid conditions at the beginning of your function and exit early (`return`, `continue`, or `raise`).

    -   **Avoid:** `if condition: ... (deeply nested code) ...`
    -   **Prefer:** `if not condition: return`

3.  **Name Variables to Reveal Intent:** A variable's name should clearly state its purpose. Avoid single-letter or overly generic names. Good naming makes code self-documenting. **You cannot use letters or non-semantical names in your code changes.**

4.  **Extract Complex Logic into Functions:** If a loop or conditional block becomes complex, move that logic into a new function. Give the new function a name that explains *what* it does. This hides the complexity (the *how*) and makes the original code easier to read.

**To-Do Checklist:**
- [ ] Identify functions longer than 20-25 lines. Can they be broken down into smaller, helper functions?
- [ ] Find nested `if/else` statements. Can they be flattened by using guard clauses?
- [ ] Look for variables named `data`, `item`, `x`, or `temp`. Rename them to be more descriptive.
- [ ] **Do not add comments to the code. Use the code to auto-explain the code itself. Just add comments to the code if it is ultra really necessary.**

---

### 5. Reliability & Resilience: Fail Fast, Recover Gracefully

**Objective:** Maintain system usability during partial failure.

**Instructions:**

1.  Use retries with exponential backoff for transient errors only.
2.  Ensure write operations are idempotent (using keys, deduplication tables, or version checks).
3.  Apply circuit breakers and bulkheads around fragile dependencies.
4.  Enforce end-to-end request deadlines.

**To-Do Checklist:**
- [ ] Add idempotency keys to state-affecting POST/PUT requests.
- [ ] Wrap flaky external calls with circuit breakers.
- [ ] Propagate deadlines via headers/context.

---

### 6. Optimize Database Interactions

**Objective:** Interact with the database efficiently to minimize latency and resource consumption.

**Instructions:**

1.  **Bulk Operations:** Use bulk methods (e.g., `bulk_insert_mappings`) for multiple records to reduce roundtrips.
2.  **Selectivity:** Retrieve only necessary data using `load_only` or by selecting specific columns, never use `*` or fetch all if not necessary.
3.  **Master Eager Loading:** Use `joinedload` or `selectinload` to prevent "N+1 query problems."
4.  **Database Computation:** Use built-in database functions (aggregations, `ts_rank`) instead of processing raw data in application code.

**To-Do Checklist:**
- [ ] Replace loops containing database queries with single, efficient queries.
- [ ] Audit queries to ensure only necessary columns are retrieved.
- [ ] Move manual data processing logic to the database layer where possible.

---

### 7. Complex Condition Handling

**Objective:** Improve readability of complex logical checks.

**Instruction:** Use named boolean variables for complex conditions in `if` statements.

**Python Example:**
```python
# Avoid
if not user.is_active and not user.is_admin:
    return False

# Prefer
have_enough_balance = (
  user.balance < 100
  and user.is_active
  and user.is_admin
)
if have_enough_balance:
    return False
```

---

### 8. Constants over Magic Numbers

**Instruction:** Replace magic numbers with named constants.

**Python Example:**
```python
# Avoid
if user.age < 18:
    return False

# Prefer
MIN_AGE = 18
is_user_under_age = user.age < MIN_AGE
if is_user_under_age:
    return False
```

---

### 9. Type Safety Strategy: TypeScript vs. Zod

-   **Roles:** TypeScript types only run at build time, so trust them for internal data you already control. Zod schemas execute at runtime, so put them on every system boundary to stop malformed input from APIs, DBs, files, env vars, or users.

-   **When to use TypeScript:** describe props/contracts between your own modules, shape domain entities that have already been validated, and derive those types directly from Zod via `z.infer<typeof schema>` to keep compile-time safety in sync with runtime rules.

-   **When to use Zod:** validate untrusted inputs (HTTP requests, webhooks, database rows, environment variables) and perform transformations/sanitization before the data enters the application layer. Keep these schemas in the infrastructure layer so upper layers consume only trusted entities.

-   **Clean architecture flow:** External source â†' _Zod parses & transforms (runtime guard)_ â†' `z.infer` creates the TypeScript type â†' Application/Domain/UI layers operate purely on the trusted type.

**To-Do Checklist:**
- [ ] Add Zod schemas to all entry points where data crosses trust boundaries.
- [ ] Derive TypeScript types from Zod schemas.
- [ ] Remove manual runtime checks once Zod validation is in place.

---

### 10. KISS & YAGNI: Avoid Unnecessary Complexity (MANDATORY)

**Objective:** Write the simplest code that solves the problem. Complexity is a liability, not an asset.

**Core Principles:**

1.  **KISS (Keep It Simple, Stupid):** Always choose the simplest solution that meets requirements. Simple code is easier to understand, maintain, debug, and extend.

2.  **YAGNI (You Aren't Gonna Need It):** Do not implement features, abstractions, or flexibility that are not currently required. Build for today's requirements, not hypothetical future ones.

3.  **Explicit User Requirement Override:** The only time to introduce complexity is when the user explicitly requests it or the problem domain fundamentally requires it. When in doubt, ask.

4.  **Occam's Razor for Code:** When multiple valid solutions exist, prefer the one with the fewest assumptions, moving parts, and lines of code.

**Decision Framework:**

When faced with implementation choices, apply this hierarchy:
-   **First:** Can this be done with standard library or existing code? → **Do that.**
-   **Second:** Does a simple, direct solution exist? → **Use it.**
-   **Third:** Is abstraction genuinely necessary? → **Only if complexity is explicitly required.**
-   **Never:** Build flexibility "just in case" or add layers "for future extensibility."

**Red Flags (Avoid These):**
-   Premature abstraction (creating base classes/interfaces for single implementations)
-   Over-engineering (design patterns where a simple function would suffice)
-   Speculative features ("we might need this later")
-   Configuration for configuration's sake
-   Layers of indirection without clear benefit

**Python Example:**
```python
# AVOID: Over-engineered, speculative abstraction
class DataProcessor(ABC):
    @abstractmethod
    def process(self, data: dict) -> dict:
        pass

class UserDataProcessor(DataProcessor):
    def process(self, data: dict) -> dict:
        return {"name": data.get("name", "").upper()}

# PREFER: Simple, direct solution
def process_user_name(user_data: dict) -> dict:
    return {"name": user_data.get("name", "").upper()}
```

**To-Do Checklist:**
- [ ] Before adding an abstraction, ask: "Is there a simpler way?"
- [ ] Before adding a feature, ask: "Was this explicitly requested?"
- [ ] Before adding a configuration option, ask: "Can this just be a constant?"
- [ ] Review any code with more than 2 layers of abstraction—can any be removed?

---

### Error Handling Pattern

The project uses a custom error hierarchy:
- **Location:** `src/features/shared/domain/errors/AppError.ts`
- Typed error codes for debugging.
- Factory methods for error creation.
- Consistent error structure across the application.