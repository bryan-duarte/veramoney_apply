# Agent Integration Implementation

## Overview

Updates to the existing agent system to incorporate the knowledge retrieval tool: tool registration, system prompt updates, error handling, citation guardrails, and Chainlit UI support.

## Files to Modify

- `src/agent/core/conversational_agent.py` - Register search_knowledge tool
- `src/agent/core/prompts.py` - Add knowledge tool documentation and citation instructions
- `src/agent/middleware/tool_error_handler.py` - Add service name mapping
- `src/chainlit/handlers.py` - Add knowledge tool UI constants

## Files to Create

- `src/agent/middleware/knowledge_guardrails.py` - Citation verification middleware

## Implementation Guidelines

### conversational_agent.py
- Import `search_knowledge` from `src.tools.knowledge`
- Add to tools list alongside get_weather and get_stock_price
- No other changes needed (middleware stack auto-applies to all tools)

### prompts.py
- Add `search_knowledge` to the capabilities disclosure section (alongside weather and stock)
- Tool description: accepts query string and optional document_type filter
- Returns relevant documents from knowledge base with metadata
- Add citation requirements section:
  - When using knowledge base results, include source references at the end of the response
  - Format: numbered footnotes with document title and page number
  - Only cite documents actually returned by the tool
  - Never fabricate citations
- Add guidance on when to use the tool:
  - Questions about VeraMoney company history, mission, team
  - Questions about Uruguayan fintech regulation
  - Questions about Uruguayan banking regulation
  - Questions about financial compliance in Uruguay
  - Do NOT use for: general knowledge, weather, stock prices

### tool_error_handler.py
- Add entry to TOOL_SERVICE_NAMES dict: `"search_knowledge": "knowledge base"`
- No other changes (existing error handler pattern covers new tool)

### knowledge_guardrails.py (new)
- Use `@after_model` decorator (same pattern as output_guardrails.py)
- Extract knowledge tool results from ToolMessage objects in state
- If knowledge tool was called:
  - Parse retrieved chunk content from tool result JSON
  - Check if agent's final response references or reflects the retrieved content
  - Log warning if agent appears to cite documents not in the retrieved results
  - Log warning if agent completely ignores retrieved content
- Non-blocking: always returns None (doesn't modify state)
- Add to middleware stack in conversational_agent.py

### chainlit/handlers.py
- Add `TOOL_KNOWLEDGE = "search_knowledge"` constant
- Add context extraction case for knowledge tool:
  - Extract query and document_type from tool args
  - Format step name: "Searching knowledge base" or "Searching {document_type}"
- Tool results display: show number of chunks found

## Dependencies

- src/tools/knowledge (search_knowledge)
- src/agent/middleware (existing middleware patterns)

## Integration Notes

- The middleware stack order matters: logging -> tool_error_handler -> output_guardrails -> knowledge_guardrails
- knowledge_guardrails runs after the model generates its response (post-processing)
- System prompt changes are critical for agent behavior - test with various query types
- Chainlit changes are cosmetic but improve user experience
