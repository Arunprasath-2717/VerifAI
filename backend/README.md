# VerifAI Backend — Phase 0: Foundation & Infrastructure

Welcome to the backend service for **VerifAI — AI Claim Verification & Trust-Scoring System**.

This service is built with **Python** and **FastAPI**. It provides a clean, asynchronous, modular, and free-tier friendly foundation designed for easy onboarding and future feature expansion across upcoming phases (Authentication, Claim Extraction, Evidence Retrieval, Cross-Model Consistency, Chat, and Reporting).

---

## 1. Architectural Principles

- **Framework**: FastAPI (async ASGI framework using Starlette and Pydantic v2).
- **Simplicity**: No Celery, Redis, Docker orchestration, Kubernetes, or microservice bloat.
- **Database Connectivity**: Asynchronous connection pooling with `asyncpg` targeted for PostgreSQL / Supabase.
- **Resilience**: Non-fatal startup if database is unreachable in `development`/`testing` modes. Strict fail-fast enforcement in `production` mode with secure secrets validation.
- **Observability**: In-process metrics collector (uptime, request counts, response time percentiles p50/p95, error rates) without heavy external monitoring services.
- **Standardized API Contracts**: Uniform envelopes for both success and error responses.

---

## 2. Directory Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                     # ASGI entrypoint, lifespan context, router registration
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py           # v1 router aggregating all modular sub-routers
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── health.py       # GET /health, GET /api/v1/health, GET /api/v1/ready
│   │           ├── metrics.py      # GET /api/v1/metrics
│   │           └── test_echo.py    # POST /api/v1/test-validation (422 test helper)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py               # Pydantic Settings with env parsing and production guards
│   │   ├── database.py             # asyncpg connection pool manager & health check
│   │   ├── errors.py               # Global exception handlers (404, 422, 500, AppError)
│   │   ├── logging.py              # Structured logging configuration
│   │   ├── metrics.py              # In-process metrics tracking (p50, p95, status codes)
│   │   └── middleware.py           # Security headers, Request ID, and timing middleware
│   └── schemas/
│       ├── __init__.py
│       ├── common.py               # StandardResponse, StandardErrorResponse, ErrorDetail
│       ├── health.py               # SystemHealthData, ReadinessData schemas
│       └── metrics.py              # MetricsData, TimingMetrics schemas
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures & AsyncClient setup
│   ├── test_config.py              # Settings validation & production safeguard tests
│   ├── test_database.py            # Database manager, connection retry & pool tests
│   ├── test_errors.py              # Exception handler & 422 validation tests
│   ├── test_factory.py             # App factory & route registration tests
│   ├── test_health.py              # GET /health, /api/v1/health, /api/v1/ready tests
│   ├── test_metrics.py             # In-process metrics tracking & percentile tests
│   └── test_middleware.py          # Security headers, request ID & timing tests
├── .env.example                    # Environment variable configuration template
├── pyproject.toml                  # Pytest & coverage configuration
├── requirements.txt                # Pinned dependencies
└── README.md                       # Backend documentation
```

---

## 3. Getting Started

### 3.1 Prerequisites

- Python 3.10, 3.11, 3.12, 3.13, or 3.14
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
| `DEBUG` | FastAPI debug mode flag | `true` |
| `PORT` | Local server port | `8000` |
| `HOST` | Bind host address | `127.0.0.1` |
| `DATABASE_URL` | PostgreSQL/Supabase asyncpg connection string | `postgresql://postgres:postgres@localhost:5432/verifai` |
| `DATABASE_POOL_MIN_SIZE` | Minimum connections in asyncpg pool | `2` |
| `DATABASE_POOL_MAX_SIZE` | Maximum connections in asyncpg pool | `10` |
| `CORS_ORIGINS` | Comma-separated list of allowed CORS origins | `http://localhost:3000,http://localhost:5173` |
| `SECRET_KEY` | JWT/HMAC signing key (must be changed in prod) | `dev-insecure-secret-key-change-in-production-12345` |
| `LOG_LEVEL` | Logging verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` |

---

## 4. Running the Application

### Development Server

Run with automatic reload enabled:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Once running:
- **Root Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **Interactive Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI JSON**: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## 5. API Endpoints

### 5.1 Root Liveness Check
- **Endpoint**: `GET /health`
- **Purpose**: Lightweight, unauthenticated liveness probe for uptime monitors, load balancers, and reverse proxies.
- **Response**:
```json
{
  "success": true,
  "data": {
    "status": "healthy"
  },
  "meta": null
}
```

### 5.2 System & Database Health Check
- **Endpoint**: `GET /api/v1/health`
- **Purpose**: Verifies that both the application process and database pool are reachable and healthy.
- **Healthy Response (`200 OK`)**:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "0.1.0",
    "environment": "development",
    "database": "connected"
  },
  "meta": null
}
```
- **Degraded/Unhealthy Response (`503 Service Unavailable`)**:
```json
{
  "success": false,
  "error": {
    "type": "SERVICE_UNHEALTHY",
    "message": "System health check failed: database is disconnected",
    "details": {
      "status": "unhealthy",
      "version": "0.1.0",
      "environment": "development",
      "database": "disconnected"
    }
  }
}
```

### 5.3 Traffic Readiness Check
- **Endpoint**: `GET /api/v1/ready`
- **Purpose**: Determines whether the backend is ready to accept incoming user traffic. Returns `200` if all readiness probes pass, `503` otherwise.

### 5.4 In-Process Application Metrics
- **Endpoint**: `GET /api/v1/metrics`
- **Purpose**: Lightweight runtime telemetry collected without external daemons.
- **Response Example**:
```json
{
  "success": true,
  "data": {
    "uptime_seconds": 342.15,
    "total_requests": 128,
    "total_errors": 2,
    "active_requests": 1,
    "error_rate_percentage": 1.56,
    "response_timing_ms": {
      "average": 4.12,
      "min": 0.85,
      "max": 42.10,
      "p50": 3.45,
      "p95": 8.90
    },
    "requests_by_method": {
      "GET": 120,
      "POST": 8
    },
    "requests_by_status": {
      "200": 126,
      "422": 2
    },
    "requests_by_endpoint": {
      "/health": 80,
      "/api/v1/health": 40,
      "/api/v1/metrics": 8
    }
  },
  "meta": {
    "type": "in_process_metrics",
    "scope": "application"
  }
}
```

### 5.5 Validation Echo Test
- **Endpoint**: `POST /api/v1/test-validation`
- **Payload Example**: `{"name": "VerifAI", "score": 95.0}`
- **Validation Failure (`422 Unprocessable Entity`)**: Returns clear JSON array of field-level errors:
```json
{
  "success": false,
  "error": {
    "type": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "field": "name",
        "message": "String should have at least 2 characters",
        "type": "string_too_short"
      }
    ]
  }
}
```

---

## 6. Testing & Quality Assurance

The test suite runs with `pytest` and `pytest-asyncio`.

### Running All Tests

```bash
pytest
```

### Running with Code Coverage

```bash
pytest --cov=app --cov-report=term-missing --cov-report=html
```

Coverage is configured to maintain **>90%** coverage across core backend modules.

---

## 7. Adding New Modules (Guide for Teammates)

When implementing future phases (e.g., Auth, Claims, Evidence, Consistency):

1. **Add Route Endpoints**:
   Create `app/api/v1/endpoints/<feature>.py` with an `APIRouter`.
2. **Register Router**:
   Include the router in `app/api/v1/router.py`:
   ```python
   from app.api.v1.endpoints import <feature>
   api_router.include_router(<feature>.router, prefix="/<feature>", tags=["<feature>"])
   ```
3. **Add Data Schemas**:
   Create `app/schemas/<feature>.py` using Pydantic models. Inherit responses from `StandardResponse[T]`.
4. **Database Operations**:
   Access the pool using `database_manager.get_connection()`:
   ```python
   from app.core.database import database_manager

   async with database_manager.get_connection() as conn:
       row = await conn.fetchrow("SELECT ...")
   ```
5. **Add Tests**:
   Create `tests/test_<feature>.py` and test all happy and error paths using the `client` fixture from `tests/conftest.py`.
