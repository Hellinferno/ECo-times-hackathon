# Code Style And Guardrails

## Source Of Truth

- Prefer repo-visible docs over hidden memory or unpublished local notes.
- Read the target project's README and guidance before changing code.
- Inside AIBAA, respect the nested `.claude/` and local project conventions.

## Canonical Paths

- Use `ecomonitor/` as the canonical WorldMonitor and EcoMonitor tree.
- Treat `worldmonitor/` as a duplicate-candidate path unless the task explicitly targets it.
- Do not land fixes only in a duplicate or archive tree.

## Editing Rules

- Match the existing style of the target project instead of forcing one repo-wide style.
- Default to ASCII unless the file already needs Unicode.
- Keep comments short and only where they help future readers.
- Do not edit generated or vendor artifacts unless regeneration is part of the task.

## Safety

- Avoid destructive git and filesystem operations unless explicitly requested.
- Keep machine-specific permissions out of committed settings.
- Never commit secrets, local overrides, or temporary agent work folders.
