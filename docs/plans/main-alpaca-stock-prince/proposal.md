# Stock Tool Implementation with Alpaca API

> *"Free market data is like free advice—worth exactly what you pay for it, which is 15 minutes of delay."*
> — El Barto

## Overview

**Request**: Implement Task 2 - Stock Price Tool using Alpaca Market Data API

**Created**: 2026-02-18

## What

Implement a LangChain-compatible stock price tool that retrieves current market data for a given ticker symbol using the Alpaca Market Data API.

The tool will:
- Accept a stock ticker symbol (e.g., `AAPL`)
- Return structured JSON with price, timestamp, change, and change percentage
- Validate ticker format (1-5 uppercase letters)
- Be callable by LangChain agents via the `@tool` decorator

## Why

This is a core requirement of the VeraMoney technical assessment. The stock tool, combined with the weather tool, demonstrates the ability to build LLM-powered agents with real-world tool integration in a fintech context.

Using Alpaca API (vs yfinance) demonstrates:
- Integration with professional financial APIs
- Proper authentication handling
- Understanding of market data limitations (15-minute delay on free tier)

## Impact

### Files Created
- `src/tools/stock/schemas.py` - Pydantic models for input/output
- `src/tools/stock/client.py` - Async Alpaca API client
- `src/tools/stock/tool.py` - LangChain tool definition
- `src/tools/stock/__init__.py` - Module exports

### Files Modified
- `src/config/settings.py` - Add Alpaca API credentials
- `.env.example` - Add Alpaca environment variables

### No Impact On
- Agent layer (future task)
- Chat endpoint (placeholder remains)
- Weather tool (unchanged)
