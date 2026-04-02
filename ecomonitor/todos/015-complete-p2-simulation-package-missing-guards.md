---
status: complete
priority: p2
issue_id: "015"
tags: [code-review, deep-forecast, simulation-package, correctness]
---

# Simulation package null-guard and fallback cleanup

## Resolution

- `buildSimulationPackageEvaluationTargets` warns when a theater cannot be resolved back to a candidate.
- `selectedTheaters` falls back to `dominantRegion || 'unknown theater'` so simulation prompts never emit literal `undefined`.
- `buildSimulationStructuralWorld` supports both scalar and array `macroRegion` values on incoming signals.
- Regression tests cover the missing-label and `macroRegion: string[]` cases.

## Technical Details

- File: `scripts/seed-forecasts.mjs`
- Tests: `tests/forecast-trace-export.test.mjs`

## Work Log

- 2026-03-24: Found by correctness review on PR #2204.
- 2026-04-02: Closed. Missing-candidate logging, theater-label fallback, and `macroRegion` array handling are all in place.
