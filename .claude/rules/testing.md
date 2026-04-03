# Testing Defaults

Use the smallest verification set that proves the change is correct, then expand only when the touched surface requires it.

## AlphaHunter

- Backend default: `cd alphahunter && make test`
- Frontend default: `cd alphahunter && make lint`
- Use `make build-frontend` when frontend bundling behavior changes

## EcoMonitor

- Default checks:
  - `cd ecomonitor && npm run typecheck`
  - `cd ecomonitor && npm run test:data`
- Add `npm run typecheck:api` for server or API contract changes
- Use browser verification when UI behavior, routing, or rendering changes

## AIBAA

- Default checks:
  - `cd "AI Investment Banking Analyst Agent (AIBAA)" && make test`
  - `cd "AI Investment Banking Analyst Agent (AIBAA)" && make lint`
- Add `make migrate` verification when schema or persistence behavior changes

## Reporting

- State exactly which checks ran.
- If a check did not run, say why.
- Call out residual risk when verification stays partial.
