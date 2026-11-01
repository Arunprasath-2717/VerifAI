# VerifAI — API Security Boundary Matrix

**Document Status:** Complete & Verified  
**Revision:** v1.0.0 (Release Hardening)  
**Classification:** Internal Technical Architecture  
**Target Specification:** FastAPI REST API (`/api/v1`)

---

## 1. Overview & Policy

Every endpoint exposed by the VerifAI backend operates under strict Defense-in-Depth principles. The API boundaries enforce:
- **Transport Security:** Mandatory HTTPS in staging and production environments.
- **Authentication:** Stateless asymmetric/symmetric HMAC-SHA256 JWT tokens with strict claim validation (`sub`, `iss`, `aud`, `exp`, `iat`).
- **Authorization & RBAC:** Role-Based Access Control enforcing `USER`, `ANALYST`, and `ADMIN` privileges.
- **Ownership & IDOR Isolation:** Multi-tenant namespace isolation where `owner_id` is cryptographically tied to the authenticated user ID. Client attempts to specify foreign `owner_id` parameters are rejected with `403 FORBIDDEN`.
- **Rate Limiting:** Sliding-window rate limiting per IP (unauthenticated) or per user ID (authenticated), returning `429 TOO_MANY_REQUESTS` with standard `Retry-After` headers.
- **Payload & Input Sanitization:** Max 10MB payload size, filename sanitization via strict regex, file type whitelist enforcement, and Pydantic v2 field constraint validation.
- **Response Sanitization:** Stripped internal stack traces in production, exclusion of sensitive user data (hashes, salts), and standardized envelope formats.

---

## 2. API Security Boundary Matrix

| Method | Path | Auth Required | Role Required | Rate Limit (req/min) | IDOR Protection | Input Sanitization & Validation | Response Sanitization |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **POST** | `/api/v1/auth/register` | No | None (Public) | 5 / IP | N/A (Creates new identity) | Email normalization (`lower()`), username regex `^[a-zA-Z0-9_-]{3,64}$`, password complexity validation (>=12 chars, upper, lower, digit, symbol) | Hashed password stripped; returns `UserResponse` with `id`, `email`, `username`, `role` |
| **POST** | `/api/v1/auth/login` | No | None (Public) | 10 / IP | N/A (Credential check) | Identifier trimmed, constant-time Argon2id password verification against timing attacks | Returns short-lived JWT access token and public user profile; no secrets exposed |
| **GET** | `/api/v1/auth/me` | **Yes** (Bearer) | Any (`USER`, `ANALYST`, `ADMIN`) | 60 / user | Enforced (`sub` claim resolves target user) | Token signature, issuer, audience, and expiration verification | User profile response, credentials excluded |
| **POST** | `/api/v1/verification` | Optional / Recommended | Any (`USER`+) or Anonymous IP | 20 / user or IP (Max 3 concurrent) | **Enforced:** If authenticated, `owner_id` pinned to user `sub`. Specifying other user's `owner_id` returns `403`. | Payload length capped (10MB middleware, 50k chars Pydantic), prompt injection treated purely as data | Internal judge confidence and model telemetry stripped if degraded; raw LLM prompts excluded |
| **GET** | `/api/v1/verification/{id}` | Optional / Recommended | Any (`USER`+) or Anonymous IP | 60 / user or IP | **Enforced:** Access checked against record `owner_id`. Unauthorized cross-tenant query returns `403 FORBIDDEN` (or `404` on probing). | UUID path parameter parsing and format verification | Sanitized job status and claim breakdown |
| **GET** | `/api/v1/verifications` | **Yes** (Bearer) | Any (`USER`, `ANALYST`, `ADMIN`) | 60 / user | **Enforced:** `USER` and `ANALYST` see only their own jobs (`owner_id == sub`). `ADMIN` can query any owner. | Pagination parameter bounding (`limit` <= 100, `offset` >= 0) | Returns paginated list of user-owned jobs only |
| **POST** | `/api/v1/knowledge/documents` | Optional / Recommended | Any (`USER`+) or Anonymous IP | 30 / user or IP | **Enforced:** `owner_id` resolved to caller. Mismatched client `owner_id` yields `403 FORBIDDEN`. | Title length capped (256), content capped (1MB / 500k chars), filename path-traversal sanitized | Document metadata and chunk count returned; raw storage paths obscured |
| **POST** | `/api/v1/knowledge/upload` | Optional / Recommended | Any (`USER`+) or Anonymous IP | 30 / user or IP | **Enforced:** Uploaded document assigned to caller namespace. Cross-user spoofing blocked with `403`. | Multipart upload; extension whitelist (`.txt`, `.md`, `.markdown`, `.pdf`, `.json`, `.csv`); magic byte validation; 1MB size limit | Sanitized document metadata |
| **GET** | `/api/v1/knowledge/documents` | Optional / Recommended | Any (`USER`+) or Anonymous IP | 60 / user or IP | **Enforced:** Queries strictly filtered by caller `owner_id`. Cross-user inspection blocked. | Query parameter bounding | List of user's own documents only |
| **GET** | `/api/v1/knowledge/documents/{id}` | Optional / Recommended | Any (`USER`+) or Anonymous IP | 60 / user or IP | **Enforced:** Document `owner_id` checked. Mismatches return `403 FORBIDDEN`. | UUID path format validation | Document details without internal system paths |
| **DELETE**| `/api/v1/knowledge/documents/{id}` | Optional / Recommended | Any (`USER`+) or Anonymous IP | 30 / user or IP | **Enforced:** Caller must own document or possess `ADMIN` role. Foreign delete returns `403 FORBIDDEN`. | UUID path format validation | Confirmation of deletion; no sensitive data returned |
| **POST** | `/api/v1/knowledge/query` | Optional / Recommended | Any (`USER`+) or Anonymous IP | 30 / user or IP | **Enforced:** Search inverted index and chunk store strictly bounded to caller's `owner_id`. | Query string length bounded, top_k capped (1..50) | Retrieved chunk snippets bounded, no system metadata leaked |
| **GET** | `/api/v1/health` | No | None (Public) | 120 / IP | N/A | None | Health status of backend, database, model, and evidence subsystems; version info |
| **GET** | `/api/v1/health/liveness` | No | None (Public) | 120 / IP | N/A | None | Binary status `{"status": "alive"}` |
| **GET** | `/api/v1/health/readiness` | No | None (Public) | 120 / IP | N/A | None | Subsystem health checks |

---

## 3. Mandatory Security Headers Applied

Applied globally via `app.core.middleware.SecurityHeadersMiddleware`:

| Header | Configured Value | Purpose |
| :--- | :--- | :--- |
| `X-Content-Type-Options` | `nosniff` | Prevents MIME-type sniffing by browsers |
| `X-Frame-Options` | `DENY` | Prevents clickjacking attacks by forbidding iframe embedding |
| `X-XSS-Protection` | `1; mode=block` | Legacy XSS filter protection |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Protects sensitive paths from leaking in Referer headers |
| `Content-Security-Policy` | `default-src 'self'` (Production) | Restricts resource loading to trusted origins |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Enforces TLS communication (production) |

---

## 4. Rate Limiting Policy Details

Sliding-window rate limiting is implemented via `app.core.rate_limit.SlidingWindowRateLimiter`.
When limits are exceeded:
- **HTTP Status Code:** `429 Too Many Requests`
- **Response Body:** Standard error envelope with code `TOO_MANY_REQUESTS`.
- **Response Headers:** `Retry-After: <seconds>` indicating the backoff window.
