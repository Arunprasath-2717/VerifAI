# VerifAI — Cross-Generation Consistency Hallucination Risk Analysis

[![Backend CI & Hermetic Verification](https://github.com/Arunprasath-2717/VerifAI/actions/workflows/backend-ci.yml/badge.svg?branch=Final)](https://github.com/Arunprasath-2717/VerifAI/actions/workflows/backend-ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)](https://www.sqlalchemy.org/)
[![License](https://img.shields.io/badge/License-Proprietary-gray.svg)]()

VerifAI is an intelligent verification and evaluation system engineered to detect, quantify, and mitigate cross-generation consistency hallucinations in large language model (LLM) workflows.

---

## 1. System Overview & Architecture

VerifAI is designed as a high-throughput **Modular Monolith** powered by **Python and FastAPI**, backed by **PostgreSQL 16** via asynchronous SQLAlchemy 2.x and `asyncpg`.

```
VerifAI/
├── backend/          # Core FastAPI modular monolith & async persistence
│   ├── app/          # Application package (core, api/v1, modules, models, schemas)
│   ├── tests/        # Deterministic hermetic test suite (1,164+ unit, integration & matrix tests)
│   ├── pyproject.toml# Tooling configuration (pytest, ruff, mypy)
│   ├── requirements.txt      # Pinned production dependencies
│   ├── requirements-dev.txt  # Development & test tooling dependencies
│   └── requirements-lock.txt # Frozen reproducible dependency lockfile
├── database/         # PostgreSQL schema, migrations, and seeds
├── scripts/          # Automation, utilities, and live smoke test runners
│   ├── smoke_test.py # 8-checkpoint automated live application smoke test
│   └── demo_verification.py # Live verification runner for API scenarios
├── extension/        # Chrome Manifest V3 browser extension (Secondary client)
│   ├── manifest.json # MV3 permissions, host matching, and action declaration
│   ├── content.js    # Multi-LLM DOM auto-detection (ChatGPT, Claude, Gemini, DeepSeek)
│   ├── background.js # Service worker and context menu verification relay
│   ├── popup.html    # Glassmorphism extension popup interface
│   ├── popup.css     # Design tokens, animations, and responsive popup layout
│   └── popup.js      # Backend communication, health polling, and verification rendering
├── docs/             # Technical architecture guides & Architecture Decision Records (ADRs)
│   ├── ARCHITECTURE_DECISIONS.md # Locked ADR-001 through ADR-011
│   ├── FRONTEND_BACKEND_CONTRACT.md # Contract specification for Web Dashboard
│   ├── VERIFAI_COMPLETE_TECHNICAL_GUIDE.md # Exhaustive technical architecture guide
│   └── API_SECURITY_MATRIX.md   # Security, rate limit, and auth governance matrix
├── .github/workflows/# Continuous integration pipelines
│   └── backend-ci.yml# Multi-version Python verification workflow
├── frontend/         # Web dashboard (Primary user-facing client)
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
  - Namespace-isolated Private Knowledge Base (KB) evidence provider with deterministic token overlap retrieval.
  - 1,149 hermetic automated tests (100% passing across backend, benchmark, and KB suites).
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

### 3.4 Knowledge Base REST API Endpoints
- `POST /api/v1/knowledge/documents` — Ingest document into owner namespace (validates format, limits, content hash).
- `GET /api/v1/knowledge/documents` — List documents strictly isolated to requested owner namespace.
- `GET /api/v1/knowledge/documents/{id}` — Retrieve document details and constituent text chunks.
- `DELETE /api/v1/knowledge/documents/{id}` — Delete document and cascade delete all its chunks.
- `POST /api/v1/knowledge/search` — Scored search across owner namespace chunks.

## 4. Product Interfaces & Client Architecture

VerifAI is structured around an authentic client-server separation where the backend and verification engine serve as the single source of truth:

```text
AUTHENTIC WEB DASHBOARD (Primary Client)
        │
        ▼ (REST API & Real SSE Lifecycle)
   FASTAPI API (Modular Monolith)
        │
        ▼ (Pipeline Execution & Consensus Arbitration)
VERIFICATION ENGINE
```

### 4.1 Client Surface Taxonomy
- **PRIMARY:** **Web Dashboard** (`frontend/`) — The primary user-facing client interface consuming the FastAPI REST endpoints and truthful SSE verification lifecycle streaming.
- **SECONDARY:** **Chrome Extension** (`extension/`) — Browser companion extension for in-situ verification of LLM responses across web chat interfaces.
- **FUTURE / OUT OF SCOPE:** Terminal CLI and Model Context Protocol (MCP) integrations.

### 4.2 Chrome Extension Setup
1. Open Chrome / Chromium and navigate to `chrome://extensions/`.
2. Enable the **Developer mode** toggle in the top-right corner.
3. Click **Load unpacked** and select the `extension/` directory from this repository.
4. Pin the **VerifAI** icon to your toolbar.
5. Open any LLM interface (ChatGPT, Claude, Gemini, DeepSeek, Perplexity) and click the extension icon to verify responses against the running backend (`http://127.0.0.1:8000`).

---

## 5. Verification Suite & Quality Assurance

VerifAI enforces a zero-regression, hermetic quality gate:

### 5.1 Execute Test Suite (1,164 Tests)
```bash
.venv/bin/pytest -v
```

### 5.2 Linting and Formatting
```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
```

### 5.3 Static Type Checking
```bash
.venv/bin/mypy backend/app
```

### 5.4 Automated Live Application Smoke Test
```bash
.venv/bin/python scripts/smoke_test.py
```

### 5.5 End-to-End API Demonstration Runner
```bash
.venv/bin/python scripts/demo_verification.py
```

---

## 6. API Contracts & Architecture Standards

### 6.1 Versioned Endpoints Under `/api/v1`
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
- **Real-Time Streaming Lifecycle (`POST /api/v1/chat/conversations/{id}/messages/stream`):**
  Streams genuine Server-Sent Events (SSE) for conversation lifecycle milestones and pipeline progression.

### 6.2 Unified JSON Error Envelope
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

## 7. Product Client & Architectural Boundaries

Per approved Architecture Decision Records (ADR-001 through ADR-011):
- **Client Architecture:** Web Dashboard is the primary product surface; Chrome Extension is the active secondary companion; CLI is deprecated and out of scope.
- **Verification Engine Invariant:** All truth evaluations, claim classifications, evidence retrievals, and trust calibrations occur strictly server-side in the verification engine. No client-side mock results, fake timers, or fabricated trust scores are permitted.
- **Authentication:** Unified JWT and Firebase Auth token verification with local PostgreSQL user auto-provisioning.
- **SSRF Defense:** Strict pre-persistence validation of client-submitted URLs via `is_safe_url`.
- **Branch Governance:** All active work occurs on `Final`. Pushes to `main` are strictly forbidden until verified release.
