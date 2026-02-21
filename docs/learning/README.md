# VeraMoney Apply - Learning Documentation

> **Knowledge Library Catalog**

This directory contains curated technical knowledge extracted from code reviews, implementation experiences, and best practices research. Each "book" focuses on a specific domain and follows a structured format for maximum educational value.

---

## Library Catalog

### Security Patterns
**File**: `security-patterns.md`

Security vulnerabilities and their remediation patterns for production Python applications.

| Topic | Impact | Location |
|-------|--------|----------|
| Timing Attack Prevention | Critical | API key validation |
| Hardcoded Credentials | Critical | Documentation and code |
| Default Passwords | High | Configuration classes |
| SSRF Prevention | Critical | URL fetching utilities |
| Exception Handling | Medium | Error middleware |

### Async and Resource Management Patterns
**File**: `async-resource-management.md`

Concurrency patterns, resource lifecycle management, and reliability patterns for async Python applications.

| Topic | Impact | Location |
|-------|--------|----------|
| Race Condition Prevention | High | Lazy initialization |
| Connection Pooling | High | HTTP clients |
| Blocking Calls in Async | High | Sync SDK integration |
| None Guards | Medium | Optional nested attributes |
| Division by Zero | Medium | Financial calculations |

### SOLID Principles and Clean Code Patterns
**File**: `solid-clean-code.md`

Software architecture principles, maintainability patterns, and type safety practices.

| Topic | Impact | Location |
|-------|--------|----------|
| Single Responsibility | High | Handler decomposition |
| DRY Principle | Medium | Factory functions |
| Dependency Injection | High | Tool creation |
| Interface Segregation | Medium | Configuration splitting |
| Magic Strings to Enums | Medium | Status values |
| JSON Construction | Medium | Response formatting |

---

## Reading Guide

### For Security Reviews
Start with `security-patterns.md` to understand common vulnerabilities in Python web applications. Each pattern includes the wrong path (anti-pattern) and the path of excellence (correct pattern) with full code examples.

### For Performance Optimization
Review `async-resource-management.md` to identify connection pooling opportunities, race conditions, and blocking calls that may impact application responsiveness.

### For Architecture Improvements
Consult `solid-clean-code.md` for guidance on decomposing large classes, eliminating duplication, and improving type safety across the codebase.

---

## Contribution Guidelines

When adding new learnings:

1. **Identify the appropriate book** - Check existing files for the most relevant category
2. **Follow the entry format** - Each entry must include:
   - Investigation Thesis (root cause analysis)
   - Bibliographic Evidence (official sources)
   - Application Impact (domain and severity)
   - Anti-pattern and Correct Pattern (code examples)
   - Reasoning (connections to broader concepts)
3. **Update the table of contents** - Add new entries to the book's TOC
4. **Cross-reference related topics** - Link to other books when applicable

---

## Quality Standards

All entries must:
- Cite official documentation or authoritative sources
- Include runnable code examples
- Follow Python 3.11+ syntax
- Adhere to the project's async-first architecture
- Avoid comments in code (self-documenting code only)

---

*Last Updated: 2026-02-21*
