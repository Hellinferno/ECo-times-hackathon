# Changelog

All notable repository-level changes are documented here.

## 2026-04-02 - Phase 2 hardening pass

### AIBAA

- Added a real RAG indexing lifecycle with `pending -> indexing -> indexed/failed` state handling.
- Exposed `rag_status`, `rag_indexed_at`, and `rag_error` through document-facing APIs.
- Added prompt-guard sanitization for user input and retrieved document context, with security audit logging for suspicious content.
- Extended agent run metadata to include chunk usage, guard events, registry metadata, and prompt versioning.
- Expanded the model registry and admin surface with staging, validation, promote, rollback, eval report, and audit endpoints.

### AlphaHunter

- Replaced coarse reasoning-cache bucketing with exact prompt-content hashing plus prompt/model versioning.
- Added reasoning-output validation so generated narratives must match the numeric signal payload.
- Added deterministic fallback behavior when the model output is invalid or unavailable.
- Added scheduled calibration snapshots and runtime settings for confidence threshold monitoring.

### EcoMonitor

- Hardened simulation-package entity naming by sanitizing actor-derived labels before display and ID generation.
- Added support for `macroRegion` arrays in structural-world filtering.
- Updated simulation-package tests to cover sanitization and `macroRegion: string[]` behavior.
- Reclassified stale pending Phase 2 TODOs into completed records so backlog status matches implementation.

### Shared evaluation and training scaffold

- Added `datasets/<project>/<task>/gold.jsonl` examples for AIBAA, AlphaHunter, and EcoMonitor workflows.
- Added `evals/validate_gold_datasets.py` plus per-project eval directories and report scaffolding.

### Verification

- `pytest "AI Investment Banking Analyst Agent (AIBAA)\\apps\\api\\src\\test_auth_security.py" -q`
- `pytest "AI Investment Banking Analyst Agent (AIBAA)\\apps\\api\\src\\test_orchestrator_routing.py" -q`
- `pytest alphahunter\\apps\\backend\\test_reasoning_agent.py -q`
- `pytest alphahunter\\apps\\backend\\test_api_endpoints.py -q`
- `cmd /c npx tsx --test tests/forecast-trace-export.test.mjs`
- `python evals/validate_gold_datasets.py`
