# VerifAI — Implementation Roadmap

## 1. Project Overview

**Project Name:** VerifAI — Cross-Generation Consistency Hallucination Risk Analysis  
**System Type:** Intelligent Verification and Evaluation System  
**Architecture:** Modular Monolith (Python + FastAPI)  
**Primary Reviewer & Truth Authority:** Arun (Single Source of Verification Truth)

---

## 2. Core Governance & Execution Principles

1. **One-Phase-at-a-Time Workflow:**  
   Development proceeds strictly in sequential phases. Work on a subsequent phase is prohibited until the preceding phase satisfies all completion criteria and receives formal human sign-off.
2. **The Five Mandatory Completion Criteria:**
   - **Criterion 1 (Specification Compliance):** Exact requirements and observable metrics defined and verified.
   - **Criterion 2 (Hermetic Test Coverage):** Unit, integration, and regression tests execute hermetically with zero external credential/network coupling.
   - **Criterion 3 (Negative Control Audit):** Every test and audit mechanism is challenged with negative controls to prevent false positives.
   - **Criterion 4 (Documentation & Contract Integrity):** Architecture, APIs, and phase ledgers accurately reflect active code.
   - **Criterion 5 (Formal Human Sign-Off):** Arun provides explicit approval recorded in `SIGN_OFF_REGISTER.md`.
3. **Branching Model (`Final` before `main`):**
   - Active development occurs exclusively on the `Final` branch.
   - The `main` branch represents stable, verified releases.
   - Unverified work must never be pushed directly to `main`.
4. **Commit Discipline:**
   - Maximum budget of 500 meaningful, atomic, test-backed commits across the project lifecycle.
   - No placeholder, cosmetic, or empty commit bloat.

---

## 3. High-Level Phase Roadmap

| Phase       | Title                                  | Focus Area                                                                      | Status               |
| ----------- | -------------------------------------- | ------------------------------------------------------------------------------- | -------------------- |
| **Phase 0** | **Repository Baseline & Governance**   | Repository audit, environment verification, governance documentation            | **COMPLETE** |
| **Phase 1** | **Database & Auth Foundation**         | Async PostgreSQL foundation, centralized config, structured logging, errors, CI | **COMPLETE — AWAITING ARUN'S SIGN-OFF** |
| **Phase 2** | **Benchmark Dataset & Annotation**     | 100-case hallucination benchmark, Cohen's kappa quality gate, dataset freeze   | **IMPLEMENTATION COMPLETE — AWAITING ARUN'S SIGN-OFF** |
| **Phase 3** | **Backend Core & Verification Engine** | Verification orchestration, claim extraction, evidence retrieval, multi-judge  | **COMPLETE & APPROVED** |
| **Phase 4** | **Ingestion & Browser Extension**      | Payload ingestion API, Chrome extension integration, security & reliability     | **IMPLEMENTATION COMPLETE — AWAITING ARUN'S SIGN-OFF** |
| **Phase 5** | **Hardening, Integration & Delivery**  | Hermetic validation, end-to-end verification, release preparation               | Planned              |

---

## 4. Phase 3 — Backend Core & Verification Engine Scope

| Deliverable | Description | Status |
|---|---|---|
| `backend/app/models/verification.py` | SQLAlchemy 2.x ORM models for jobs, claims, evidence, evaluations, and audit trail | **COMPLETE** |
| `backend/app/schemas/verification.py` | Pydantic v2 schemas for verification inputs, options, outcomes, and audit logs | **COMPLETE** |
| `backend/app/modules/claims/` | `DeterministicClaimExtractor` (offset invariants) and `ContentClassifier` (6-way taxonomy) | **COMPLETE** |
| `backend/app/modules/evidence/` | `LocalPassageRetriever`, `SafeWebRetriever` (Wikipedia API), `TestFixtureRetriever`, SSRF filter | **COMPLETE** |
| `backend/app/modules/judging/` | `DeterministicRuleJudge`, `SecondarySemanticJudge`, `OpenSourceModelJudge`, `DisagreementEngine` | **COMPLETE** |
| `backend/app/modules/verification/` | `VerificationOrchestrator` coordinating pipeline execution, audit logging, and DB persistence | **COMPLETE** |
| `backend/app/api/v1/endpoints/verification.py` | FastAPI REST endpoints `POST /api/v1/verification` and `GET /api/v1/verification/{id}` | **COMPLETE** |
| `scripts/verify.py` | Standalone CLI demonstration tool with human-readable and raw JSON reporting | **COMPLETE** |
| `backend/tests/` | 111 hermetic unit and integration tests (172 tests combined with benchmark suite) | **COMPLETE — 172/172 PASS** |

---

## 5. Phase 4 — Ingestion & Auxiliary Extension Scope

| Deliverable | Description | Status |
|---|---|---|
| `backend/app/models/ingestion.py` | SQLAlchemy 2.x ORM model `IngestedPayload` with relationship to `VerificationJob` and status tracking | **COMPLETE** |
| `backend/app/schemas/ingestion.py` | Pydantic v2 schemas: `IngestionSource`, `IngestionStatus`, `IngestionPayloadRequest`, `IngestionResponse` | **COMPLETE** |
| `backend/app/api/v1/endpoints/ingestion.py` | FastAPI REST endpoints `POST /api/v1/ingest` and `GET /api/v1/ingest/{id}` with SSRF safety & verification trigger | **COMPLETE** |
| `extension/` | Auxiliary demonstration Chrome Manifest V3 extension (DOM auto-detection, selection, context menu, popup UI) | **COMPLETE (AUXILIARY)** |
| `backend/tests/test_ingestion_api.py` | Unit & integration tests for ingestion endpoints, DB session commit, and error responses | **COMPLETE** |
| `backend/tests/test_security_ssrf_matrix.py` | 250 parameterized SSRF tests covering loopback, private IPv4/IPv6, cloud metadata, and domain authority | **COMPLETE** |
| `backend/tests/test_claim_taxonomy_matrix.py` | 175 parameterized taxonomy tests across factual, opinion, prediction, hypothetical, creative, and instruction classes | **COMPLETE** |
| `backend/tests/test_pipeline_reliability_matrix.py` | 129 failure, edge-case, and boundary tests for multilingual text, judge arbitration, numbers, and polarity | **COMPLETE** |
| `backend/tests/test_api_boundary_matrix.py` | 292 boundary tests covering HTTP method enforcement, headers, metadata nesting, UUID paths, and text limits | **COMPLETE** |
| `backend/tests/test_prompt_injection_isolation.py` | Adversarial tests for boundary isolation, breakout sanitization, and prompt extraction prevention | **COMPLETE** |
| `backend/tests/test_deterministic_judge_config.py` | Tests for deterministic configuration (temperature=0.0, seed=42) and metadata reporting | **COMPLETE** |
| `backend/tests/test_unknown_taxonomy_routing.py` | Tests for CONTEXT_UNKNOWN vs SEARCH_UNKNOWN routing, persistence, and serialization | **COMPLETE** |
| Full Test Suite | 1,054 total tests across backend and benchmark suites executed hermetically in <2.5s | **COMPLETE — 1,054/1,054 PASS** |

---

## 6. Architectural Boundaries & Scope Locks

- **Core MVP Scope:** Backend verification engine (Python + FastAPI modular monolith), Supabase PostgreSQL persistence (SQLAlchemy + asyncpg), local knowledge retrieval, safe web search fallback, and baseline ingestion. The core first-cycle interface is strictly the REST API.
- **Auxiliary Demonstration Client:** The Chrome extension is an auxiliary demonstration client outside the locked core backend MVP acceptance gate. It does not introduce a separate core architecture.
- **Future Integration Surfaces (Strictly Out-of-Scope for Core MVP):**
  - Model Context Protocol (MCP) integrations
  - Advanced React dashboard frontend
- **Execution Constraints:**
  - AI models must be free/open-source and executed locally where possible with deterministic defaults (temperature=0.0, seed=42).
  - Verification truth is strictly owned by the backend; Arun is the single source of verification truth.
  - Phase 5 remains strictly locked until formal human sign-off.
