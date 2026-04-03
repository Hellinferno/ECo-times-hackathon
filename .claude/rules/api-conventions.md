# API Conventions

## EcoMonitor

- Edge functions in `ecomonitor/api/` must stay self-contained.
- Do not import browser app code into edge handlers.
- Preserve request-varying cache keys and existing cache helpers.
- Keep server-side fetches explicit about headers and runtime boundaries.

## FastAPI Projects

- Keep auth, config, and dependency wiring explicit and environment-driven.
- Preserve clear router boundaries and do not hide security-sensitive behavior in implicit globals.
- Schema, persistence, and migration changes should stay aligned with project-native docs and commands.

## Secrets And Exposure

- Never commit `.env` files, tokens, or machine-local settings.
- Keep local overrides in gitignored files such as `CLAUDE.local.md` and `.claude/settings.local.json`.
- Review CORS, auth, and permission changes as security-sensitive even when the code change is small.
