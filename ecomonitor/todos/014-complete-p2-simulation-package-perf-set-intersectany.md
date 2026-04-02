---
status: complete
priority: p2
issue_id: "014"
tags: [code-review, deep-forecast, simulation-package, performance]
---

# Simulation package builder performance cleanup

## Resolution

- `buildSimulationPackageEntities` computes `allForecastIdSet` once and uses `Set.has()` for actor-registry membership checks.
- `isMaritimeChokeEnergyCandidate` uses `Array.includes()` for the small `marketBucketIds` list instead of allocating a `Set` per candidate.
- The simulation-package export suite remains the release gate for these optimizations.

## Technical Details

- File: `scripts/seed-forecasts.mjs`
- Tests: `tests/forecast-trace-export.test.mjs`

## Work Log

- 2026-03-24: Found by performance review on PR #2204.
- 2026-04-02: Closed. The remaining bucket-check allocation was removed and the actor-registry loop already used the shared forecast-id set.
