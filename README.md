# AIBAA — AI Investment Banking Analyst Agent

[![Version](https://img.shields.io/badge/version-1.0.0--alpha-blue.svg)](.)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Node](https://img.shields.io/badge/Node-18+-339933?style=flat&logo=node.js&logoColor=white)](https://nodejs.org)
[![Gemini](https://img.shields.io/badge/Gemini_API-Powered-4285F4?style=flat&logo=google&logoColor=white)](https://ai.google.dev)
[![NVIDIA](https://img.shields.io/badge/NVIDIA_NIM-Powered-76B900?style=flat&logo=nvidia&logoColor=white)](https://build.nvidia.com)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](.)

**Industry-Grade AI-Powered Financial Analysis Platform**

[Features](#features) · [Quick Start](#quick-start) · [Architecture](#architecture) · [Configuration](#configuration) · [Roadmap](#roadmap)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Development Commands](#development-commands)
- [Roadmap](#roadmap)

---

## Overview

**AIBAA** (AI Investment Banking Analyst Agent) is an enterprise-grade financial analysis platform built on a sophisticated Multi-Agent architecture. It leverages foundational models to automate complex, time-consuming investment banking tasks.

The current version represents **Version 1.0 (Alpha)** with core infrastructure, authentication APIs, and the financial modeling engine foundation (DCF and LBO) complete.

---

## Features

### Orchestrator & Multi-Agent Framework

- **Task Routing:** Routes queries to six specialized AI agents: Financial Modeling, Pitchbook, Due Diligence, Market Research, Doc Drafter, Coordination
- **RAG Pipeline (WIP):** Semantic chunking and vector retrieval context via ChromaDB

### Advanced Financial Engines

- **DCF (Discounted Cash Flow):** Multi-scenario (Base/Bear/Bull) analysis, WACC calculators, implied share price ranges
- **LBO (Leveraged Buyout):** Sources & Uses mechanics, IRR targets, MOIC calculations, debt scheduling
- **Excel Generation:** Automated professional IB-quality `.xlsx` models with assumptions, scenario heatmaps, and DCF/LBO outputs

### Backend & Infrastructure

- **FastAPI Foundation:** Performant API layer with dependency-injected auth, idempotency, and security headers
- **Database:** SQLAlchemy + Alembic (SQLite for dev, PostgreSQL for production)
- **Docker Ready:** Composable microservices — `api`, `web`, `db`, `redis`, `chroma`

---

## Architecture

```text
┌────────────────────────────────────────────────────────────┐
│                   Frontend (Vite / React)                  │
│          Deals │ Documents │ Agents │ Outputs              │
└───────────────────────────┬────────────────────────────────┘
                            │ HTTP/REST
┌───────────────────────────▼────────────────────────────────┐
│                  Backend (FastAPI / Python)                 │
│          Deals │ Documents │ Agents │ Outputs              │
│                                                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │               Agent Orchestrator                    │   │
│  └──────┬──────────┬──────────┬───────────┬────────────┘   │
│         │          │          │           │                 │
│  ┌──────▼──┐ ┌─────▼───┐ ┌───▼──┐ ┌──────▼──────┐         │
│  │Modeling │ │Pitchbook│ │ Docs │ │  Research   │         │
│  │ Agents  │ │  Agent  │ │Agent │ │   Agent     │         │
│  └─────────┘ └─────────┘ └──────┘ └─────────────┘         │
└────────────────────────────────────────────────────────────┘
         │                    │                  │
┌────────▼───────┐  ┌─────────▼──────┐  ┌───────▼──────┐
│  PostgreSQL 16 │  │   Redis 7      │  │  ChromaDB    │
│  (primary db)  │  │  (cache/queue) │  │  (vectors)   │
└────────────────┘  └────────────────┘  └──────────────┘
```

---

## Quick Start

### Prerequisites

- Docker Compose
- Python 3.11+
- Node.js 18+

### Clone Repository

```bash
git clone https://github.com/Hellinferno/ECo-times-hackathon.git
cd "ECo-times-hackathon/AI Investment Banking Analyst Agent (AIBAA)"
```

### Option 1: Docker (recommended)

```bash
cp .env.example .env   # fill in GEMINI_API_KEY, NVIDIA_API_KEY, AIBAA_JWT_SECRET
make up
```

- **API / Docs:** <http://localhost:8000/docs>
- **Web App:** <http://localhost:3000>

### Option 2: Local (no Docker)

**Backend:**

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
make install
make migrate
make dev-api
```

**Frontend:**

```bash
make dev-web
```

---

## Configuration

Copy `.env.example` to `.env` and fill in values:

```env
# Security & Auth
AIBAA_JWT_SECRET=your_jwt_secret_here
AIBAA_ENV=development

# Database
DATABASE_URL=sqlite:///./aibaa.db
# Production: postgresql://user:password@localhost/aibaa

# AI APIs
GEMINI_API_KEY=your_google_ai_key
NVIDIA_API_KEY=your_nvidia_nim_key
```

---

## Development Commands

| Command | Action |
|---------|--------|
| `make up` | Start all Docker services |
| `make down` | Stop all running services |
| `make logs` | Tail the `api` container logs |
| `make test` | Run Pytest suite for backend |
| `make lint` | Run Ruff (Python) + ESLint (frontend) |
| `make migrate` | Apply `alembic upgrade head` |

---

## Roadmap

- **Phase 0:** Foundation, Auth & Infrastructure — *Completed*
- **Phase 1:** Core Backend + Data Layer — *In Progress*
- **Phase 2:** RAG Pipeline + Agent Framework — *Stubbed*
- **Phase 3:** Computation Engine + First Agent — *DCF/LBO Built*
- **Phase 4:** Full Agent Suite + PDF/Word Generation
- **Phase 5:** Complete Frontend Workflows

---

← [Back to suite overview](../README.md)
