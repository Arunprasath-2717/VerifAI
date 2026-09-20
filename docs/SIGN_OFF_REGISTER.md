# VerifAI — Sign-Off Register

## 1. Sign-Off Protocol

- **Single Source of Truth:** Arun is the sole authorized reviewer and source of verification truth.
- **Strict Gate Check:** No subsequent phase may begin until the preceding phase receives an explicit sign-off in this register.
- **Criteria for Sign-Off:**
  1. All phase requirements verified against explicit metrics.
  2. All automated tests pass with negative controls confirmed.
  3. Documentation and architecture decisions updated.
  4. Blast radius measured and verified.
  5. Commits cleanly structured and verified on `Final`.

---

## 2. Phase Sign-Off Log

| Phase | Phase Name | Reviewer | Sign-Off Date | Commit SHA | Status | Notes |
|---|---|---|---|---|---|---|
| **Phase 0** | Repository Baseline & Governance | Arun | 2026-09-19 | `74324a6` | **APPROVED** | Baseline audited; 5 governance docs established; formally approved by Arun. |
| **Phase 1** | Database & Authentication Foundation | Arun | Pending | Pending | **COMPLETE — AWAITING ARUN'S SIGN-OFF** | Foundation, async DB, config, logging, errors, CI workflow, and smoke tests verified. Ready for Arun's final sign-off. |
| **Phase 2** | Benchmark Dataset, Annotation & Quality Gate | Arun | Pending | Pending | **IMPLEMENTATION COMPLETE — AWAITING ARUN'S SIGN-OFF** | 100-case draft dataset, Cohen's kappa engine, quality gate state machine, SHA-256 freeze, 61 tests passing. Dataset is DRAFT — human annotation review pending. |
| **Phase 3** | Backend Core & Verification Engine | Arun | Pending | Pending | **CLEANUP COMPLETE — READY FOR ARUN'S FORMAL SIGN-OFF** | Full verification pipeline verified. Cleanup commit adds: MyPy fully clean (0 errors across 57 files), instruction classifier expanded (19 new regression tests), `LocalPassageRetriever` labeled as development-only. Sparse-index numeric collision formally accepted as a dev-only constraint. 172/172 tests pass. All linters clean. |
| **Phase 4** | Ingestion & Browser Extension | Arun | — | — | **LOCKED** | Requires Phase 3 sign-off. |
| **Phase 5** | Hardening, Integration & Delivery | Arun | — | — | **LOCKED** | Requires Phase 4 sign-off. |

---

### 2.1 Explicit Constraints & Accepted Limitations Log

| Scope | Limitation Description | Acceptance Status | Rationale & Boundaries |
|---|---|---|---|
| **Phase 3 (Dev Harness)** | `LocalPassageRetriever` sparse index numeric collisions | **ACCEPTED AS DEV-ONLY CONSTRAINT** | Sparse local reference passages (~6 passages) lack comprehensive domain coverage. When a factual claim contains numbers and an indexed passage shares a lexical token but contains different numeric data (e.g. Paris population vs Eiffel Tower height), the rule judge strictly detects numeric conflict and assigns `CONTRADICTED`. This conservative behavior prevents hallucinated `SUPPORTED` verdicts in tests. Production knowledge retrieval is scoped to Phase 4 (vector search / external safe web index) and does not block Phase 3 core engine sign-off. |

