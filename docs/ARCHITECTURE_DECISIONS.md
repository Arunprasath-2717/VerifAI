# VerifAI — Architecture Decision Records (ADR)

## ADR-001: Backend Framework & Pattern
- **Status:** Accepted (Locked)
- **Context:** VerifAI requires high-throughput asynchronous execution, type safety, and clear modular structure for cross-generation hallucination verification.
- **Decision:** Use Python with FastAPI structured as a Modular Monolith.
- **Consequences:** Provides fast asynchronous endpoint handling, native Pydantic schema validation, and modular decoupling without distributed microservice complexity.

---

## ADR-002: Persistence, Database Access & Storage
- **Status:** Accepted (Locked)
- **Context:** The system requires relational persistence for verification jobs, prompt/response pairs, metrics, and artifact storage.
- **Decision:** 
  - Database: Supabase PostgreSQL
  - Database Driver & ORM: SQLAlchemy + asyncpg (fully asynchronous)
  - Object Storage: Supabase Storage
  - Vector Search: `pgvector` extension is a required future prerequisite to be verified before Phase 4 knowledge-base ingestion.
- **Consequences:** Ensures ACID compliance, async I/O performance, unified cloud storage for verification payloads, and vector similarity search readiness.

---

## ADR-003: Authentication Layer & Deferral Addendum
- **Status:** Accepted (Locked)
- **Context:** System endpoints and operations require identity control and tenant isolation.
- **Decision:** Supabase Auth with JWT verification at the FastAPI middleware/dependency layer.
- **Addendum (Scope & Timing):** Active implementation of user authentication is explicitly deferred to Future Enhancements following core verification engine stabilization. It is not part of the initial MVP bootstrap.
- **Consequences:** Keeps initial engineering laser-focused on the core verification engine and consistency evaluation pipeline while preserving an architectural slot for future JWT middleware.

---

## ADR-004: AI Model Execution & Cost Strategy
- **Status:** Accepted (Locked)
- **Context:** Hallucination risk analysis requires LLM inference for claim extraction, cross-generation comparison, and consistency checks.
- **Decision:** Use free and open-source models, executed locally wherever possible.
- **Consequences:** Eliminates per-token vendor costs, protects data privacy, and ensures hermetic execution.

---

## ADR-005: Verification Orchestration & Authority
- **Status:** Accepted (Locked)
- **Context:** Clients (extensions, future UIs) submit verification requests.
- **Decision:** The backend owns 100% of verification orchestration, pipeline execution, and verdict generation. Arun is the single source of verification truth.
- **Consequences:** Prevents client-side bias or inconsistent evaluations; guarantees deterministic and audit-traceable results.

---

## ADR-006: Integration Boundaries & Core MVP Scope
- **Status:** Accepted (Locked)
- **Context:** Future expansion includes MCP and rich web dashboards.
- **Decision:** MCP (Model Context Protocol) and the React web dashboard are designated as future integration surfaces and are strictly out-of-scope for the core MVP.
- **Consequences:** Keeps the MVP laser-focused on the verification engine and consistency evaluation pipeline.

---

## ADR-007: Branching Strategy & Release Governance
- **Status:** Accepted (Locked)
- **Context:** Maintaining repository integrity and preventing untested regression.
- **Decision:**
  - `Final` is the exclusive active development branch.
  - `main` is the stable release branch.
  - Unverified code is never pushed directly to `main`.
  - Target maximum of 500 meaningful commits.
- **Consequences:** Enforces strict gatekeeping and human sign-off before stable branch updates.
