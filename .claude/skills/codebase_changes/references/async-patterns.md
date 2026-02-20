# Async-First Architecture

This application is I/O bound. ALL code MUST be asynchronous.

## Core Rules

1. All functions must be `async def`
2. All I/O operations must use `await`
3. Use async libraries exclusively
4. LangChain: use `ainvoke()`, `astream()` instead of `invoke()`, `stream()`

## Library Mappings

| Sync | Async |
|------|-------|
| `requests` | `httpx.AsyncClient` |
| `sqlite3` | `aiosqlite` |
| `open()` | `aiofiles.open()` |
| `time.sleep()` | `asyncio.sleep()` |

## Examples

```python
# WRONG
def get_weather(city: str) -> dict:
    response = requests.get(f"https://api.weather.com/{city}")
    return response.json()

# CORRECT
async def fetch_weather_data(city_name: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.weather.com/{city_name}")
        return response.json()
```

```python
# WRONG
result = agent.invoke({"messages": [...]})

# CORRECT
result = await agent.ainvoke({"messages": [...]})
```

## Common Mistakes

- Calling `asyncio.run()` inside async functions (use `await` instead)
- Using `requests` instead of `httpx`
- Forgetting `await` on coroutines
- Mixing sync and async code paths
