# OOP Migration Plan

> "Any fool can write code that a computer can understand. Good programmers write code that humans can understand."
> - Martin Fowler

## Overview

**Request**: Migrate the VeraMoney Apply codebase from a functional/procedural architecture with some classes to a fully OOP-oriented structure while preserving all current logic and functionality.

**Created**: 2026-02-20

## What

Transform ~85 standalone module-level functions across 7 layers (API, Agent, Tools, RAG, Observability, Config, Chainlit) into a cohesive OOP architecture with:

1. **Manual Dependency Injection Pattern** - Constructor injection with optional defaults
2. **Service Classes** - Encapsulate related functionality with clear contracts
3. **Base Handler Classes** - Eliminate duplicate code in endpoints
4. **RAG Pipeline as Class** - Break down 152-line function into methods
5. **Preserved Patterns** - Keep LangChain decorators, current tool structure, async-first architecture

## Why

**Current Issues:**
- 85 standalone functions spread across modules
- 3 global singletons (memory store, knowledge client, Langfuse) making testing difficult
- Duplicate code in chat_complete and chat_stream endpoints
- 152-line RAG pipeline function mixing concerns
- Complex import chains with no clear ownership

**Benefits of OOP Migration:**
- **Testability**: Constructor injection enables easy mock injection
- **Maintainability**: Related functionality grouped in classes
- **Readability**: Self-documenting code with clear contracts
- **Scalability**: Easier to extend with new features
- **No Logic Changes**: Methods stay identical, only structure changes

## Impact

| Area | Files Affected | Changes |
|------|---------------|---------|
| **API Layer** | 8 files | Base handler class, endpoint refactoring |
| **Agent Layer** | 6 files | Keep current structure, minor tweaks |
| **Tools Layer** | 9 files | Keep current structure (client + tool function) |
| **RAG Layer** | 7 files | Pipeline class, method extraction |
| **Observability** | 4 files | Manager class, prompt manager class |
| **DI Container** | 2 new files | Service container, initialization |
| **Chainlit** | 5 files | Handler classes |

**Total**: ~41 files touched, 2 new files created
