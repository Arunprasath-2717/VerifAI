# VerifAI Backend — Phase 0 & Phase 1: Foundation, Database & Authentication

Welcome to the backend service for **VerifAI — AI Claim Verification & Trust-Scoring System**.

This service is built with **Python** and **FastAPI**. It provides a clean, asynchronous, modular, and free-tier friendly backend with authoritative user authentication powered by **Supabase Auth** and PostgreSQL/asyncpg. The authentication subsystem is unified for shared use across the **Web UI**, **Browser Extension**, and **Model Context Protocol (MCP)** clients.

---

## 1. Architectural Principles

- **Framework**: FastAPI (async ASGI framework using Starlette and Pydantic v2).
- **Single Backend**: One unified FastAPI backend serves all clients (Web, Extension, MCP).
- **Authentication**: Delegated to **Supabase Auth** via its GoTrue REST API using `httpx.AsyncClient`. Zero custom password hashing or secondary JWT systems.
- **Application Database**: PostgreSQL with asynchronous connection pooling via `asyncpg`. Application-level `users` table maps 1-to-1 to Supabase Auth UID.
- **Resilience**: Non-fatal startup if database is unreachable during local development. Strict fail-fast safeguards in `production` mode validating remote database URLs and Supabase credentials.
- **Observability**: In-process metrics collector (uptime, request counts, response time percentiles p50/p95, error rates) without heavy external monitoring services.
- **Standardized API Contracts**: Uniform envelopes for both success (`StandardResponse[T]`) and error (`ErrorResponse`) responses.

---

## 2. Directory Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                     # ASGI entrypoint (uvicorn app.main:app)
│   ├── factory.py                  # Application factory (create_app) with lifespan hooks
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py         # Reusable auth dependencies (get_current_user)
│   │   ├── health.py               # Root GET /health liveness probe
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py           # v1 router aggregating all modular sub-routers
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── auth.py         # Phase 1: Register, Login, Logout, Me, Refresh
│   │           ├── health.py       # GET /api/v1/health
│   │           ├── ready.py        # GET /api/v1/ready
│   │           ├── metrics.py      # GET /api/v1/metrics
│   │           └── test_echo.py    # POST /api/v1/test-validation (422 test helper)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py               # Pydantic Settings with env parsing and production guards
│   │   ├── database.py             # asyncpg connection pool manager & health check
│   │   ├── errors.py               # Global exception handlers (404, 409, 422, 500, AppError)
│   │   ├── logging.py              # Structured logging configuration
│   │   ├── metrics.py              # In-process metrics tracking (p50, p95, status codes)
│   │   └── middleware.py           # Security headers, Request ID, and timing middleware
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── user_repository.py      # CRUD database operations on public.users
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py                 # Register, Login, UserResponse, AuthTokens schemas
│   │   ├── common.py               # StandardResponse, ErrorResponse, ErrorDetails
│   │   ├── health.py               # SystemHealthData, ReadinessData schemas
│   │   └── metrics.py              # MetricsData, TimingMetrics schemas
│   └── services/
│       ├── __init__.py
│       └── supabase_auth.py        # Supabase GoTrue API async client & error mapping
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures & AsyncClient setup
│   ├── test_auth.py                # Phase 1: 18 authentication scenarios & Supabase tests
│   ├── test_config.py              # Settings validation & production safeguard tests
│   ├── test_database.py            # Database manager, connection retry & pool tests
│   ├── test_errors.py              # Exception handler & 422 validation tests
│   ├── test_factory.py             # App factory & route registration tests
│   ├── test_health.py              # GET /health, /api/v1/health, /api/v1/ready tests
│   ├── test_metrics.py             # In-process metrics tracking & percentile tests
│   ├── test_middleware.py          # Security headers, request ID & timing tests
│   ├── test_performance.py         # Latency benchmarks (p95 < 200ms)
│   ├── test_shutdown.py            # SIGINT & SIGTERM graceful shutdown tests
│   └── test_user_repo.py           # UserRepository CRUD unit tests
├── .env.example                    # Environment variable configuration template
├── pyproject.toml                  # Pytest & coverage configuration
├── requirements.txt                # Pinned dependencies
└── README.md                       # Backend documentation
```

---

## 3. Getting Started

### 3.1 Prerequisites

- Python 3.10+ (tested through Python 3.14)
- Git

### 3.2 Virtual Environment Setup

From the `backend/` directory:

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows (cmd/powershell):
# .venv\Scripts\activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.3 Environment Configuration

Copy the sample environment file to `.env`:

```bash
cp .env.example .env
```

Key environment variables:

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `ENVIRONMENT` | Runtime mode: `development`, `testing`, `production` | `development` |
| `DEBUG` | FastAPI debug mode flag (must be `false` in production) | `true` |
| `PORT` | Local server port | `8000` |
| `HOST` | Bind host address | `0.0.0.0` |
| `DATABASE_URL` | PostgreSQL/Supabase connection string | `postgresql://postgres:postgres@localhost:5432/verifai` |
| `SUPABASE_URL` | Supabase project URL | `https://your-project.supabase.co` |
| `SUPABASE_ANON_KEY` | Public Supabase anon key | `your-supabase-anon-key` |
| `SUPABASE_SERVICE_ROLE_KEY` | Server-only Supabase service-role secret | `your-supabase-service-role-key` |
| `CORS_ORIGINS` | Comma-separated list of allowed CORS origins | `http://localhost:3000,http://localhost:5173` |
| `LOG_LEVEL` | Logging verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` |

---

## 4. Running the Application

### Development Server

Run with automatic reload enabled:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Once running:
- **Interactive Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI JSON**: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## 5. API Endpoints

### 5.1 Authentication Endpoints (`/api/v1/auth`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Register identity in Supabase & sync to application `users` table | No |
| `POST` | `/api/v1/auth/login` | Authenticate with email/password and obtain session tokens | No |
| `POST` | `/api/v1/auth/logout` | Revoke active user session in Supabase Auth | Yes (`Bearer <token>`) |
| `GET` | `/api/v1/auth/me` | Fetch authenticated user profile | Yes (`Bearer <token>`) |
| `PATCH` | `/api/v1/auth/me` | Update user profile (`display_name`) | Yes (`Bearer <token>`) |
| `DELETE` | `/api/v1/auth/me` | Permanently delete profile and Supabase Auth identity | Yes (`Bearer <token>`) |
| `POST` | `/api/v1/auth/refresh` | Exchange refresh token for new access token | No |

#### Registration Example (`POST /api/v1/auth/register`)
Request body:
```json
{
  "email": "analyst@verifai.app",
  "password": "SecurePassword123!",
  "display_name": "Arun Prasath"
}
```
Response (`201 Created`):
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "11111111-2222-3333-4444-555555555555",
      "email": "analyst@verifai.app",
      "display_name": "Arun Prasath",
      "created_at": "2026-09-09T09:00:00Z",
      "updated_at": "2026-09-09T09:00:00Z"
    },
    "session": {
      "access_token": "eyJhbGciOiJIUzI1NiIs...",
      "refresh_token": "d8f8a1...",
      "token_type": "bearer",
      "expires_in": 3600
    }
  },
  "meta": null
}
```

### 5.2 System & Health Endpoints
- `GET /health` — Lightweight root liveness probe (`{"success": true, "data": {"status": "healthy"}}`).
- `GET /api/v1/health` — System and database connection status (`200 OK` or `503 Service Unavailable`).
- `GET /api/v1/ready` — Traffic readiness check.
- `GET /api/v1/metrics` — In-process latency percentiles (p50, p95), requests by endpoint, error rates.

---

## 6. Reusable Authentication Dependency (For Future Modules)

Any protected endpoint across future phases (Claims, Evidence, Verifications, Reports, Chat, MCP) simply injects `get_current_user`:

```python
from fastapi import APIRouter, Depends
from app.api.dependencies import get_current_user
from app.schemas.auth import UserResponse

router = APIRouter()

@router.get("/my-verifications")
async def get_user_verifications(
    current_user: UserResponse = Depends(get_current_user),
):
    # current_user.id is the verified Supabase UUID
    return {"user_id": current_user.id, "email": current_user.email}
```

---

## 7. Testing & Quality Assurance

The test suite runs with `pytest` and `pytest-asyncio`.

### Running All Tests

```bash
pytest -v
```

### Running with Code Coverage

```bash
pytest --cov=app --cov-report=term-missing --cov-report=html
```

The test suite runs **85 tests** across 12 test suites maintaining **97% overall code coverage** (with 100% coverage on dependencies, health, ready, metrics, and middleware).

### Running Latency Benchmark

```bash
pytest tests/test_performance.py -v -s
```
Result: `p95 < 1.00ms` (far below the `< 200ms` threshold).
