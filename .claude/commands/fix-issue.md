# /project:fix-issue

Use this command for bug fixes, regressions, and targeted cleanup tasks.

## Flow

1. Reproduce the issue or locate the failing path.
2. Resolve the canonical project path before editing.
   - Use `ecomonitor/` for WorldMonitor and EcoMonitor work.
   - Treat `worldmonitor/` as read-only duplicate-candidate context unless explicitly requested.
3. Read the local project guidance before changing code.
4. Implement the smallest safe fix that addresses the root cause.
5. Verify with the minimum impacted tests and checks.
6. Summarize the fix, verification, and any follow-up risk.

## Guardrails

- Do not patch only the duplicate tree.
- Do not introduce new root-level deploy scripts when project-native entrypoints already exist.
- Keep project-local `.claude/` behavior intact inside AIBAA.
- Preserve generated files unless regeneration is part of the fix.
