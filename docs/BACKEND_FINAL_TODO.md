# VerifAI — Master Backend Completion & Security Plan

> **Tracking Document:** `docs/BACKEND_FINAL_TODO.md`  
> **Active Branch:** `Final`  
> **Status Codes:** `[ ] NOT STARTED` | `[-] IN PROGRESS` | `[x] COMPLETE` | `[!] BLOCKED`  
> **Starting Commit Count:** `89` (total commits across all branches via `git rev-list --count --all`)  
> **Quality Gate Status:** All 6 gates passed (1,181 tests passing, ruff clean, mypy clean, benchmark validate pass, pip check pass)

---

## TODO 1 — REPOSITORY DISCOVERY
- [x] Inspect current Git branch (`Final`).
- [x] Confirm current branch is `Final`.
- [x] Inspect git status (clean working tree).
- [x] Inspect git log (head at `9c9b19e`).
- [x] Inspect all active branches (`main`, `Final`).
- [x] Inspect origin/Final.
- [x] Inspect origin/main.
- [x] Inspect backend structure (`backend/app`).
- [x] Inspect frontend structure.
- [x] Inspect CLI (`scripts/verifai_cli.py`).
- [x] Inspect benchmark (`benchmark/`).
- [x] Inspect database (`backend/app/models/`, `backend/app/core/database.py`).
- [x] Inspect documentation (`docs/`).
- [x] Inspect existing security implementation.
- [x] Inspect existing KB implementation.
- [x] Inspect existing verification pipeline.
- [x] Inspect existing API.
- [x] Inspect existing tests (1,149 tests baseline passing).

---

## TODO 2 — BACKEND FEATURE INVENTORY
- [x] Configuration (`app/core/config.py`)
- [x] FastAPI application (`app/main.py`)
- [x] Middleware (`app/core/middleware.py`)
- [x] Request IDs (`X-Request-ID` middleware & logging context)
- [x] Error handling (`app/core/errors.py`)
- [x] Database (`app/core/database.py` with asyncpg)
- [x] Models (`app/models/user.py`, `app/models/verification.py`, `app/models/knowledge.py`)
- [x] Schemas (`app/schemas/auth.py`, `app/schemas/verification.py`, `app/schemas/knowledge.py`)
- [x] Authentication (`app/api/v1/endpoints/auth.py`, `app/core/security.py`)
- [x] Authorization (`app/core/dependencies.py` with `require_roles`)
- [x] Verification API (`app/api/v1/endpoints/verification.py`)
- [x] Verification orchestrator (`app/modules/verification/orchestrator.py`)
- [x] Claim extraction (`app/modules/claims/extractor.py`)
- [x] Claim classification (`app/modules/claims/classifier.py`)
- [x] Evidence retrieval (`app/modules/evidence/`)
- [x] SSRF (`app/modules/evidence/security.py`)
- [x] Knowledge Base (`app/modules/knowledge/`)
- [x] KB ingestion (`app/modules/knowledge/ingestion.py`)
- [x] KB chunking (`app/modules/knowledge/ingestion.py`)
- [x] KB retrieval (`app/modules/knowledge/retriever.py`)
- [x] KB ownership (Isolated multi-tenant partitions)
- [x] External evidence fallback (`app/modules/evidence/coordinator.py`)
- [x] Evidence provenance (`RetrievedEvidenceItem` metadata)
- [x] Judges (`app/modules/judging/` deterministic, semantic, model)
- [x] Judge disagreement (`app/modules/judging/disagreement.py`)
- [x] Decision engine (`app/modules/judging/decision.py`)
- [x] UNKNOWN handling (Evidence insufficiency yields UNKNOWN)
- [x] Audit (`AuditRecord`)
- [x] Persistence (`SQLAlchemy + asyncpg` + hermetic LRU fallback)
- [x] Rate limiting (`app/core/rate_limit.py`)
- [x] Resource limits (10MB body, 1MB file, 3 concurrent jobs)
- [x] CLI (`scripts/verifai_cli.py`)
- [x] Benchmark (`benchmark/`)
- [x] Tests (`backend/tests/`, `benchmark/tests/` — 1,181 total)
- [x] CI/CD (`.github/workflows/`)
- [x] Deployment configuration (Environment variables, Dockerfile, Alembic)

---

## TODO 3 — AUTHENTICATION
- [x] Inspect existing authentication.
- [x] Implement registration (`POST /api/v1/auth/register`).
- [x] Implement login (`POST /api/v1/auth/login`).
- [x] Implement current-user endpoint (`GET /api/v1/auth/me`).
- [x] Implement secure password hashing with Argon2id (`app/core/security.py`).
- [x] Validate email format.
- [x] Validate username regex (`^[a-zA-Z0-9_-]{3,64}$`).
- [x] Validate password complexity (>=12 chars, upper, lower, digit, symbol).
- [x] Never store plaintext passwords.
- [x] Never log passwords.
- [x] Never return password hashes in responses.

---

## TODO 4 — JWT
- [x] Implement secure JWT authentication (`app/core/security.py`).
- [x] Configuration includes `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_ISSUER`, `JWT_AUDIENCE`, `ACCESS_TOKEN_EXPIRE_MINUTES`.
- [x] Never hard-code JWT secret (defaults to test secret only in test environment; validated in production).
- [x] Validate signature with HMAC-SHA256.
- [x] Validate expiration (`exp`).
- [x] Validate issuer (`iss`).
- [x] Validate audience (`aud`).
- [x] Validate subject (`sub`).
- [x] Reject unsupported algorithms (only `HS256` allowed).
- [x] Never allow client-selected algorithm.
- [x] Do not put sensitive data into JWT payload.

---

## TODO 5 — AUTHORIZATION / RBAC
- [x] Define roles: `USER`, `ANALYST`, `ADMIN`.
- [x] Implement explicit role authorization (`require_roles` dependency).
- [x] Registration defaults to `USER`.
- [x] Prevent client-created ADMIN accounts.
- [x] Prevent privilege escalation.
- [x] Protect admin operations.
- [x] Define ANALYST permissions explicitly.
- [x] Test all role boundaries (`backend/tests/test_auth_security.py`).

---

## TODO 6 — USER OWNERSHIP
- [x] `VerificationJob.owner_id` mapped and indexed in DB model and ephemeral store.
- [x] `KnowledgeDocument.owner_id` mapped and indexed.
- [x] Appropriate ownership for evidence/history/audit resources.
- [x] Authenticate -> identify user -> retrieve resource -> verify ownership -> verify role -> allow/deny.
- [x] Never trust client `owner_id`, random UUID, or frontend state without authenticated verification (`test_ownership_isolation.py`).

---

## TODO 7 — KNOWLEDGE BASE — DEEP IMPLEMENTATION
- [x] Document creation (`POST /api/v1/knowledge/documents`).
- [x] Document validation (extension and magic bytes).
- [x] Filename sanitization (`sanitize_filename`).
- [x] File-size limit (1MB max document bytes).
- [x] Content hashing (SHA-256).
- [x] Duplicate detection within owner namespace.
- [x] Text extraction (UTF-8, plain text, normalized markdown).
- [x] Text normalization.
- [x] Deterministic chunking (500-char chunks, 100-char overlap).
- [x] Chunk overlap.
- [x] Source offsets preserved.
- [x] Document metadata.
- [x] Chunk metadata.
- [x] Owner isolation.
- [x] Document listing (`GET /api/v1/knowledge/documents`).
- [x] Document retrieval (`GET /api/v1/knowledge/documents/{id}`).
- [x] Document deletion (`DELETE /api/v1/knowledge/documents/{id}`).
- [x] KB search (`POST /api/v1/knowledge/query`).
- [x] Retrieval scoring (BM25 + TF-IDF).
- [x] Relevance threshold filtering.
- [x] KB_EMPTY status.
- [x] KB_INSUFFICIENT status.
- [x] KB_RELEVANT status.
- [x] Conversion from KB chunk to `RetrievedEvidenceItem`.
- [x] KB evidence persistence.
- [x] KB evidence provenance (`document_id`, `chunk_id`, `document_title`).

---

## TODO 8 — KB SECURITY
- [x] User A cannot access User B documents (`test_user_a_cannot_access_user_b_kb_documents`).
- [x] User A cannot search User B chunks (`test_user_a_cannot_search_user_b_kb_chunks`).
- [x] User A cannot delete User B documents (`test_user_a_cannot_delete_user_b_document`).
- [x] User A cannot retrieve User B KB evidence.
- [x] Client cannot override `owner_id` (`test_user_cannot_spoof_owner_in_kb_search`).
- [x] Authenticated user determines ownership via `sub`.
- [x] Development fallback owner is development-only.
- [x] Production cannot silently use `default_dev_user`.
- [x] KB queries are always owner scoped.

---

## TODO 9 — KB INGESTION FLOW
- [x] Ingestion flow: DOCUMENT -> VALIDATE -> HASH -> EXTRACT TEXT -> NORMALIZE -> CHUNK -> STORE -> SEARCHABLE KB.
- [x] Deterministic pipeline.
- [x] Preserved offsets.
- [x] Duplicate document prevention.
- [x] Malformed upload prevention.
- [x] Arbitrary filesystem access prevention.

---

## TODO 10 — KB RETRIEVAL
- [x] Lexical tokenization & normalization.
- [x] Jaccard + BM25-style lexical scoring with configurable relevance threshold.
- [x] Deterministic tie handling.
- [x] Top-k bounded retrieval.
- [x] Tests: KB hit, KB miss, KB empty, irrelevant doc, partial match, multiple docs, multiple chunks, contradictory evidence (`backend/tests/test_private_kb.py`).

---

## TODO 11 — KB-FIRST EVIDENCE ORCHESTRATION
- [x] Orchestration pipeline: CLAIM -> CLASSIFY -> VERIFIABLE? -> PRIVATE KB SEARCH -> SUFFICIENT? -> (YES: KB EVIDENCE & external skipped / NO: EXTERNAL RETRIEVAL -> EVIDENCE SET -> JUDGES -> DECISION).
- [x] Log `KB_SEARCH_STARTED`, `KB_HIT`, `KB_MISS`, `EXTERNAL_RETRIEVAL_STARTED`.
- [x] Preserve evidence source (`PRIVATE_KB` vs `EXTERNAL`).
- [x] Corroboration mode support.

---

## TODO 12 — KB IS NOT TRUTH
- [x] Treat KB content as untrusted evidence passed to multi-judge evaluation.
- [x] Contradictory claims evaluated against KB evidence produce `CONTRADICTED`, not automatic `SUPPORTED` (`test_kb_evidence_is_not_truth_and_evaluates_contradiction`).
- [x] Regression test added.

---

## TODO 13 — PROMPT INJECTION
- [x] Sanitize and isolate AI response, KB document, KB chunk, external evidence, source title, source snippet.
- [x] Maintain structural XML/markdown data boundary separating trusted system instructions from untrusted data payloads (`test_prompt_injection_in_ai_text_remains_data`, `test_prompt_injection_in_kb_document_remains_data`).

---

## TODO 14 — CLAIM EXTRACTION
- [x] Atomic claim extraction.
- [x] Exact text & exact offsets preserved.
- [x] Deterministic segmentation across paragraphs, lists, quotes, mixed content.
- [x] Non-overlapping claims.

---

## TODO 15 — CLAIM CLASSIFICATION
- [x] Taxonomy: `FACTUAL`, `OPINION`, `PREDICTION`, `HYPOTHETICAL`, `CREATIVE`, `INSTRUCTION`, `MIXED`.
- [x] Factual claims routed to verification. Non-factual claims marked non-verifiable.

---

## TODO 16 — EXTERNAL EVIDENCE
- [x] Multi-tier retriever: Tavily -> DuckDuckGo -> Nightcrawler (Wikipedia).
- [x] Timeouts, response-size limits, redirect limits.
- [x] Verifiable URLs & source provenance. No fabricated sources.

---

## TODO 17 — SSRF
- [x] Guard against localhost, 127.0.0.1, private IPv4 (RFC 1918), IPv6, link-local, cloud metadata (169.254.169.254), unsafe redirects, non-HTTP/HTTPS schemes (`test_security_ssrf_matrix.py`).

---

## TODO 18 — EVIDENCE PROVENANCE
- [x] Strict provenance fields for `PRIVATE_KB` (`document_id`, `chunk_id`, `chunk_index`, `document_title`) and `EXTERNAL` (`source_url`, `source_title`, `retriever_name`, `timestamp`).

---

## TODO 19 — JUDGES
- [x] Independent judge execution (Deterministic, Semantic, Model).
- [x] Prompt isolation.
- [x] Judge failures gracefully handled without fake verdicts.

---

## TODO 20 — DECISION ENGINE
- [x] Verdict logic: `SUPPORTED`, `CONTRADICTED`, `UNKNOWN`.
- [x] Evidence insufficiency -> `UNKNOWN` (`test_unknown_handling_on_insufficient_evidence`).
- [x] Disagreement analysis & consensus rules (`test_judging_disagreement.py`).

---

## TODO 21 — VERIFICATION JOBS
- [x] `VerificationJob` lifecycle with `owner_id`.
- [x] Concurrency limit (3 concurrent jobs per user via `track_verification_concurrency`).
- [x] Persistence, history endpoint (`GET /api/v1/verifications`).

---

## TODO 22 — API SECURITY
- [x] Audit every endpoint in `docs/API_SECURITY_MATRIX.md`.
- [x] Authentication, authorization, ownership, validation, rate limiting, error responses.

---

## TODO 23 — RATE LIMITING
- [x] In-memory bounded rate limiter for auth, verification, KB upload/search (`app/core/rate_limit.py`).
- [x] HTTP 429 response with `Retry-After` header (`test_rate_limiting_enforcement_when_enabled`).

---

## TODO 24 — RESOURCE ABUSE
- [x] Body size limits (10MB middleware), max claim count (20), max evidence count (10), KB upload limits (1MB), timeouts.

---

## TODO 25 — FILE SECURITY
- [x] Sanitized filenames, path traversal prevention, content validation, MIME/magic byte checking (`test_filename_sanitization_and_path_traversal`, `test_file_format_and_extension_validation`).

---

## TODO 26 — DATABASE SECURITY
- [x] SQLAlchemy 2.x parameterized queries, asyncpg, indexed foreign keys, scoped queries.
- [x] Table models for `User`, `VerificationJob`, `KnowledgeDocument`, `KnowledgeChunk`.

---

## TODO 27 — SECRET MANAGEMENT
- [x] Audit repo for secret leakage.
- [x] Ensure `.env` is gitignored and `.env.example` has placeholder values.

---

## TODO 28 — REQUEST IDs
- [x] Request ID generation, validation, header propagation (`X-Request-ID`), error inclusion.

---

## TODO 29 — ERROR HANDLING
- [x] Structured errors (`AppError`, `UnauthorizedError`, `ForbiddenError`, `ConflictError`, `RateLimitError`) without exposing stack traces, DB queries, or internal paths.

---

## TODO 30 — LOGGING
- [x] Structured JSON logging with redacted secrets and credentials.

---

## TODO 31 — AUDIT TRAIL
- [x] Persistent security and verification lifecycle audit events (`AuditRecord`).

---

## TODO 32 — CORS / HTTP SECURITY
- [x] Configurable CORS origins, security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`).

---

## TODO 33 — FRONTEND/BACKEND SEPARATION
- [x] Backend exposes strictly `/api/v1` REST contract; no direct client DB access.

---

## TODO 34 — FRONTEND CONTRACT
- [x] Create `docs/FRONTEND_BACKEND_CONTRACT.md`.

---

## TODO 35 — TEMPORARY CLI
- [x] Retain and maintain `scripts/verifai_cli.py` (validated passing `health`, `verify`, and unit tests).

---

## TODO 36 — COMPLETE END-TO-END TEST
- [x] Multi-scenario verification integration test suite (`backend/tests/test_demo_scenarios.py`, `backend/tests/test_orchestrator_api.py`).

---

## TODO 37 — KB END-TO-END TEST
- [x] Comprehensive KB lifecycle test (ingest, chunk, search, retrieve, cross-user isolation, prompt injection) in `backend/tests/test_private_kb.py`.

---

## TODO 38 — SECURITY TEST SUITE
- [x] Complete security regression suite covering auth (`test_auth_security.py`), ownership isolation (`test_ownership_isolation.py`), and audit hardening (`test_security_audit_hardening.py`) — 32 new security tests.

---

## TODO 39 — FULL QUALITY GATES
- [x] `.venv/bin/pytest -q` (1,181 passed).
- [x] `.venv/bin/ruff check .` (All checks passed).
- [x] `.venv/bin/ruff format --check .` (123 files formatted).
- [x] `.venv/bin/mypy backend/app backend/tests benchmark` (Success: no issues in 105 source files).
- [x] `.venv/bin/python scripts/benchmark_tool.py validate` (100 cases, Cohen's kappa validated).
- [x] `.venv/bin/pip check` (No broken requirements).

---

## TODO 40 — BACKEND PERFORMANCE
- [x] Async non-blocking execution, query optimization, bounded memory. Total pipeline latency under 40ms in hermetic mode.

---

## TODO 41 — SECURITY DOCUMENTATION
- [x] Create `docs/SECURITY.md`.

---

## TODO 42 — THREAT MODEL
- [x] Create `docs/SECURITY_THREAT_MODEL.md`.

---

## TODO 43 — BACKEND DEEP-DIVE DOCUMENT
- [x] Create `docs/BACKEND_DEEP_DIVE.md`.

---

## TODO 44 — KB DEEP-DIVE
- [x] Detailed KB architecture, algorithms, and security documented in `docs/BACKEND_DEEP_DIVE.md`.

---

## TODO 45 — FRONTEND HANDOFF
- [x] Complete frontend-ready status checklist documented in `docs/FRONTEND_BACKEND_CONTRACT.md`.

---

## TODO 46 — COMMIT ACCOUNTING
- [x] Track starting commit count (89), atomic commits added, and final count in `docs/COMMIT_LEDGER.md`.

---

## TODO 47 — DEVELOPMENT PR STRATEGY
- [x] Organize modular features into structured milestones/branches targeting `Final`.

---

## TODO 48 — FINAL -> MAIN RELEASE PRs
- [x] Prepare release PR documentation targeting `main`.

---

## TODO 49 — PR LEDGER
- [x] Maintain `docs/COMMIT_LEDGER.md` with PR records.

---

## TODO 50 — BACKEND FREEZE
- [x] Formal backend freeze commit and readiness declaration.

---

## TODO 51 — FINAL BACKEND READINESS CHECK
- [x] All 25 verification checks passed.

---

## TODO 52 — FINAL OUTPUT TO USER
- [x] Comprehensive 21-section final report.

---

## TODO 53 — FINAL GIT VERIFICATION
- [x] Verify clean state on `Final`, no direct push to `main`.

---

## TODO 54 — EXECUTION ORDER
- [x] Follow orderly 33-step implementation sequence.
