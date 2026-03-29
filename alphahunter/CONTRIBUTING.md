# Contributing to AlphaHunter

Thank you for your interest in contributing. This document covers how to set up your environment, the code conventions we follow, and the pull request process.

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Code Style](#code-style)
- [Running Tests](#running-tests)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Signal Development Guide](#signal-development-guide)

---

## Development Setup

**Prerequisites:** Python 3.11+, Node 20+, Docker + Docker Compose (optional but recommended)

```bash
# Clone the repo
git clone https://github.com/your-org/alphahunter.git
cd alphahunter

# Backend
cd apps/backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Copy and configure environment
cp ../../.env.example ../../.env
# Edit .env — GEMINI_API_KEY is optional (template fallback works without it)

# Run with SQLite (no Docker needed)
uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
cd apps/frontend
npm install
npm run dev
```

**With Docker (full stack including PostgreSQL + Redis):**
```bash
docker compose up -d
```

The backend auto-creates DB tables on startup (`Base.metadata.create_all`). Alembic migrations are used for production schema changes.

---

## Project Structure

```
alphahunter/
  apps/
    backend/
      agents/          6-agent pipeline (DataAgent → ... → AuditAgent)
      api/endpoints/   FastAPI route handlers
      models/db/       SQLAlchemy ORM models
      providers/       External data providers (TinyFish, NSE direct)
      services/        Business logic services (AlertService, etc.)
      utils/           Shared helpers (runtime_settings, etc.)
    frontend/
      src/             React 19 + TypeScript pages and components
  .env.example         Template for required environment variables
  LICENSE              Apache 2.0
```

---

## Code Style

**Python (backend):**
- Follow PEP 8. Use `ruff` for linting if available.
- Type hints on all public functions.
- Docstrings on all classes and non-trivial methods.
- Never catch `Exception` broadly without logging and re-raising or having a specific fallback.

**TypeScript (frontend):**
- Strict mode enabled (`"strict": true` in tsconfig).
- Prefer named exports over default exports.
- Keep API calls in `src/api/client.ts`, not scattered across components.

**Commit messages:** Use conventional commits:
```
feat(signal): add RSI oversold detection
fix(scan): prevent alert creation when confidence < threshold
chore(deps): upgrade yfinance to 0.2.x
```

---

## Running Tests

```bash
# Backend
cd apps/backend
pytest -v --cov=. --cov-report=term-missing

# Frontend
cd apps/frontend
npm run test
```

**Coverage targets:**
- Agent logic (SignalAgent, DecisionAgent, BacktestingAgent): > 80%
- API endpoints: > 70%
- NaN sanitisation utilities: 100%

---

## Submitting a Pull Request

1. **Fork** the repository and create a branch: `git checkout -b feat/my-feature`
2. Make your changes with tests.
3. Run the full test suite locally (both backend and frontend).
4. Open a PR against `main`. Fill in the PR template.
5. The CI pipeline runs automatically — all checks must pass before review.

**PR checklist:**
- [ ] Tests added or updated for changed logic
- [ ] No `print()` statements left in backend code (use `logger.info/debug`)
- [ ] New environment variables added to `.env.example`
- [ ] No hardcoded API keys or secrets
- [ ] `OHLCV` data used in tests uses synthetic data, not real stock prices

---

## Signal Development Guide

Adding a new signal to `SignalAgent`:

1. Add a `_detect_<signal_name>(self, ...) -> Tuple[bool, Dict[str, Any]]` method
2. Call it in `detect_signals()` alongside the other signals
3. Add the signal to `legacy_signal_count` (or `extended_signal_count` if TinyFish-dependent)
4. Include `strength` (0.0–1.0) in the details dict — used for composite scoring
5. Add a corresponding `_find_<signal_name>_analogues()` method to `BacktestingAgent`
6. Add unit tests with synthetic OHLCV data in `tests/unit/test_signal_agent.py`

Signal strength guidelines:
- `1.0` = extremely strong signal (rare, high conviction)
- `0.5–0.8` = typical strong signal
- `0.1–0.4` = weak but present
- `0.0` = signal not triggered (never set strength > 0 when signal is False)
