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
| **Phase 0** | **Repository Baseline & Governance**   | Repository audit, environment verification, governance documentation            | **READY FOR REVIEW** |
| **Phase 1** | **Database & Auth Foundation**         | Supabase PostgreSQL schema, asyncpg migrations, Supabase Auth integration       | Planned              |
| **Phase 2** | **Backend Core & Verification Engine** | Modular monolith services, verification orchestration, local open-source models | Planned              |
| **Phase 3** | **Ingestion & Browser Extension**      | Payload ingestion API, Chrome extension integration                             | Planned              |
| **Phase 4** | **Benchmark & Evaluation Suite**       | Consistency hallucination benchmark datasets, evaluation runners                | Planned              |
| **Phase 5** | **Hardening, Integration & Delivery**  | Hermetic validation, end-to-end verification, release preparation               | Planned              |

---

## 4. MVP Boundaries & Out-of-Scope Elements

- **Core MVP Scope:** Backend verification engine (Python + FastAPI modular monolith), Supabase PostgreSQL persistence (SQLAlchemy + asyncpg), Supabase Auth, Supabase Storage, local open-source model inference pipeline, and baseline ingestion.
- **Future Integration Surfaces (Strictly Out-of-Scope for Core MVP):**
  - Model Context Protocol (MCP) integrations
  - Advanced React dashboard frontend
- **Execution Constraints:**
  - AI models must be free/open-source and executed locally where possible.
  - Verification truth is strictly owned by the backend; Arun is the single source of verification truth.
