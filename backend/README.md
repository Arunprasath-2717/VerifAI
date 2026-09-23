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
│   │   ├── database.py      # Async SQLAlchemy engine, sessionmaker, probe
│   │   ├── dependencies.py  # Common FastAPI dependency injection providers
│   │   ├── errors.py        # AppError exceptions & standardized error handlers
│   │   ├── logging.py       # Structured logging, contextvar, secret masking
│   │   └── middleware.py    # RequestIDMiddleware & safe request logging
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
│   ├── test_app.py          # App startup, CORS, and OpenAPI tests
│   ├── test_config.py       # Configuration, log level, and env override tests
│   ├── test_database.py     # Engine, session lifecycle, and probe tests
│   ├── test_errors.py       # Standard error contract & sanitization tests
│   ├── test_health.py       # Health/readiness checks and negative controls
│   ├── test_logging.py      # Formatting, secret masking, and deduplication tests
│   └── test_middleware.py   # Request ID generation, propagation, and cleanup
├── .env.example             # Safe environment variable template
├── pyproject.toml           # Project metadata & tool config (pytest, ruff, mypy)
├── requirements.txt         # Pinned production dependencies (SQLAlchemy, asyncpg, etc.)
├── requirements-dev.txt     # Developer & testing dependencies (pytest, ruff, mypy)
└── requirements-lock.txt    # Fully frozen reproducible dependency lockfile
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
- Prompt 2 established the underlying async engine, session lifecycle, and pooling infrastructure.

---

## 7. Structured Logging & Secret Masking (Phase 1, Prompt 3)

### 7.1 Architecture & Setup
Application logging is centrally managed in `app/core/logging.py` using Python's standard-library logging framework:
- **Idempotent Initialization:** Calling `setup_logging(log_level)` removes existing handlers before attaching the custom `StreamHandler`, preventing duplicate log records upon repeated imports or reloads.
- **Consistent Log Format:** Standard format:
  ```
  %(asctime)s [%(levelname)s] [%(name)s] [request_id=%(request_id)s] %(message)s
  ```
  Timestamps are formatted in strict **ISO 8601 UTC** with `Z` suffix (`2026-09-19T14:52:21Z`).
- **Contextual Correlation:** The active request ID is stored in a `contextvars.ContextVar` (`request_id_ctx`) and automatically stamped into every log record emitted during the request lifecycle. Logs emitted outside a request lifecycle default to `[request_id=-]`.

### 7.2 Automated Secret Scrubbing
All log output passes through regex-based scrubbing filters (`mask_secrets`) before console emission:
- **Database Connection Strings:** `postgresql+asyncpg://user:password@host/db` is automatically redacted to `postgresql+asyncpg://user:***@host/db`.
- **Authorization Tokens:** `Bearer <token>` and `Basic <token>` are scrubbed to `Bearer [REDACTED]`.
- **Credential Key-Values:** Sensitive assignments such as `password=...`, `token=...`, `api_key=...` are masked with `***`.

---

## 8. Request & Correlation Tracking Middleware (Phase 1, Prompt 3)

### 8.1 Middleware Lifecycle
The `RequestIDMiddleware` (`app/core/middleware.py`) is implemented as a pure ASGI middleware:
1. **Header Inspection:** Checks the incoming HTTP request for the configured header (default `X-Request-ID`).
2. **Strict Sanitization:** Validates client-supplied IDs against alphanumeric, dashes, and underscores (max 64 chars). Any ID containing whitespace, newlines, control characters, or excessive length is rejected and replaced with a clean `uuid.uuid4().hex`.
3. **Context Binding:** Binds the sanitized request ID to both `request_id_ctx` (for logging) and `request.state.request_id` (for route access).
4. **Header Injection:** Intercepts `http.response.start` to guarantee that `X-Request-ID` is present on **every HTTP response** (including 200, 404, 405, 422, and 500 responses).
5. **Safe Access Logging:** Emits structured start and completion logs recording HTTP method, path, status, and duration in milliseconds without logging sensitive headers or request bodies.
6. **Guaranteed Cleanup:** Automatically resets the `ContextVar` in a `finally` block to prevent correlation leakage across async execution contexts.

---

## 9. Standardized API Error Contract (Phase 1, Prompt 3)

### 9.1 Unified JSON Error Envelope
All application errors, HTTP exceptions, validation errors, and unexpected server failures return a uniform JSON envelope:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable explanation.",
    "request_id": "c4b82d3f9a7e4...",
    "details": null
  }
}
```

### 9.2 Error Categories & Handlers
- **Application Errors (`AppError`):** Base exception for operational errors (`NotFoundError`, `BadRequestError`, `ServiceUnavailableError`).
- **HTTP Exceptions (`StarletteHTTPException`):** Maps HTTP status codes to stable string codes (`400: BAD_REQUEST`, `404: NOT_FOUND`, `405: METHOD_NOT_ALLOWED`, `503: SERVICE_UNAVAILABLE`).
- **Validation Errors (`RequestValidationError`):** Returns HTTP 422 with code `VALIDATION_ERROR`. Field errors are sanitized to include `location`, `message`, and `type`, while **omitting raw input values** to prevent credential reflection.
- **Unhandled Exceptions (`Exception`):** Returns HTTP 500 with code `INTERNAL_SERVER_ERROR` and a safe generic message (`"An unexpected internal error occurred."`). Full tracebacks are logged server-side with request correlation and secret masking, but are **never exposed to clients**.

---

## 10. Supported Configuration Variables Reference

| Variable | Type | Default | Description |
|---|---|---|---|
| `PROJECT_NAME` | `str` | `"VerifAI"` | Application display name |
| `VERSION` | `str` | `"0.1.0"` | Application semantic version |
| `API_V1_STR` | `str` | `"/api/v1"` | API v1 route prefix |
| `ENVIRONMENT` | `str` | `"development"` | Options: `development`, `test`, `testing`, `staging`, `production` |
| `DEBUG` | `bool` | `false` | Enable FastAPI debug mode |
| `LOG_LEVEL` | `str` | `"INFO"` | Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `HOST` | `str` | `"127.0.0.1"` | Bind host |
| `PORT` | `int` | `8000` | Bind port |
| `REQUEST_ID_HEADER` | `str` | `"X-Request-ID"` | Request/correlation ID header name |
| `BACKEND_CORS_ORIGINS` | `list[str]` | `["http://localhost:3000", ...]` | Allowed CORS origins |
| `DATABASE_URL` | `SecretStr` | `None` | Asynchronous PostgreSQL connection string |
| `DATABASE_POOL_SIZE` | `int` | `5` | SQLAlchemy connection pool size |
| `DATABASE_MAX_OVERFLOW` | `int` | `10` | SQLAlchemy maximum overflow connections |
| `DATABASE_POOL_TIMEOUT` | `int` | `30` | Seconds to wait before timing out pool checkout |
| `DATABASE_CONNECT_TIMEOUT` | `float` | `3.0` | Socket connection timeout in seconds |

---

## 11. Scope Boundaries — What is Intentionally NOT Implemented in Phase 1 Prompt 3

To maintain strict compliance with project governance:
- **Domain Tables & Migrations:** No verification, job, or domain tables; Alembic migrations deferred to future prompts.
- **Authentication:** Supabase Auth JWT verification remains deferred to Future Enhancements.
- **pgvector Implementation:** The `pgvector` extension is a future prerequisite for Phase 4 knowledge-base ingestion.
- **Verification Engine & AI Models:** No claim extraction, LLM judge execution, or hallucination risk scoring.
- **External Logging Services:** No external logging platforms (Datadog, Sentry, ELK); standard-library logging only.
- **Frontend / Extension / MCP:** Strictly isolated from backend infrastructure.

