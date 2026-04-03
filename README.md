<div align="center">

# ECo Times Hackathon — AI Financial Intelligence Suite

[![Hackathon](https://img.shields.io/badge/ECo_Times-Hackathon_2026-FF6B35?style=for-the-badge)](https://github.com/Hellinferno/ECo-times-hackathon)
[![Projects](https://img.shields.io/badge/Projects-3-4F46E5?style=for-the-badge)](#the-suite)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-007ACC?style=for-the-badge&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Gemini](https://img.shields.io/badge/Gemini_API-Powered-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)

**One monorepo. Three AI-powered platforms. Built for the ECo Times Hackathon.**

[AlphaHunter](#-alphahunter-ai) · [EcoMonitor](#-ecomonitor) · [AIBAA](#-aibaa) · [Quick Start](#-quick-start) · [Deployment](#-deployment)

</div>

---

## The Suite

Three independent yet complementary platforms that cover the full spectrum of AI-powered financial intelligence — from real-time stock signals and global geopolitical risk to enterprise-grade investment banking automation.

---

## Latest Update

The current repository state includes a full Phase 2 hardening pass across the suite:

- **AIBAA:** background RAG indexing, auditable document state, prompt-injection guards, model-registry governance endpoints, and traceable agent runs
- **AlphaHunter:** exact-input reasoning cache keys, output validation against numeric payloads, deterministic fallbacks, and scheduled calibration snapshots
- **EcoMonitor:** safer simulation-package entity sanitization, `macroRegion` array support, and synchronized Phase 2 backlog records
- **Shared evaluation layer:** gold datasets and eval scaffolding under [`datasets/`](datasets) and [`evals/`](evals) for router, retriever, extractor, reasoner, and validator workflows

See [`CHANGELOG.md`](CHANGELOG.md) for the release-style summary of the implemented work and verification steps.

- **Monorepo developer workflow:** canonical project routing and contributor guardrails are now documented in [`CLAUDE.md`](CLAUDE.md), with shared commands, rules, and skills under [`.claude/`](.claude)

---

### AlphaHunter AI

> **Autonomous Stock Market Intelligence Engine for Indian Retail Investors**

[![Docs](https://img.shields.io/badge/README-alphahunter%2F-blue?style=flat)](alphahunter/README.md)
[![Stack](https://img.shields.io/badge/FastAPI_+_React_+_Gemini-stack-informational?style=flat)]()

AlphaHunter continuously monitors **100+ NSE-listed stocks**, detects trading opportunities using a 6-agent AI pipeline, validates every signal against **2 years of historical data**, and delivers actionable trade recommendations with entry, target, and stop-loss levels — explained in plain English.

**Key capabilities:**
- Real-time market scanning every 15 minutes during market hours
- 3 signal algorithms: Breakout, Volume Spike, Bulk Deal detection
- Gemini-powered reasoning grounded in actual price/volume data
- Reasoning outputs are validated against exact signal numbers before display, with deterministic fallback on mismatch
- Confidence-scored decisions: **BUY / WATCH / AVOID** (0–100 scale)
- Full decision audit trail with track record

**Tech:** Python 3.11 · FastAPI · PostgreSQL · Redis · React 19 · Tailwind CSS 4 · Gemini API · yfinance · Docker

→ [Full documentation](alphahunter/README.md)

---

### EcoMonitor

> **Real-Time Global Intelligence Dashboard**

[![Docs](https://img.shields.io/badge/README-ecomonitor%2F-blue?style=flat)](ecomonitor/README.md)
[![Live](https://img.shields.io/badge/Live-worldmonitor.app-green?style=flat)](https://worldmonitor.app)
[![Stack](https://img.shields.io/badge/TypeScript_+_Tauri_+_deck.gl-stack-informational?style=flat)]()

WorldMonitor is a sophisticated situational awareness platform aggregating **435+ curated news feeds**, real-time geospatial data, and financial market signals into a unified AI-synthesized intelligence brief. It runs as a web app, PWA, or native desktop app.

**Key capabilities:**
- 435+ feeds across 15 categories, AI-synthesized into actionable briefs
- Dual map engine: 3D globe (globe.gl) + WebGL flat map (deck.gl) with 45 data layers
- Country Intelligence Index: composite risk scoring across 12 signal categories
- Finance radar: 92 stock exchanges, commodities, crypto, 7-signal market composite
- Local AI with Ollama — no API keys required
- Native desktop app (Tauri 2) for Windows, macOS, Linux
- 5 site variants from a single codebase · 21 languages + RTL

**Tech:** Vanilla TypeScript · Vite · globe.gl · deck.gl · MapLibre GL · Tauri 2 (Rust) · Ollama · Convex · Protocol Buffers

→ [Full documentation](ecomonitor/README.md) · [Live app](https://worldmonitor.app)

---

### AIBAA

> **AI Investment Banking Analyst Agent**

[![Docs](https://img.shields.io/badge/README-AIBAA%2F-blue?style=flat)](<AI Investment Banking Analyst Agent (AIBAA)/README.md>)
[![Stack](https://img.shields.io/badge/FastAPI_+_React_+_Gemini_+_NVIDIA_NIM-stack-informational?style=flat)]()
[![Version](https://img.shields.io/badge/version-1.0.0--alpha-blue.svg)]()

AIBAA is an enterprise-grade financial analysis platform built on a Multi-Agent architecture. It automates complex investment banking tasks — DCF/LBO modeling, pitchbook generation, due diligence — through six specialized AI agents orchestrated by a central routing layer.

**Key capabilities:**
- Multi-agent orchestration: Financial Modeling · Pitchbook · Due Diligence · Market Research · Doc Drafter · Coordination
- DCF modeling: multi-scenario (Base/Bear/Bull), WACC calculator, implied share price ranges
- LBO modeling: Sources & Uses mechanics, IRR targets, MOIC, debt scheduling
- Professional-grade Excel generation (`.xlsx` IB models)
- Auditable RAG pipeline with background indexing, prompt guards, and traceable chunk usage

**Tech:** Python 3.11 · FastAPI · PostgreSQL · Redis · ChromaDB · React · Vite · Gemini API · NVIDIA NIM · Docker

→ [Full documentation](<AI Investment Banking Analyst Agent (AIBAA)/README.md>)

---

## Architecture Overview

The three platforms are independent deployments that can share data through well-defined interfaces:

```text
┌─────────────────────────────────────────────────────────────────┐
│                    ECo Times AI Suite                           │
│                                                                 │
│  ┌─────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │  AlphaHunter    │  │  WorldMonitor     │  │    AIBAA      │ │
│  │                 │  │                  │  │               │ │
│  │ NSE Stock       │  │ Geopolitical     │  │ Investment    │ │
│  │ Intelligence    │  │ Risk Monitoring  │  │ Banking AI    │ │
│  │                 │  │                  │  │               │ │
│  │ FastAPI+React   │  │ TypeScript+Tauri │  │ FastAPI+React │ │
│  │ Gemini API      │  │ Local AI/Ollama  │  │ Gemini+NVIDIA │ │
│  └────────┬────────┘  └────────┬─────────┘  └───────┬───────┘ │
│           │                   │                     │         │
│           └───────────────────┼─────────────────────┘         │
│                               │                               │
│               WorldMonitor sidecar integration                │
│          (macro/market/geopolitical risk data → AIBAA)        │
└─────────────────────────────────────────────────────────────────┘
```

> AIBAA optionally mounts WorldMonitor as a sidecar service to feed live macroeconomic, geopolitical, and commodity data into its financial models.

---

## Repository Structure

```text
ECo-times-hackathon/
├── alphahunter/                          # AlphaHunter AI — NSE stock intelligence
│   ├── apps/
│   │   ├── backend/                      # FastAPI + 6-agent pipeline
│   │   └── frontend/                     # React 19 + TypeScript SPA
│   ├── docker-compose.yml
│   ├── Makefile
│   └── README.md                         ← AlphaHunter documentation
│
├── ecomonitor/                          # EcoMonitor — global intelligence dashboard
│   ├── src/                              # Vite TypeScript app (apps/web/)
│   ├── apps/
│   │   └── web/                          # Vite TypeScript app (src/, server/)
│   ├── src-tauri/                        # Rust desktop app
│   ├── vercel.json
│   └── README.md                         ← EcoMonitor documentation
│
├── AI Investment Banking Analyst Agent (AIBAA)/   # AIBAA — investment banking AI
│   ├── apps/
│   │   ├── api/                          # FastAPI backend
│   │   └── web/                          # React frontend
│   ├── aibaa/                            # Core Python package
│   ├── docker-compose.yml
│   └── README.md                         ← AIBAA documentation
│
├── files/                                # Shared project specifications (12 docs)
│   ├── 01-project-overview.md
│   ├── 04-system-architecture.md
│   ├── 08-computation-engine.md
│   └── ...
│
├── .claude/                              # Shared monorepo agent rules, commands, and skills
│   ├── rules/                            # API, code-style, and testing guardrails
│   ├── commands/                         # Reusable fix/review/deploy playbooks
│   ├── skills/                           # Domain workflows (deploy, security-review)
│   └── agents/                           # Reviewer personas (code-reviewer, security-auditor)
│
└── README.md                             ← You are here
```

### Contributor workflow notes

- Use `ecomonitor/` as the canonical WorldMonitor/EcoMonitor tree.
- Treat `worldmonitor/` as a duplicate-candidate path unless explicitly requested.
- Keep machine-local overrides in gitignored files such as `CLAUDE.local.md`.

---

## Quick Start

For a complete local checkout including the standalone AIBAA repository, clone the suite with `--recurse-submodules`.

### AlphaHunter

```bash
git clone --recurse-submodules https://github.com/Hellinferno/ECo-times-hackathon.git
cd ECo-times-hackathon/alphahunter

# Start PostgreSQL + Redis
docker compose up -d postgres redis

# Backend
cd apps/backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt && cp ../../.env.example ../../.env
uvicorn main:app --reload --port 8000

# Frontend (new terminal)
cd apps/frontend && npm install && npm run dev
```
Open <http://localhost:5173> → click **Trigger Market Scan**.

### EcoMonitor

```bash
cd ECo-times-hackathon/ecomonitor
npm install
npm run dev        # http://localhost:5173
```
No environment variables required for basic operation.

### AIBAA

```bash
cd "ECo-times-hackathon/AI Investment Banking Analyst Agent (AIBAA)"
cp .env.example .env   # add GEMINI_API_KEY + AIBAA_JWT_SECRET
make up                # boots api, web, db, redis, chroma via Docker
```
- **API docs:** <http://localhost:8000/docs>
- **Web app:** <http://localhost:3000>

---

## Tech Stack Summary

| | AlphaHunter | WorldMonitor | AIBAA |
|---|---|---|---|
| **Frontend** | React 19, TypeScript, Tailwind 4 | Vanilla TypeScript, Vite | React, Vite, Tailwind |
| **Backend** | Python 3.11, FastAPI | Node.js sidecar, Vercel Edge | Python 3.11, FastAPI |
| **Database** | PostgreSQL 15, Redis 7 | Upstash Redis | PostgreSQL 16, Redis 7 |
| **AI/LLM** | Gemini API | Ollama / Groq / OpenRouter | Gemini API, NVIDIA NIM |
| **Vector Store** | — | — | ChromaDB |
| **Maps/Viz** | Recharts | deck.gl, globe.gl, MapLibre GL | — |
| **Desktop** | — | Tauri 2 (Rust) | — |
| **Deployment** | Vercel + Railway | Vercel Edge Functions | Docker Compose |

---

## Deployment

All three projects support split frontend/backend deployment:

| Project | Frontend | Backend | Database |
|---------|----------|---------|----------|
| AlphaHunter | Vercel (`alphahunter/apps/frontend`) | Railway (single replica) | Railway PostgreSQL |
| WorldMonitor | Vercel Edge (60+ functions) | Railway relay | Upstash Redis |
| AIBAA | Vercel (`AIBAA/apps/web`) | Railway | Railway PostgreSQL |

**Required environment variables per project:**

```bash
# AlphaHunter
GEMINI_API_KEY=...
VITE_API_BASE_URL=https://<railway-backend>/api
ALLOWED_ORIGINS=https://<vercel-domain>

# AIBAA
GEMINI_API_KEY=...
NVIDIA_API_KEY=...
AIBAA_JWT_SECRET=...
DATABASE_URL=postgresql://...
```

---

## Project Specifications

Comprehensive architecture and design documents in [`files/`](files/):

| # | Document |
|---|----------|
| 01 | Project Overview — vision, pipeline, demo flow |
| 02 | User Stories — 23 stories across 8 epics |
| 03 | Information Architecture — navigation, content models |
| 04 | System Architecture — agent pipeline, data flow |
| 05 | Database Schema — 10 tables, DDL, indexes |
| 06 | API Contracts — full REST specification |
| 07 | Monorepo Structure — folder layout, Docker config |
| 08 | Computation Engine — signal detection formulas |
| 09 | Engineering Scope — MVP boundaries, risk register |
| 10 | Development Phases — hackathon build plan |
| 11 | Environment & DevOps — setup, CI/CD, monitoring |
| 12 | Testing Strategy — 30+ test case specifications |

---

## License

| Project | License |
|---------|---------|
| AlphaHunter | Built for the ECo Times Hackathon |
| WorldMonitor | [AGPL-3.0](ecomonitor/LICENSE) — commercial use requires a separate license |
| AIBAA | MIT |

---

<div align="center">

Built for the **ECo Times Hackathon 2026**

</div>
