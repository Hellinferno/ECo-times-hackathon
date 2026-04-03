# /project:review

Use this command for code review, change audits, and pre-merge checks in this monorepo.

## Flow

1. Identify the affected project and canonical path.
2. Read repo-visible context first:
   - Root [`CLAUDE.md`](../../CLAUDE.md)
   - Target project README
   - [`ecomonitor/AGENTS.md`](../../ecomonitor/AGENTS.md) for EcoMonitor work
   - AIBAA nested `.claude/` when working inside AIBAA
3. Review findings first, ordered by severity: blocker, major, minor, suggestion.
4. Always include a security pass:
   - secrets or local-only files
   - auth and CORS mistakes
   - unsafe permissions or destructive scripts
   - duplicate-tree edits in non-canonical paths
5. Run only the minimum impacted checks for the touched area.

## Minimum Checks by Project

- `alphahunter/`
  - `cd alphahunter && make test`
  - `cd alphahunter && make lint`
- `ecomonitor/`
  - `cd ecomonitor && npm run typecheck`
  - `cd ecomonitor && npm run test:data`
  - Use browser verification when UI behavior changes
- `AI Investment Banking Analyst Agent (AIBAA)/`
  - `cd "AI Investment Banking Analyst Agent (AIBAA)" && make test`
  - `cd "AI Investment Banking Analyst Agent (AIBAA)" && make lint`

## Output

- Findings first with file references.
- Brief note on what was checked.
- Call out residual risk or missing verification explicitly.
