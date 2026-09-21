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
  - Direct pushes to `main` are strictly forbidden.
  - Commits require explicit human sign-off from Arun.
- **Consequences:** Guarantees traceable, reviewed, and verifiable code progression.

---

## ADR-008: Centralized Configuration, Structured Logging & Standardized Error Handling
- **Status:** Accepted (Locked)
- **Context:** Backend observability, diagnostic tracing, and security require structured logging with correlation IDs and consistent error responses without credential leakage.
- **Decision:**
  - Configuration: Environment-driven via `pydantic-settings` with `SecretStr` credential masking.
  - Request Tracking: Pure ASGI middleware injecting `X-Request-ID` into contextvars and response headers with strict input sanitization.
  - Logging: Standard library logging with ISO 8601 UTC timestamps, correlation IDs, and automated secret/credential redaction.
  - Error Handling: Standardized JSON error envelope (`error: {code, message, request_id, details}`) with client-safe status codes and sanitized validation details.
- **Consequences:** Provides end-to-end request traceability, protects sensitive credentials across logs and responses, and establishes a uniform API contract for all downstream consumers.

---

## ADR-009: In-Memory Evidence Retriever as Hermetic Development Harness
- **Status:** Accepted (Locked)
- **Context:** Phase 3 verification pipeline requires hermetic, deterministic execution without external network dependencies or live vector databases. `LocalPassageRetriever` supplies in-memory passages for unit tests, CI, and local CLI demonstrations.
- **Decision:** `LocalPassageRetriever` is designated strictly as a development and testing harness. Its known behavior—including sparse coverage and false-contradiction outcomes when unrelated numeric values co-occur across matching lexical tokens—is formally accepted as a development-only constraint.
- **Consequences:** 
  - All outputs from this retriever are marked with `retriever_name = "LOCAL_PASSAGE_INDEX"`.
  - The deterministic rule judge strictly enforces numeric consistency without fabricating agreement.
  - Production retrieval using vector embeddings, full knowledge corpus ingestion, and live web retrieval is strictly governed under Phase 4 and Phase 5.
  - Phase 3 backend verification core is unblocked for formal human sign-off.

---

## ADR-010: Ingestion API Contract, SSRF Perimeter & Browser Extension Architecture
- **Status:** Accepted (Locked)
- **Context:** Phase 4 requires capturing AI responses directly from active user browser sessions (ChatGPT, Claude, Gemini, DeepSeek, Perplexity) and ingestion through a decoupled API perimeter. The ingestion layer must prevent Server-Side Request Forgery (SSRF) abuse through submitted source URLs, handle client metadata cleanly, support optional immediate verification triggering, and provide an offline-resilient, permission-minimal browser extension.
- **Decision:**
  - **API Contract:** Expose dedicated `/api/v1/ingest` (POST) and `/api/v1/ingest/{id}` (GET) endpoints backed by SQLAlchemy `IngestedPayload` ORM persistence and Pydantic v2 schemas (`extra="forbid"`).
  - **SSRF Defense-in-Depth:** Mandatory pre-persistence URL validation via `is_safe_url`. Rejects loopback (`127.0.0.0/8`, `::1`), link-local/cloud metadata (`169.254.0.0/16`, `fe80::/10`), private RFC-1918 subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), unique local IPv6 (`fc00::/7`), carrier-grade NAT, and non-HTTP schemes with HTTP 400.
  - **Immediate Verification Mode:** Support `verify_immediately: bool = True` triggering `VerificationOrchestrator` in-process and embedding the full verification outcome in the ingestion response, while retaining asynchronous persistence.
  - **Chrome Manifest V3 Extension:** Manifest V3 client using scoped permissions (`activeTab`, `scripting`, `storage`, `contextMenus`, `http://localhost:8000/*`), intelligent DOM heuristics targeting modern LLM web client markup, user selection fallback, context menu integration, and dark glassmorphism popup UI.
- **Consequences:**
  - Secures backend and cloud environments against malicious URL callback abuse.
  - Decouples client text capture from pipeline execution details.
  - Enables single-click verification of AI responses across leading LLM interfaces without requiring browser credential exposure.

