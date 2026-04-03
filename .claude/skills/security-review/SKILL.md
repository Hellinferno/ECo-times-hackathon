---
name: security-review
description: Repo-wide security review workflow for the ECo Times monorepo. Focuses on unsafe permissions, secrets exposure, auth and CORS handling, and accidental inclusion of local-only files or duplicate-tree edits.
---

# Security Review

Use this skill when auditing changes in `alphahunter/`, `ecomonitor/`, or `AI Investment Banking Analyst Agent (AIBAA)/`.

## Scope

- committed permissions and local settings hygiene
- secrets, `.env`, and credential leaks
- auth, session, and CORS behavior
- destructive scripts or risky shell instructions
- accidental work in non-canonical trees such as `worldmonitor/`

## Workflow

1. Identify the canonical project path.
2. Read repo-visible guidance first.
3. Inspect changed files for:
   - auth bypasses
   - over-broad CORS or origin matching
   - unsafe file or process permissions
   - local settings committed by mistake
   - secrets in docs, config, or tests
4. Run the minimum project checks needed to support the review.
5. Report findings first, ordered by severity.

## Monorepo Notes

- `ecomonitor/` is canonical for WorldMonitor work.
- AIBAA has its own nested `.claude/` and local ignore rules that should remain in place.
- Root committed settings should stay portable and free of machine-specific permissions.
