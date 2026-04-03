---
name: deploy
description: Safe release-preparation workflow for AlphaHunter, EcoMonitor, and AIBAA. Routes to project-native test, lint, build, and migration commands instead of inventing new root deployment logic.
---

# Deploy

Use this skill when preparing one of the three canonical projects for deployment or handoff.

## Workflow

1. Confirm the target project and deployment surface.
2. Use the project's documented validation commands.
3. Verify secrets stay external and local overrides are ignored.
4. Build only the artifacts relevant to the target.
5. Summarize what is ready, what was verified, and what still needs operator action.

## Project Defaults

### AlphaHunter

- `cd alphahunter && make test`
- `cd alphahunter && make lint`
- `cd alphahunter && make build-frontend`

### EcoMonitor

- `cd ecomonitor && npm run typecheck`
- `cd ecomonitor && npm run test:data`
- `cd ecomonitor && npm run build:full`

### AIBAA

- `cd "AI Investment Banking Analyst Agent (AIBAA)" && make test`
- `cd "AI Investment Banking Analyst Agent (AIBAA)" && make lint`
- `cd "AI Investment Banking Analyst Agent (AIBAA)" && make migrate`

## Guardrails

- Do not route deployment work through `worldmonitor/` by default.
- Do not commit environment secrets or local settings while preparing a release.
- If docs and commands disagree, update the project-native docs in the same task.
