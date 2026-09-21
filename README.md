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
│   ├── app/          # Application package (core, api/v1, modules, models, schemas)
│   ├── tests/        # Deterministic hermetic test suite (959 unit, integration & matrix tests)
│   ├── pyproject.toml# Tooling configuration (pytest, ruff, mypy)
│   ├── requirements.txt      # Pinned production dependencies
│   ├── requirements-dev.txt  # Development & test tooling dependencies
│   └── requirements-lock.txt # Frozen reproducible dependency lockfile
├── database/         # Supabase PostgreSQL schema, migrations, and seeds
├── scripts/          # Automation, utilities, and live smoke test runners
│   ├── verify.py     # Standalone CLI demonstration and verification runner
│   └── smoke_test.py # 8-checkpoint automated live application smoke test
├── extension/        # Chrome Manifest V3 browser extension (Phase 4)
│   ├── manifest.json # MV3 permissions, host matching, and action declaration
│   ├── content.js    # Multi-LLM DOM auto-detection (ChatGPT, Claude, Gemini, DeepSeek)
│   ├── background.js # Service worker and context menu verification relay
│   ├── popup.html    # Glassmorphism extension popup interface
│   ├── popup.css     # Design tokens, animations, and responsive popup layout
│   └── popup.js      # Backend communication, health polling, and verification rendering
├── docs/             # Architecture Decision Records (ADRs) & governance ledgers
│   ├── IMPLEMENTATION_ROADMAP.md # Multi-phase execution roadmap
│   ├── PHASE_STATUS.md           # Phase progression & verification status
│   ├── ARCHITECTURE_DECISIONS.md # Locked ADR-001 through ADR-010
│   ├── COMMIT_LEDGER.md          # 500-commit budget ledger & tracking
│   └── SIGN_OFF_REGISTER.md      # Gate check sign-off registry
├── .github/workflows/# Continuous integration pipelines
│   └── backend-ci.yml# Multi-version Python verification workflow
├── frontend/         # Web dashboard (future integration surface; out of scope for MVP)
├── mcp/              # Model Context Protocol integrations (future integration surface)
└── benchmark/        # Hallucination benchmark datasets & evaluators (Phase 2)
```

---

## 2. Current Project Status

- **Phase 0 (Repository Baseline & Governance):** **COMPLETE** (Formally approved by Arun; Commit `74324a6`).
- **Phase 1 (Database & Auth Foundation):** **COMPLETE — AWAITING ARUN'S SIGN-OFF**
- **Phase 2 (Benchmark Dataset & Quality Gate):** **IMPLEMENTATION COMPLETE — AWAITING ARUN'S SIGN-OFF**
- **Phase 3 (Backend Core & Verification Engine):** **APPROVED & SIGNED OFF BY ARUN** (Commit `8de897d`).
- **Phase 4 (Ingestion & Browser Extension):** **IMPLEMENTATION COMPLETE — AWAITING ARUN'S SIGN-OFF**
  - Payload Ingestion API (`POST /api/v1/ingest`, `GET /api/v1/ingest/{id}`) with SSRF perimeter.
  - Manifest V3 Chrome Extension with DOM auto-detection and dark glassmorphism popup.
  - 1,020 hermetic automated tests (100% passing across backend and benchmark suites).
- **Phase 5 (Hardening, Integration & Delivery):** **LOCKED** pending Phase 4 formal sign-off.

---

## 3. Quickstart & Local Setup

### 3.1 Prerequisites
- Python 3.11, 3.12, or 3.14
- Git
- Google Chrome or Chromium-based browser (for extension)

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

### 3.4 CLI Verification Demonstration Tool
Test the verification pipeline directly from the command line:
```bash
# Verify a factual statement
.venv/bin/python scripts/verify.py --text "Water has the chemical formula H2O."

# Output structured JSON
.venv/bin/python scripts/verify.py --text "Apollo 11 landed on the moon in 1969." --json
```

### 3.5 Chrome Extension Installation
1. Open Chrome / Chromium and navigate to `chrome://extensions/`.
2. Enable **Developer mode** toggle in top-right corner.
3. Click **Load unpacked** and select the `extension/` directory from this repository.
4. Pin the **VerifAI** icon to your toolbar.
5. Open any LLM interface (ChatGPT, Claude, Gemini, DeepSeek, Perplexity) and click the extension icon to verify responses.

---

## 4. Verification Suite & Quality Assurance

VerifAI enforces a zero-regression, hermetic quality gate:

### 4.1 Execute Test Suite (1,020 Tests)
```bash
.venv/bin/pytest -v
```

### 4.2 Linting and Formatting
```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
```

### 4.3 Static Type Checking
```bash
.venv/bin/mypy backend/app backend/tests
```

### 4.4 Automated Live Application Smoke Test
```bash
.venv/bin/python scripts/smoke_test.py
```

---

## 5. API Contracts & Architecture Standards

### 5.1 Versioned Endpoints Under `/api/v1`
- **Liveness Probe (`GET /api/v1/health`):**
  Returns HTTP 200 with `{status: "live", service: "verifai-backend", version: "0.1.0", request_id: "..."}`.
- **Readiness Probe (`GET /api/v1/ready`):**
  Evaluates dependency health honestly. Returns HTTP 503 until external persistence dependencies are configured.
- **Payload Ingestion (`POST /api/v1/ingest`):**
  Ingests AI-generated text, enforces SSRF boundaries, stores payload in PostgreSQL, and optionally triggers immediate verification.
- **Ingestion Query (`GET /api/v1/ingest/{id}`):**
  Retrieves previously ingested payload record by UUID.
- **Claim Verification (`POST /api/v1/verification`):**
  Executes end-to-end claim extraction, evidence retrieval, multi-judge evaluation, and trust score calculation.
- **Verification Result (`GET /api/v1/verification/{id}`):**
  Retrieves completed verification job and full audit trail by UUID.

### 5.2 Unified JSON Error Envelope
All errors conform to RFC-7807 compliant structure:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "source_url must use http or https scheme.",
    "request_id": "c4b82d3f9a7e4...",
    "details": null
  }
}
```

---

## 6. Locked Architectural Boundaries

Per approved Architecture Decision Records (ADR-001 through ADR-010):
- **Verification Authority:** Arun is the single source of verification truth. The backend owns 100% of verification orchestration.
- **Authentication Deferral:** Supabase Auth is deferred to Future Enhancements (ADR-003 Addendum).
- **AI Models:** Local open-source models only (ADR-004).
- **SSRF Defense:** Strict pre-persistence validation of client-submitted URLs (ADR-010).
- **Out of Scope for Core MVP:** React dashboard and Model Context Protocol (MCP) are designated as future integration surfaces (ADR-006).
- **Branch Governance:** All active work occurs on `Final`. Pushes to `main` are strictly forbidden until verified release.
