# RAG Pipeline with PDF Knowledge Base

> "Nothing says 'regulated fintech' like downloading PDFs from the internet and trusting an AI to read them correctly."
> - El Barto

## Overview

**Request**: Implement a RAG (Retrieval-Augmented Generation) tool that downloads 3 PDF documents from controlled URLs, processes them with PDFPlumberLoader (for table extraction), embeds them into ChromaDB, and exposes a knowledge retrieval tool to the conversational agent.

**Created**: 2026-02-19

## What

A complete RAG pipeline that:
- Downloads 3 PDFs (VeraMoney history, fintech regulation, bank regulation) from R2 CDN URLs
- Processes PDFs with PDFPlumberLoader preserving table structure
- Splits documents with type-specific chunk sizes
- Embeds chunks using OpenAI text-embedding-3-small
- Stores in a single ChromaDB collection with rich metadata
- Exposes an async `search_knowledge` tool with optional document_type filtering
- Loads data on application startup (check-and-load strategy)
- Includes citation verification guardrails

## Why

This is a bonus task for the VeraMoney technical assessment that demonstrates:
- RAG pipeline architecture in a regulated fintech context
- Vector database integration (ChromaDB already configured in docker-compose)
- Document processing with table-aware loaders
- Agent tool integration following existing patterns
- Production-ready patterns (startup loading, guardrails, metadata filtering)

## Impact

- New modules: `src/rag/` (4-5 files), `src/tools/knowledge/` (3 files)
- Modified files: agent creation, system prompt, middleware, settings, lifespan, Chainlit handlers
- New dependency: `pdfplumber` (for PDFPlumberLoader)
- ChromaDB collection: `veramoney_knowledge` with ~100-300 chunks from 3 PDFs
