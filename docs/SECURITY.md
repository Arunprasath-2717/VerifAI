# VerifAI — Security Architecture & Policy

**Document Status:** Approved & Enforced  
**Version:** 1.0.0 (Release Hardening)  
**Security Level:** Production Grade  
**Target Platform:** Linux / Python 3.14 / FastAPI / PostgreSQL / Asyncpg

---

## 1. Security Architecture Overview

VerifAI enforces a defense-in-depth security model across all network, application, database, and machine learning boundaries. As an AI-powered verification engine evaluating cross-generation consistency and hallucination risk, VerifAI processes untrusted third-party LLM generations and private customer knowledge bases. 

Under VerifAI's security paradigm:
1. **Zero Implicit Trust:** All inputs—including AI response text, retrieved evidence from external APIs, and user-uploaded documents—are treated as hostile, unverified data.
2. **Untrusted Evidence Isolation:** Private Knowledge Base (PKB) contents and live search snippets are treated as external claims or reference data, NEVER as execution commands or absolute ground truth.
3. **Multi-Tenant Cryptographic Boundaries:** User documents, search indices, and verification jobs are strictly partitioned by authenticated user identity (`owner_id`), preventing horizontal and vertical privilege escalation.
4. **Hermetic & Bounded Computation:** Execution pipelines enforce strict resource constraints (timeout limits, maximum payload sizes, sliding-window rate limits, and concurrency caps) to guarantee resilience against denial-of-service vectors.

```
                     +---------------------------------------+
                     |         TLS / Reverse Proxy           |
                     +---------------------------------------+
                                        │
                                        ▼
                     +---------------------------------------+
                     |        Security Middleware Layer      |
                     | - HTTP Headers (nosniff, DENY)        |
                     | - Max Request Size (10MB)             |
                     | - Correlation Request ID Tracking     |
                     +---------------------------------------+
                                        │
                                        ▼
                     +---------------------------------------+
                     |         Authentication & RBAC         |
                     | - Argon2id Password Hashing           |
                     | - HMAC-SHA256 JWT Claim Verification  |
                     | - Role Scopes (USER, ANALYST, ADMIN)  |
                     +---------------------------------------+
                                        │
                                        ▼
                     +---------------------------------------+
                     |       Sliding-Window Rate Limiter     |
                     | - Per-IP / Per-User Action Windows    |
                     | - Concurrency Caps (Max 3 Jobs/User)  |
                     +---------------------------------------+
                                        │
                                        ▼
                     +---------------------------------------+
                     |      Application Layer / Endpoints    |
                     | - Ownership Resolution (Anti-IDOR)    |
                     | - Pydantic v2 Schema Sanitization     |
                     +---------------------------------------+
                                        │
                     ┌──────────────────┴──────────────────┐
                     ▼                                     ▼
        +─────────────────────────+           +─────────────────────────+
        |  Verification Engine    |           |  Private Knowledge Base |
        | - Claim Extraction      |           | - Magic Byte Validation |
        | - External SSRF Shield  |           | - Filename Sanitization |
        | - Prompt Isolation      |           | - Isolated Inverted Idx |
        | - Dual-Judge Consensus  |           | - Tenant Partitioning   |
        +─────────────────────────+           +─────────────────────────+
```

---

## 2. Authentication & Authorization Model

### 2.1 Password Hashing (Argon2id)
All user passwords are encrypted using state-of-the-art **Argon2id** through `argon2-cffi`:
- **Algorithm:** Argon2id (hybrid memory-hard and timing-attack resistant)
- **Time Cost ($t$):** 2 iterations
- **Memory Cost ($m$):** 65,536 KiB (64 MiB)
- **Parallelism ($p$):** 4 threads
- **Salt Generation:** 16 cryptographically random bytes via OS CSPRNG
- **Constant-Time Verification:** Employs constant-time string comparisons to eliminate timing side-channels.

### 2.2 Stateless JWT Tokens
Authentication sessions are managed via signed JSON Web Tokens:
- **Algorithm Whitelist:** Strictly restricted to `HS256` (HMAC with SHA-256). Any attempt to pass `none`, asymmetric keys, or unsupported algorithms triggers immediate rejection.
- **Mandatory Claim Validation:**
  - `sub`: Authenticated User ID (UUID string)
  - `iss`: Configured issuer (`VerifAI-Auth-Authority`)
  - `aud`: Configured audience (`verifai-client`)
  - `exp`: Short-lived expiration (default 60 minutes)
  - `iat`: Timestamp of issuance
  - `role`: Role string (`USER`, `ANALYST`, `ADMIN`)
- **Key Rotation Ready:** `JWT_SECRET` must be set via high-entropy environment variables.

### 2.3 Role-Based Access Control (RBAC)
VerifAI distinguishes between three functional roles:
- **`USER`:** Default authenticated role. Access is restricted strictly to their own verification jobs and private knowledge documents.
- **`ANALYST`:** Read/write permissions across personal verifications, with elevated access to benchmark run telemetry and calibration metrics.
- **`ADMIN`:** Superuser access allowing cross-tenant inspection for audit and compliance, tenant resource management, and system-wide rate limit configuration.

---

## 3. Data Protection & Privacy

### 3.1 In-Transit Protection
- All traffic must terminate over TLS 1.3 (or TLS 1.2 minimum).
- HTTP Strict Transport Security (`Strict-Transport-Security: max-age=31536000; includeSubDomains`) is enforced in production deployments.

### 3.2 At-Rest Protection & Multi-Tenancy
- Database rows for `VerificationJob` and `KnowledgeDocument` include indexed `owner_id` columns.
- All SQL queries automatically include `WHERE owner_id = :user_id` filtering, eliminating Insecure Direct Object References (IDOR).
- Ephemeral in-memory fallback stores maintain distinct hash maps keyed by `owner_id`.

### 3.3 Sensitive Information Masking
- Password hashes and internal cryptographic keys are never serialized in API responses (`UserResponse` explicitly omits `hashed_password`).
- Detailed error stack traces are suppressed in non-debug environments (`AppError` maps internal exceptions to generic customer-safe error envelopes).

---

## 4. Threat Mitigation Summary

| Threat / Vulnerability | Mitigation Strategy | Implemented In |
| :--- | :--- | :--- |
| **Prompt Injection** | AI response text and KB evidence are parsed purely as AST/string propositions. Text is never concatenated into raw LLM instructions without boundary encapsulation. Deterministic and NLI judges evaluate claims against evidence using structured logic. | `app.modules.judging`, `app.modules.claims` |
| **SSRF (Server-Side Request Forgery)** | All external HTTP evidence retrievers validate URLs before connection. IP resolution blocks loopback (`127.0.0.0/8`, `::1`), private ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), link-local (`169.254.0.0/16`), and metadata endpoints (`metadata.google.internal`, `169.254.169.254`). | `app.modules.evidence.retrievers` |
| **IDOR (Horizontal Privilege Escalation)**| All verification and knowledge base queries enforce identity resolution against the authenticated JWT caller (`sub`). Spoofed `owner_id` requests are blocked with `403 FORBIDDEN`. | `app.core.dependencies`, `app.api.v1.endpoints` |
| **Denial of Service (Payload)** | Global `10MB` payload limit middleware returns `413 PAYLOAD_TOO_LARGE`. Document upload endpoints enforce `1MB` maximum file size. Verification text capped at 50,000 characters. | `app.core.middleware`, `app.schemas` |
| **Denial of Service (Rate / Concurrency)**| In-memory sliding-window rate limiters throttle excessive requests per IP or User ID (`429 TOO_MANY_REQUESTS` with `Retry-After`). Active verification concurrency is capped at 3 simultaneous jobs per user. | `app.core.rate_limit` |
| **Arbitrary File Upload / Path Traversal**| Uploaded filenames are sanitized via regex (`[a-zA-Z0-9_.-]`), strip path delimiters (`../`, `..\`), and enforce extension whitelisting (`.txt`, `.md`, `.pdf`, `.json`, `.csv`). Executable extensions (`.py`, `.exe`, `.sh`) are rejected with `422`. Magic bytes are inspected. | `app.modules.knowledge.ingestion` |
| **Timing Attacks** | Password verification uses constant-time string comparisons. | `app.core.security` |

---

## 5. Vulnerability Reporting Policy

We welcome vulnerability reports from the security research community. If you discover a security vulnerability in VerifAI, please follow responsible disclosure guidelines:

1. **Email Reports:** Send all disclosures directly to `security@verifai.internal` or open an encrypted private issue.
2. **Details to Include:**
   - Detailed description of the vulnerability.
   - Exact steps, scripts, or HTTP payloads to reproduce.
   - Potential impact assessment.
   - Any suggested mitigations.
3. **Response Timelines:**
   - **Initial Acknowledgement:** Within 24 business hours.
   - **Triage & Reproducibility Assessment:** Within 72 business hours.
   - **Patch Release:** Target within 14 business days for Critical/High severity issues.
4. **Non-Disclosure Agreement:** Please do not publicly disclose the issue until a patch has been merged and released.

---

## 6. Security Checklist for Deployment

Before deploying VerifAI to a staging or production environment, ensure the following configuration checklist is satisfied:

- [ ] **Environment Separation:** Set `ENVIRONMENT=production` in the server environment.
- [ ] **Debug Disabled:** Ensure `DEBUG=False` in configuration.
- [ ] **Cryptographic Keys:**
  - [ ] Set `JWT_SECRET` to a cryptographically strong, randomly generated string of at least 32 bytes (`openssl rand -hex 32`).
  - [ ] Never commit secrets, keys, or passwords to git.
- [ ] **Database Configuration:**
  - [ ] Use SSL/TLS connection parameters for PostgreSQL/Supabase (`ssl=require`).
  - [ ] Enforce principle of least privilege on the database user.
- [ ] **Rate Limiting:**
  - [ ] Verify `RATE_LIMIT_ENABLED=True`.
  - [ ] In multi-replica clusters, configure Redis as the distributed state store for rate limiting.
- [ ] **Network & Ingress:**
  - [ ] Configure reverse proxy (Nginx, Traefik, or Cloudflare) to terminate TLS 1.3.
  - [ ] Set upstream timeout policies to prevent slowloris attacks.
  - [ ] Bind backend Uvicorn/Gunicorn processes to internal network interfaces (e.g., `127.0.0.1` or private VPC overlay), never directly to public `0.0.0.0`.
- [ ] **Dependencies:**
  - [ ] Run `.venv/bin/pip check` and vulnerability scans (e.g., `pip-audit`, `safety`).
  - [ ] Keep container base images updated to latest security patches.
