# VerifAI — Cross-Generation Consistency Hallucination Risk Analysis

[![Backend CI & Hermetic Verification](https://github.com/Arunprasath-2717/VerifAI/actions/workflows/backend-ci.yml/badge.svg?branch=Final)](https://github.com/Arunprasath-2717/VerifAI/actions/workflows/backend-ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)](https://www.sqlalchemy.org/)
[![License](https://img.shields.io/badge/License-Proprietary-gray.svg)]()

VerifAI is an intelligent verification and evaluation system engineered to detect, quantify, and mitigate cross-generation consistency hallucinations in large language model (LLM) workflows.

---

## 1. System Overview & Architecture

VerifAI is designed as a high-throughput **Modular Monolith** powered by **Python and FastAPI**, backed by **Supabase PostgreSQL** via asynchronous SQLAlchemy 2.x and `asyncpg`.

```
VerifAI/
├── backend/          # Core FastAPI modular monolith & async persistence
│   ├── app/          # Application package (core, api/v1, modules)
│   ├── tests/        # Deterministic hermetic test suite (45 unit/integration tests)
│   ├── pyproject.toml# Tooling configuration (pytest, ruff, mypy)
│   ├── requirements.txt      # Pinned production dependencies
│   ├── requirements-dev.txt  # Development & test tooling dependencies
│   └── requirements-lock.txt # Frozen reproducible dependency lockfile
├── database/         # Supabase PostgreSQL schema, migrations, and seeds
├── scripts/          # Automation, utilities, and live smoke test runners
│   └── smoke_test.py # 8-checkpoint automated live application smoke test
├── docs/             # Architecture Decision Records (ADRs) & governance ledgers
│   ├── IMPLEMENTATION_ROADMAP.md # Multi-phase execution roadmap
│   ├── PHASE_STATUS.md           # Phase progression & verification status
│   ├── ARCHITECTURE_DECISIONS.md # Locked ADR-001 through ADR-008
│   ├── COMMIT_LEDGER.md          # 500-commit budget ledger & tracking
│   └── SIGN_OFF_REGISTER.md      # Gate check sign-off registry
├── .github/workflows/# Continuous integration pipelines
│   └── backend-ci.yml# Multi-version Python verification workflow
├── frontend/         # Web dashboard (future integration surface; out of scope for MVP)
├── extension/        # Browser extension (Phase 3)
├── mcp/              # Model Context Protocol integrations (future integration surface)
└── benchmark/        # Hallucination benchmark datasets & evaluators (Phase 4)
```

---

## 2. Current Project Status

- **Phase 0 (Repository Baseline & Governance):** **COMPLETE** (Formally approved by Arun; Commit `74324a6`).
- **Phase 1 (Database & Foundation):** **COMPLETE — AWAITING ARUN’S SIGN-OFF**
  - Prompt 1: FastAPI Foundation & Routing (Approved; Commit `3e1c9c1` baseline).
  - Prompt 2: Async PostgreSQL Foundation (Approved; Commit `33ce288`).
  - Prompt 3: Centralized Config, Logging, Errors & ADR-008 (Approved; Commit `f0e8255` & `7a9be18`).
  - Hardening & CI: Standalone smoke test (`scripts/smoke_test.py`), GitHub Actions workflow (`backend-ci.yml`), root documentation alignment.
- **Phase 2 (Backend Core & Verification Engine):** **STRICTLY LOCKED** pending Arun's formal Phase 1 sign-off.

---

## 3. Quickstart & Local Setup

### 3.1 Prerequisites
- Python 3.11, 3.12, or 3.14
- Git

### 3.2 Installation
```bash
# Clone repository and switch to active development branch
git clone https://github.com/Arunprasath-2717/VerifAI.git
cd VerifAI
git checkout Final

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install development dependencies
pip install -r backend/requirements-dev.txt

# Configure environment variables
cp backend/.env.example backend/.env
```

### 3.3 Running the Development Server
```bash
PYTHONPATH=backend .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Interactive documentation:
- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI Schema:** [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## 4. Verification Suite & Quality Assurance

VerifAI enforces a zero-regression, hermetic quality gate:

### 4.1 Execute Test Suite
```bash
PYTHONPATH=backend .venv/bin/pytest backend/tests -v
```

### 4.2 Linting and Formatting
```bash
PYTHONPATH=backend .venv/bin/ruff check backend scripts
PYTHONPATH=backend .venv/bin/ruff format --check backend scripts
```

### 4.3 Static Type Checking
```bash
PYTHONPATH=backend .venv/bin/mypy backend/app
```

### 4.4 Dependency Integrity Check
```bash
.venv/bin/python -m pip check
```

### 4.5 Automated Live Application Smoke Test
```bash
PYTHONPATH=backend .venv/bin/python scripts/smoke_test.py
```

To test against an externally running server:
```bash
PYTHONPATH=backend .venv/bin/python scripts/smoke_test.py --base-url http://127.0.0.1:8000
```

---

## 5. API Contracts & Architecture Standards

### 5.1 Versioned Endpoints Under `/api/v1`
- **Liveness Probe (`GET /api/v1/health`):**
  Returns HTTP 200 with `{status: "live", service: "verifai-backend", version: "0.1.0", request_id: "..."}`.
- **Readiness Probe (`GET /api/v1/ready`):**
  Evaluates dependency health honestly. Returns HTTP 503 until external persistence dependencies are configured.
- **Root `/health`:** Strictly unmounted (returns HTTP 404).

### 5.2 Request & Correlation ID Tracking
- Middleware intercepts every request, validates/sanitizes client-supplied IDs, and assigns a clean UUID4 identifier if absent or malformed.
- Header `X-Request-ID` is guaranteed on **every** HTTP response (including 200, 404, 405, 422, and 500).
- Request ID is automatically bound to `contextvars` and included in all server logs (`[request_id=...]`).

### 5.3 Unified JSON Error Envelope
All errors conform to a strict schema:
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Resource not found",
    "request_id": "c4b82d3f9a7e4...",
    "details": null
  }
}
```

---

## 6. Locked Architectural Boundaries

Per approved Architecture Decision Records (ADR-001 through ADR-008):
- **Verification Authority:** Arun is the single source of verification truth. The backend owns 100% of verification orchestration.
- **Authentication Deferral:** Supabase Auth is deferred to Future Enhancements (ADR-003 Addendum). No custom auth or OTP in initial phases.
- **AI Models:** Local open-source models only (ADR-004), scheduled for Phase 2.
- **Out of Scope for Core MVP:** React dashboard and Model Context Protocol (MCP) are designated as future integration surfaces (ADR-006).
- **Branch Governance:** All active work occurs on `Final`. Pushes to `main` are strictly forbidden until verified release.
