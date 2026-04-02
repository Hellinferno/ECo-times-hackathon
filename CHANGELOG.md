# Changelog

All notable AIBAA changes are documented here.

## 2026-04-02 - Phase 2 hardening

### Agent and RAG lifecycle

- Added background RAG indexing through the worker with explicit lifecycle state transitions.
- Added `rag_status`, `rag_indexed_at`, and `rag_error` to document-facing responses.
- Added startup recovery and persistence updates so database state is the source of truth for document workflows.

### Safety and auditability

- Added prompt-guard sanitization for user text, retrieved chunks, and full-document fallback context.
- Added security audit logging for prompt-injection attempts and guard events.
- Added explicit retrieval trace data and reasoning-step logging for agent runs.

### Registry and admin controls

- Expanded the model registry with eval summaries, canary status, and rollout notes.
- Added admin APIs for stage, validate, promote, rollback, eval reports, and audit-log access.

### Verification

- `pytest apps/api/src/test_auth_security.py -q`
- `pytest apps/api/src/test_orchestrator_routing.py -q`
- `python -m compileall apps/api/src`
