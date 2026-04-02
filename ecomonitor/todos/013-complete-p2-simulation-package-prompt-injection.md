---
status: complete
priority: p2
issue_id: "013"
tags: [code-review, deep-forecast, simulation-package, security]
---

# Simulation package prompt-injection hardening

## Resolution

- `buildSimulationRequirementText` sanitizes theater label, state kind, top channel, and derived critical-signal labels before interpolation.
- `buildSimulationPackageEventSeeds` sanitizes event-seed summaries before truncation.
- Actor-registry, state-summary, evidence-derived, and fallback entity names are sanitized before becoming `name` or slug input.
- Regression tests cover newline injection in `simulationRequirement` and sanitized entity emission.

## Technical Details

- File: `scripts/seed-forecasts.mjs`
- Tests: `tests/forecast-trace-export.test.mjs`

## Work Log

- 2026-03-24: Found by code-review/security review on PR #2204.
- 2026-04-02: Closed. Simulation-package strings are sanitized before they can be persisted into downstream LLM-facing artifacts.
