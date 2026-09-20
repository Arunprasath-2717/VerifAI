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
| **Phase 2** | **Benchmark Dataset & Annotation**     | 100-case hallucination benchmark, Cohen's kappa quality gate, annotation workflow, dataset freeze | **IN PROGRESS — AWAITING ARUN'S SIGN-OFF** |
| **Phase 3** | **Backend Core & Verification Engine** | Modular monolith services, verification orchestration, local open-source models | Planned              |
| **Phase 4** | **Ingestion & Browser Extension**      | Payload ingestion API, Chrome extension integration                             | Planned              |
| **Phase 5** | **Hardening, Integration & Delivery**  | Hermetic validation, end-to-end verification, release preparation               | Planned              |

---

## 4. Phase 2 — Benchmark Dataset & Annotation Foundation

### Scope (PRD Weeks 2–3)

| Deliverable | Description | Status |
|---|---|---|
| `benchmark/schemas.py` | Pydantic models: `BenchmarkCase`, `AtomicClaim`, `ClaimAnnotation`, `DatasetManifest`; all enums | **COMPLETE** |
| `benchmark/metrics.py` | Deterministic Cohen's kappa (zero-dependency, pure Python) with confusion matrix | **COMPLETE** |
| `benchmark/quality_gate.py` | PRD §23.4 state machine: PASS / REMEDIATION_1 / REMEDIATION_2 / FAIL / INSUFFICIENT_DATA | **COMPLETE** |
| `benchmark/validator.py` | Semantic validation: offset integrity, category-verdict correlation, 100-case PRD constraints | **COMPLETE** |
| `benchmark/freeze.py` | SHA-256 manifest generation and immutable integrity verification | **COMPLETE** |
| `benchmark/cli.py` + `scripts/benchmark_tool.py` | CLI: `validate`, `agreement`, `quality-gate`, `status`, `freeze` | **COMPLETE** |
| `benchmark/data/dataset_v1_cases.json` | 100 cases (40 VF / 30 CH / 30 TU), 60/20/20 split — **DRAFT, NOT HUMAN-ANNOTATED** | **DRAFT** |
| `benchmark/tests/` | 61 deterministic unit tests (metrics, quality gate, validator, freeze) | **COMPLETE — 61/61 PASS** |
| CI pipeline update | Benchmark lint, type-check, pytest, and dataset-validate steps added to `backend-ci.yml` | **COMPLETE** |

### Research Integrity Declarations

> **The dataset at `benchmark/data/dataset_v1_cases.json` is in DRAFT status.**  
> It has NOT undergone human dual-annotator review, Cohen's kappa validation, or quality-gate approval.  
> Freezing is structurally enforced: the `freeze` CLI command requires a formal PASS from the quality gate.  
> No frozen manifest (`benchmark/metadata/dataset_v1_manifest.json`) exists yet.



- **Core MVP Scope:** Backend verification engine (Python + FastAPI modular monolith), Supabase PostgreSQL persistence (SQLAlchemy + asyncpg), Supabase Auth, Supabase Storage, local open-source model inference pipeline, and baseline ingestion.
- **Future Integration Surfaces (Strictly Out-of-Scope for Core MVP):**
  - Model Context Protocol (MCP) integrations
  - Advanced React dashboard frontend
- **Execution Constraints:**
  - AI models must be free/open-source and executed locally where possible.
  - Verification truth is strictly owned by the backend; Arun is the single source of verification truth.
