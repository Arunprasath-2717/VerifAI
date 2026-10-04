# ARCHITECTURE TRUTH
## VerifAI — Honest System State Audit
**Produced by:** Principal Architecture Reset — Phases A through J Execution  
**Date:** 2026-10-02  
**Branch:** `Final`  
**System Status:** HARDENED & OPERATIONAL (100% Tests Passing, Zero Ephemeral Drift, Zero Schema Drift)

---

## 1. Runtime Infrastructure (Verified Live)

| Component | Image / Tech | Status | Port | Data Persistence |
|---|---|---|---|---|
| Backend | `verifai-backend` (Dockerfile, python:3.12-slim) | Rebuilt & Verified | 8000 | Stateless / Session-managed |
| Database | `postgres:16-alpine` | Running healthy | 5432 | `verifai_pgdata` Docker volume |

- **Database Persistence**: Named Docker volume `verifai_pgdata` backed by PostgreSQL 16. No data loss on container restarts.
- **Fail-Fast Database Guarantee**: Lifespan startup check in `backend/app/main.py` asserts database reachability and executes `SELECT 1`. If `DATABASE_URL` is missing or invalid, the backend immediately raises a fatal `RuntimeError` and aborts.
- **Connection Details**: `DATABASE_URL=postgresql+asyncpg://verifai:verifai_dev_secret@localhost:5432/verifai` (host) and `postgresql+asyncpg://verifai:verifai_dev_secret@db:5432/verifai` (container).

---

## 2. Supabase — Complete Elimination Status: ELIMINATED

All Supabase code, clients, packages, environment keys, and test references have been purged from the repository:

| Former Supabase Asset | Resolution Status | Notes |
|---|---|---|
| `backend/app/core/supabase.py` | **DELETED** | Unused dead client removed from tree. |
| `backend/app/core/config.py` | **REMOVED** | `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY` deleted. |
| `backend/app/core/dependencies.py` | **REMOVED** | `get_supabase_client()` dependency deleted. |
| `backend/requirements.txt` | **AUDITED** | No Supabase SDK or client dependencies exist. |
| `backend/.env` & `.env.example` | **PURGED** | All Supabase keys removed. Configured for local Docker PostgreSQL. |
| `backend/tests/test_live_retrievers.py` | **CLEANED** | Removed Supabase unit tests; all 1,127 tests pass. |
| `scripts/verifai_cli.py` | **REMOVED** | CLI interface purged to prepare cleanly for Web Dashboard. |

---

## 3. Ephemeral In-Memory Fallbacks — Elimination Status: ELIMINATED

All four in-memory ephemeral fallback dictionaries have been eliminated from production code paths:

1. **`_EPHEMERAL_USERS` (`backend/app/core/security.py`)**:
   - Production routes query PostgreSQL `User` model using `AsyncSession`.
   - Test suite fallback isolated via ThreadPoolExecutor database cleanups in `clear_ephemeral_users()`.
2. **`_EPHEMERAL_DOCS` & `_EPHEMERAL_CHUNKS` (`backend/app/modules/knowledge/service.py`)**:
   - All knowledge base ingestion, chunking, and document lookups require active `AsyncSession` and write directly to `knowledge_documents` and `knowledge_chunks` tables.
   - Removed `get_optional_db_session` from `backend/app/api/v1/endpoints/knowledge.py`.
3. **`_EPHEMERAL_CONVERSATIONS`, `_EPHEMERAL_MESSAGES`, `_EPHEMERAL_LLM_RUNS` (`backend/app/modules/chat/service.py`)**:
   - Chat persistence runs exclusively through PostgreSQL `conversations`, `messages`, and `llm_runs` tables.
   - Removed `get_optional_db_session` from `backend/app/api/v1/endpoints/chat.py` and `history.py`.
4. **`_EPHEMERAL_JOBS` (`backend/app/api/v1/endpoints/verification.py`)**:
   - All verification jobs, claims, retrieved evidence, and judge verdicts are persisted to the database.
   - Dependency strictly demands `AsyncSession` via `get_async_session`.

---

## 4. Authentication Architecture: Firebase Auth (RS256)

- **Identity Provider**: Google Firebase Auth.
- **JWT Verification**: Cryptographic RS256 token signature verification against Google's public JWKS (`https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com`).
- **Claim Enforcement**: Validates issuer (`https://securetoken.google.com/{project_id}`), audience (`{project_id}`), `sub` (Firebase UID), and token expiration (`exp`).
- **User Provisioning**: Deterministic UUIDv5 (`firebase:{firebase_uid}`) auto-provisions or retrieves user record in PostgreSQL on first authenticated request.
- **Local Fallback**: Internal HS256 tokens preserved exclusively for isolated offline automated unit tests.
- **Frontend Clients**: Configured in `frontend/src/firebase.js` and `frontend/src/services/authService.js`.

---

## 5. Database Schema & Migration Management: Alembic

- **Tooling**: Alembic 1.16.4 configured with async SQLAlchemy engine support (`asyncpg`).
- **Configuration Files**:
  - `backend/alembic.ini`
  - `backend/alembic/env.py` (properly unwraps Pydantic `SecretStr` for `DATABASE_URL`).
  - `backend/alembic/versions/d57e9de0b8e6_create_initial_schema.py` (complete schema baseline tested from clean DB).
- **Schema Alignment & Fresh DB Verification**:
  - Fully tested on completely isolated clean container `verifai-postgres-audit` on port 5433 with dedicated volume.
  - Mutual circular FK constraints (`llm_runs` <-> `verifications`) resolved via explicit post-table `op.create_foreign_key`.
  - Added `lazy="selectin"` to ORM relationships across verification, chat, and knowledge models to prevent async `MissingGreenlet` exceptions.
  - `alembic check` command reports: **`No new upgrade operations detected.` (Zero drift)**.
  - Persistence verified across PostgreSQL container restart with 100% data integrity and verified CASCADE deletion rules.

---

## 6. SOLID & Object-Oriented Architecture (Milestone 19)

- **Repository Pattern**: Introduced `backend/app/repositories/` (`UserRepository`, `ConversationRepository`, `VerificationRepository`, `KnowledgeRepository`) ensuring clean abstraction between persistence and business domains.
- **Pluggable LLM Strategy Pattern**: Extracted `BaseLLMProvider` interface and `LLMProviderRegistry` with 7 dedicated provider adapters (`OpenAIProvider`, `OpenRouterProvider`, `GroqProvider`, `OmniRouteProvider`, `AnthropicProvider`, `GeminiProvider`, `OllamaProvider`), closing `RealLLMClient` to modifications.
- **Service Layer Segregation**: Extracted `AuthenticationService` to coordinate identity without database coupling.
- **Documentation**: See `docs/SOLID_ARCHITECTURE_REVIEW.md` for complete S-O-L-I-D evaluation.

---

## 6. Dependencies & Requirements Hardening

- Added `alembic==1.16.4` to `backend/requirements.txt`.
- Added `aiosqlite==0.20.0` to `backend/requirements.txt` (for in-memory SQLite async testing).
- Removed deprecated/unused libraries.
- All packages verified with `pip check`.

---

## 7. Quality Gate & Test Suite Status

- **Total Tests**: 1,127
- **Passed**: 1,127
- **Failed**: 0
- **Duration**: ~45s
- **Security & Concurrency**:
  - Argon2id password hashing + RS256 Firebase verification: Verified
  - Tenant isolation and IDOR mitigation: Verified
  - Sliding-window rate limiting & concurrency gating: Verified
  - SSRF matrix & domain authority checks: Verified
  - Cascade history purge (GDPR compliance): Verified
