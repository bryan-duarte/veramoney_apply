# User Preferences & Decisions

## Configuration Preferences

- **Context Level**: Moderado (6 exploration tasks)
- **Participation Level**: Equilibrado (8-15 questions)
- **Detail Level**: Pseudocode (guidelines only, no specific code)
- **Extras**: Neither tests nor documentation

## Q&A and Rationale

### Embedding Model
**Q:** Which OpenAI embedding model to use?
**A:** text-embedding-3-small
**Decision:** Use text-embedding-3-small (1536 dims, $0.02/1M tokens). Already configured in settings. Cost-effective and sufficient for 3 documents in Spanish.
**Rejected:** text-embedding-3-large (6x more expensive, overkill for 3 docs), text-embedding-ada-002 (legacy, user requested modern models)

### Collection Strategy
**Q:** How to organize ChromaDB collections?
**A:** Single collection with metadata
**Decision:** One `veramoney_knowledge` collection. Each chunk tagged with `document_type` metadata (vera_history, fintec_regulation, bank_regulation). Enables metadata filtering without multi-collection complexity.
**Rejected:** Three separate collections (unnecessary complexity for 3 docs), Two collections (arbitrary grouping)

### Startup Loading Strategy
**Q:** How to load PDFs into ChromaDB on startup?
**A:** Check-and-load
**Decision:** On startup, check if collection exists and has documents. If empty/missing, download PDFs and index. Skip if already populated. Fast subsequent starts with ChromaDB persistent volume.
**Rejected:** Always reload (slow starts), Lazy load (bad first-query UX)

### Chunking Strategy
**Q:** What chunk sizes per document type?
**A:** Type-specific sizes
**Decision:** vera_history: 1000 chars / 200 overlap. Regulations (fintec + bank): 1500 chars / 300 overlap. Larger chunks for regulations preserve legal context and table structures.
**Rejected:** Uniform 1000/200 (suboptimal for regulations), Uniform 1200/250 (compromise but still not ideal)

### Retrieval Parameters
**Q:** How many documents to retrieve per query?
**A:** k=4
**Decision:** Return top 4 most similar chunks per query. Good balance for a 3-document knowledge base without overwhelming the LLM context.
**Rejected:** k=3 (may miss relevant chunks), k=6 (too many tokens for 3-doc KB)

### Code Structure
**Q:** Where to place RAG code?
**A:** src/rag/ pipeline + src/tools/knowledge/ tool
**Decision:** RAG pipeline logic (loader, splitter, vectorstore, retriever) in `src/rag/`. Tool wrapper in `src/tools/knowledge/` following the existing three-layer tool pattern (client, schemas, tool).
**Rejected:** Everything in src/rag/ (breaks tool pattern), src/tools/rag/ only (mixes pipeline with interface)

### Citation Format
**Q:** How should citations appear in responses?
**A:** Footnotes at end
**Decision:** Sources listed at the bottom of the response as numbered references. Clean, non-intrusive formatting.
**Rejected:** Inline [Source: name] (clutters response), Both inline + footer (too verbose)

### Document Type Filtering
**Q:** Should the tool support filtering by document type?
**A:** Yes, optional filter
**Decision:** Tool accepts optional `document_type` parameter. Agent can filter by vera_history, fintec_regulation, or bank_regulation when relevant. Falls back to searching all documents when not specified.
**Rejected:** No filtering (loses precision), Mandatory filter (too rigid)

### RAG Guardrails
**Q:** Should we add guardrail middleware for RAG responses?
**A:** Yes, citation verification
**Decision:** Verify the agent's response references actual retrieved content. Log warnings if agent appears to fabricate information not found in retrieved documents. Non-blocking (warns, doesn't reject).
**Rejected:** No guardrails (misses hallucination risk), Strict blocking (may cause response failures)
