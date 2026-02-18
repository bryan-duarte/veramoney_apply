# Task 1: Weather Tool

> Status: TODO
> Priority: HIGH (Core Requirement)

## Overview

Create a tool that retrieves current weather information for a given city.

## Requirements

- Accept city name as input
- Return structured JSON output
- Integrate with agent via function calling
- Use public API or mock data

## Tasks

| ID | Task | Status | Notes |
|----|------|--------|-------|
| 2.1.1 | Create tool schema definition | TODO | Input: city name, Output: weather data |
| 2.1.2 | Implement weather fetch logic | TODO | Use httpx for async API calls |
| 2.1.3 | Return structured JSON | TODO | Temperature, conditions, humidity |
| 2.1.4 | Make tool invocable | TODO | Register as LangChain tool |

## Output Schema

```json
{
  "city": "Montevideo",
  "temperature": "22°C",
  "conditions": "Partly cloudy",
  "humidity": "65%"
}
```

## Implementation Location

```
src/tools/
├── __init__.py
└── weather/
    ├── __init__.py
    ├── tool.py          # LangChain tool definition
    ├── schemas.py       # Pydantic schemas
    └── client.py        # Async HTTP client
```

## LangChain Approach

**Reference:** `.claude/skills/langchain/reference/basics/tools.md`

Use the `@tool` decorator:

```python
from langchain.tools import tool
from pydantic import BaseModel

class WeatherInput(BaseModel):
    city: str

@tool
async def get_weather(input_data: WeatherInput) -> dict:
    """Get current weather for a city."""
    # Implementation
    pass
```

## API Options

| Option | Pros | Cons |
|--------|------|------|
| OpenWeatherMap | Free tier, reliable | Requires API key |
| WeatherAPI | Simple, generous free tier | Requires API key |
| Mock Data | No dependencies, instant | Not realistic |

**Recommendation:** Use mock data for development, add real API as enhancement.

## Error Handling

- Invalid city name: Return error message
- API unavailable: Return cached/default data
- Timeout: Use retry with backoff

## Testing

```bash
# Unit test
pytest tests/tools/test_weather.py

# Integration test
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"message": "What is the weather in Montevideo?"}'
```

## Dependencies

```toml
httpx>=0.25.0  # Already installed
```
