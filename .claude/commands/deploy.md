# /project:deploy

Use this command for safe release preparation and deployment routing. Do not invent new top-level deploy flows when project-native entrypoints already exist.

## Shared Release Checklist

1. Confirm the target project and environment.
2. Run the project's documented tests and lint/build steps.
3. Verify required environment variables are externalized and not committed.
4. Prefer the documented project entrypoints below.
5. Record what was verified and what still needs operator action.

## Project Entry Points

### AlphaHunter

- Dev and infra: `cd alphahunter && docker compose up -d postgres redis`
- Tests: `cd alphahunter && make test`
- Frontend lint/build: `cd alphahunter && make lint` and `cd alphahunter && make build-frontend`

### EcoMonitor

- Validation: `cd ecomonitor && npm run typecheck`
- Data tests: `cd ecomonitor && npm run test:data`
- Release build: `cd ecomonitor && npm run build:full`
- Variant or desktop releases should use the documented `npm run build:*` or `npm run desktop:*` commands

### AIBAA

- Validation: `cd "AI Investment Banking Analyst Agent (AIBAA)" && make test`
- Lint: `cd "AI Investment Banking Analyst Agent (AIBAA)" && make lint`
- Migrations: `cd "AI Investment Banking Analyst Agent (AIBAA)" && make migrate`
- Local stack bring-up: `cd "AI Investment Banking Analyst Agent (AIBAA)" && make up`

## Notes

- `worldmonitor/` is not a deployment target in this root workflow.
- If deployment docs and repo behavior drift, update the project-native docs in the same change.
