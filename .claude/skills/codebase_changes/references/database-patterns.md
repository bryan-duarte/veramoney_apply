# Database Interactions

Optimize database interactions to minimize latency and resource consumption.

## Core Principles

1. **Bulk Operations** - Use bulk methods for multiple records
2. **Selectivity** - Retrieve only necessary columns
3. **Eager Loading** - Prevent N+1 queries
4. **Database Computation** - Use DB functions instead of app-level processing

## Examples

### Bulk Operations

```python
# WRONG: Individual inserts
for record in records:
    await session.execute(insert(User).values(record))

# CORRECT: Bulk insert
await session.execute(insert(User).values(records))
```

### Selectivity

```python
# WRONG: SELECT *
users = await session.execute(select(User))

# CORRECT: Select only needed columns
users = await session.execute(
    select(User.id, User.email, User.name)
)
```

### Eager Loading

```python
# WRONG: N+1 queries
orders = await session.execute(select(Order))
for order in orders:
    customer = await session.execute(  # N queries!
        select(Customer).where(Customer.id == order.customer_id)
    )

# CORRECT: Joined eager load
orders = await session.execute(
    select(Order).options(joinedload(Order.customer))
)
```

### Database Computation

```python
# WRONG: App-level aggregation
orders = await session.execute(select(Order))
total = sum(order.amount for order in orders)

# CORRECT: Database aggregation
result = await session.execute(
    select(func.sum(Order.amount))
)
total = result.scalar()
```

## Checklist

- [ ] Replace loops containing queries with single efficient queries
- [ ] Audit queries to ensure only necessary columns retrieved
- [ ] Add `joinedload`/`selectinload` for relationships accessed in loops
- [ ] Move aggregations to database layer
