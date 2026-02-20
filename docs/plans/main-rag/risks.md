# Risks & Mitigations

## Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| PDF download fails at startup (network issue, URL change) | high | Retry with exponential backoff (tenacity). Log warning and continue without RAG if all retries fail. App still works with weather/stock tools. |
| PDFPlumberLoader fails on specific PDF format | med | Fallback to PyPDFLoader if pdfplumber raises. Test with actual PDFs before finalizing. |
| ChromaDB not available at startup | high | Health check dependency already in docker-compose. Retry connection with backoff. Graceful degradation if unavailable. |
| Large PDF causes slow startup | med | Check-and-load strategy means only first startup is slow. Subsequent starts skip indexing. Batch processing for embeddings. |
| Embedding API rate limits during bulk indexing | med | Batch embeddings in groups of ~100 chunks. Add delay between batches if needed. |
| Spanish text chunking loses context at split points | low | 20% overlap (200-300 chars) preserves context across chunk boundaries. RecursiveCharacterTextSplitter handles paragraph/sentence boundaries. |

## Integration Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Agent hallucinates knowledge base content | med | Citation verification guardrail middleware logs warnings. Anti-hallucination instructions in system prompt. |
| Agent uses knowledge tool for non-KB queries | low | Clear tool description and system prompt guidance on when to use search_knowledge vs general knowledge. |
| Metadata filtering returns no results | low | Fallback to unfiltered search if filtered search returns empty. Tool returns "no relevant information found" message. |
| ChromaDB collection corrupted | low | Collection can be rebuilt from scratch by deleting ChromaDB volume and restarting. PDFs are always re-downloadable from R2. |

## Edge Cases Identified

- User asks about content split across two chunks (overlap mitigates this)
- User asks about table data in PDFs (PDFPlumberLoader handles this)
- User asks in English about Spanish documents (embedding model handles cross-language similarity)
- ChromaDB volume exists but is empty (check-and-load detects this)
- One PDF fails to download but others succeed (index available docs, log error for failed one)
- Concurrent startup requests trigger multiple indexing (use collection existence as lock)
