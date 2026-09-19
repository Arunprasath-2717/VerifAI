# VerifAI Backend — Foundation & Development Environment

## 1. Overview & Purpose

The `backend/` directory houses the core API services, verification orchestration engine, and persistence logic for the **VerifAI** system, structured as a **Modular Monolith** using **Python + FastAPI**.

---

## 2. Directory Architecture

```
backend/
├── app/
│   ├── __init__.py          # Backend application package
│   ├── main.py              # FastAPI application factory & lifespan context
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # Environment-driven configuration (pydantic-settings)
│   │   └── dependencies.py  # Common FastAPI dependency injection providers
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py        # Top-level API router mounting versioned paths
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py       # API v1 route aggregator
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           └── health.py # Health and honest readiness probes
│   └── modules/             # Future modular domain modules
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures and TestClient setup
│   ├── test_app.py          # App startup and OpenAPI tests
│   ├── test_config.py       # Configuration and env override tests
│   └── test_health.py       # Health/readiness checks and negative controls
├── .env.example             # Safe environment variable template
├── pyproject.toml           # Project metadata & tool config (pytest, ruff, mypy)
├── requirements.txt         # Minimal production dependencies
└── requirements-dev.txt     # Developer & testing dependencies
```

---

## 3. Local Environment Setup

### 3.1 Create and Activate Virtual Environment

```bash
# From repository root
python3 -m venv .venv
source .venv/bin/activate
```

### 3.2 Install Dependencies

```bash
# Option A: Install from frozen lockfile (Recommended for exact reproducibility)
.venv/bin/pip install -r backend/requirements-lock.txt

# Option B: Install minimal development dependencies
.venv/bin/pip install -r backend/requirements-dev.txt
```

### 3.3 Configure Environment Variables

```bash
# Copy example configuration template
cp backend/.env.example backend/.env
```

---

## 4. Running the Development Server

Start the local Uvicorn development server:

```bash
PYTHONPATH=backend .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Interactive API documentation and OpenAPI schemas are accessible at:
- **Interactive Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc UI:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI Schema (JSON):** [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)
- **Liveness Probe Endpoint:** [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health) (Returns HTTP 200)
- **Readiness Probe Endpoint:** [http://127.0.0.1:8000/api/v1/ready](http://127.0.0.1:8000/api/v1/ready) (Returns HTTP 503 until external dependencies are configured in Phase 1 P2)

---

## 5. Running Tests and Code Quality Tools

### 5.1 Execute Automated Tests
```bash
PYTHONPATH=backend .venv/bin/pytest backend/tests
```

### 5.2 Linting and Formatting Checks
```bash
# Check linting
.venv/bin/ruff check backend

# Check formatting
.venv/bin/ruff format --check backend

# Automatically fix linting and format
.venv/bin/ruff check --fix backend
.venv/bin/ruff format backend
```

### 5.3 Static Type Checking
```bash
PYTHONPATH=backend .venv/bin/mypy backend/app
```

---

## 6. Database Infrastructure & Configuration (Phase 1, Prompt 2)

### 6.1 Database Configuration
Database connectivity is powered by **SQLAlchemy 2.x** and **asyncpg**:
- **Environment Variable:** `DATABASE_URL`
- **Format:** `postgresql+asyncpg://<username>:<password>@<host>:<port>/<database>`
- **Type Safety & Secret Masking:** Parsed as `pydantic.SecretStr` ensuring connection passwords are never leaked in `repr()`, string formatting, logs, or error responses.
- **Local Development Without a Database:** If `DATABASE_URL` is unset or empty, the application starts normally in `unconfigured` mode. Liveness (`/api/v1/health`) returns HTTP 200, while readiness (`/api/v1/ready`) returns HTTP 503 indicating that external persistence dependencies are unconfigured.

### 6.2 Connection Pooling & Lifecycle
- Connection creation is **lazy**: zero connections are attempted during Python module import.
- Engine pooling is conservatively tuned for development (`DATABASE_POOL_SIZE=5`, `DATABASE_MAX_OVERFLOW=10`, `DATABASE_POOL_TIMEOUT=30`).
- The async engine is cleanly disposed upon application shutdown via FastAPI's `lifespan` hook (`dispose_async_engine()`).

### 6.3 Session Management Conventions
- Database sessions are injected using the asynchronous FastAPI dependency `get_async_session`:
  ```python
  from fastapi import Depends
  from sqlalchemy.ext.asyncio import AsyncSession
  from app.core.dependencies import get_async_session


  @router.get("/example")
  async def example_endpoint(db: AsyncSession = Depends(get_async_session)): ...
  ```
- **Transaction Responsibility:** The `get_async_session` dependency guarantees session cleanup in a `finally` block, but **does not auto-commit**. Domain services and repositories are strictly responsible for calling `await session.commit()` or `await session.rollback()`.
- **Test Overrideability:** In tests, the session generator can be mocked or overridden cleanly via `app.dependency_overrides[get_async_session]`.

### 6.4 Schema Migration Status
- Migration tooling (Alembic) is intentionally **deferred** to subsequent prompts where actual domain tables are introduced.
- Prompt 2 focuses strictly on database connectivity, engine lifecycle, pooling, and session infrastructure.

---

## 7. Scope Boundaries — What is Intentionally NOT Implemented in Phase 1 Prompt 2

To maintain strict compliance with project governance:
- **Domain Tables & Schemas:** No verification, user, or application tables are defined yet.
- **Authentication:** Supabase Auth JWT verification remains deferred to Future Enhancements.
- **pgvector Implementation:** The `pgvector` extension is a future prerequisite for Phase 4 knowledge-base ingestion and is not implemented in Prompt 2.
- **Verification Engine & AI Models:** No claim extraction, LLM judge execution, or hallucination risk scoring.
- **Frontend / Extension / MCP:** Strictly isolated from the backend infrastructure.
