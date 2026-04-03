# Root Claude Workspace

This file is the repo-root entry point for Claude and other coding agents working in this monorepo.

## Canonical Projects

- `alphahunter/`: stock intelligence platform.
- `ecomonitor/`: canonical WorldMonitor and EcoMonitor codebase.
- `AI Investment Banking Analyst Agent (AIBAA)/`: investment banking platform.

## Precedence

1. Repo-visible files are the system of record.
2. Project-local guidance takes precedence inside that project.
3. Inside `AI Investment Banking Analyst Agent (AIBAA)/`, the nested `.claude/` is authoritative for project-specific workflows.
4. `CLAUDE.local.md` is optional personal guidance and must stay uncommitted.

## Non-Canonical Tree

- `worldmonitor/` is a duplicate-candidate tree. Do not delete, merge, or implement fixes there unless the task explicitly targets it.
- When a request refers to WorldMonitor, use `ecomonitor/` by default.

## Start Here

- Read the root [`README.md`](README.md) for the suite overview.
- For `ecomonitor/`, read [`ecomonitor/AGENTS.md`](ecomonitor/AGENTS.md) before going deeper.
- For `alphahunter/`, start with [`alphahunter/README.md`](alphahunter/README.md), [`alphahunter/Makefile`](alphahunter/Makefile), and [`alphahunter/SECURITY.md`](alphahunter/SECURITY.md).
- For AIBAA, start with [`AI Investment Banking Analyst Agent (AIBAA)/README.md`](<AI Investment Banking Analyst Agent (AIBAA)/README.md>), then use its nested `.claude/`.

## Workspace Layout

- `.claude/commands/`: shared slash-command playbooks.
- `.claude/rules/`: monorepo-wide guardrails.
- `.claude/skills/`: reusable workflows for review, deployment, and future optimization work.
- `.claude/agents/`: reviewer and auditor personas for parallel review loops.

## Safety Defaults

- Keep machine-specific permissions in local settings only.
- Prefer canonical tracked paths over duplicate or archival trees.
- Do not modify generated assets unless regeneration is part of the task.
- Do not commit secrets, local overrides, or temporary agent workspaces.
