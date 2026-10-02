# VerifAI — Frontend-Backend Integration Contract

**Document Status:** Complete & Locked  
**Version:** 1.0.0  
**Target Clients:** React / Next.js / TypeScript SPA Frontends  
**Backend Base URL:** `http://localhost:8000/api/v1`

---

## 1. Authentication & Session Architecture

### 1.1 Auth Flow
```
[Frontend Client]                                     [VerifAI Backend]
       │                                                      │
       ├──── POST /api/v1/auth/register (email, pwd, user) ──>│
       │<─── 201 Created (UserResponse) ──────────────────────┤
       │                                                      │
       ├──── POST /api/v1/auth/login (email/user, pwd) ──────>│
       │<─── 200 OK (TokenResponse: access_token, user) ──────┤
       │                                                      │
  [Store in Memory / Secure Cookie]                           │
       │                                                      │
       ├──── GET /api/v1/auth/me (Authorization: Bearer) ────>│
       │<─── 200 OK (UserResponse: id, email, role, etc.) ───┤
       │                                                      │
       ├──── POST /api/v1/verification (with Bearer Token) ──>│
       │     (Backend automatically sets owner_id = sub)      │
       │<─── 200 OK (VerificationResponse) ───────────────────┤
```

### 1.2 Token Storage Recommendation
- **Recommended:** Store `access_token` in memory (e.g., React Context / Zustand store) with an `HttpOnly`, `Secure`, `SameSite=Strict` cookie for session refresh, or short-lived memory storage for client SPA.
- **Header:** Include `Authorization: Bearer <access_token>` in all authenticated requests.
- **Logout:** Discard token in memory and call client logout cleanup. (Tokens expire in 60 minutes).

---

## 2. Standardized Error Response Format

All non-2xx responses adhere strictly to the standardized VerifAI Error Envelope:

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or expired authorization token.",
    "details": {
      "reason": "Token expired"
    },
    "request_id": "a9f37c4e09f848b598b0fef930263f27"
  }
}
```

### Error Code Catalogue

| HTTP Status | Error Code | Description / Client Action |
| :--- | :--- | :--- |
| `400` | `INVALID_INPUT` | Field validation failed. Check request body according to schema. |
| `401` | `UNAUTHORIZED` | Token missing, invalid, or expired. Prompt user to log in. |
| `403` | `FORBIDDEN` | Caller does not possess sufficient role or attempted IDOR cross-tenant access. |
| `404` | `NOT_FOUND` | Verification job or document ID does not exist. |
| `409` | `RESOURCE_CONFLICT` | User with given email or username already exists. |
| `413` | `PAYLOAD_TOO_LARGE`| Request body exceeds 10MB limit or uploaded file exceeds 1MB limit. |
| `422` | `UNPROCESSABLE_ENTITY` | Unsupported file extension or corrupted file content. |
| `429` | `TOO_MANY_REQUESTS`| Rate limit or concurrency limit exceeded. Check `Retry-After` header. |
| `500` | `INTERNAL_SERVER_ERROR` | Server exception. Report `request_id` to administrator. |

---

## 3. Core API Endpoints & Payloads

### 3.1 Authentication

#### `POST /api/v1/auth/register`
**Request Body:**
```json
{
  "email": "analyst@example.com",
  "username": "analyst_jane",
  "password": "SecurePassword2026!"
}
```
**Response Body (`201 Created`):**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "email": "analyst@example.com",
  "username": "analyst_jane",
  "role": "USER",
  "is_active": true,
  "created_at": "2026-10-02T10:00:00Z"
}
```

#### `POST /api/v1/auth/login`
**Request Body:**
```json
{
  "email_or_username": "analyst_jane",
  "password": "SecurePassword2026!"
}
```
**Response Body (`200 OK`):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "email": "analyst@example.com",
    "username": "analyst_jane",
    "role": "USER",
    "is_active": true,
    "created_at": "2026-10-02T10:00:00Z"
  }
}
```

#### `GET /api/v1/auth/me`
**Headers:** `Authorization: Bearer <token>`  
**Response Body (`200 OK`):** `UserResponse` object.

---

### 3.2 Verification Pipeline

#### `POST /api/v1/verification`
Submits text for claim extraction, evidence retrieval, and dual-judge verification.

**Headers:** `Authorization: Bearer <token>` (Optional but recommended)  
**Request Body:**
```json
{
  "text": "The Eiffel Tower is located in Paris, France. It was completed in 1889.",
  "options": {
    "enable_live_search": true,
    "confidence_threshold": 0.7,
    "max_claims": 20
  }
}
```
*(Note: If authenticated, `options.owner_id` is automatically set to the caller's user ID. Specifying a foreign `owner_id` returns `403 FORBIDDEN`.)*

**Response Body (`200 OK`):**
```json
{
  "verification_id": "7663fe3c-d18e-4bbf-8f69-1bd7b908fc3d",
  "status": "COMPLETED",
  "overall_verdict": "SUPPORTED",
  "trust_score": 1.0,
  "total_claims": 2,
  "supported_claims": 2,
  "contradicted_claims": 0,
  "unknown_claims": 0,
  "processing_time_ms": 142.5,
  "owner_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "claims": [
    {
      "id": "c1f7a02e-9d29-4bcf-9db1-18e388147d34",
      "claim_text": "The Eiffel Tower is located in Paris, France",
      "verdict": "SUPPORTED",
      "confidence": 0.95,
      "content_type": "FACTUAL",
      "is_verifiable": true,
      "start_offset": 0,
      "end_offset": 44,
      "explanation": "Consensus verdict: SUPPORTED based on 1 evidence passages.",
      "unknown_reason": null,
      "evidence": [
        {
          "id": "e45b174f-9e79-4a0b-bc11-21394f4c718a",
          "snippet": "The Eiffel Tower is a wrought-iron lattice tower on the Champ de Mars in Paris, France.",
          "source_title": "Eiffel Tower - Wikipedia",
          "source_url": "https://en.wikipedia.org/wiki/Eiffel_Tower",
          "retriever_name": "WIKIPEDIA",
          "relevance_score": 0.92,
          "authority_score": 0.95,
          "publication_date": "2026-01-01"
        }
      ],
      "judges": [
        {
          "judge_name": "Judge-Primary-Deterministic",
          "judgment": "SUPPORTED",
          "confidence": 0.95,
          "rationale": "Evidence passage confirms key entities and propositions (token overlap: 6/6)."
        },
        {
          "judge_name": "Judge-Secondary-Semantic",
          "judgment": "SUPPORTED",
          "confidence": 0.90,
          "rationale": "High semantic entailment with verified facts."
        }
      ]
    }
  ]
}
```

#### `GET /api/v1/verification/{id}`
Fetches the status and results of a verification job.  
**Headers:** `Authorization: Bearer <token>` (if job belongs to a user)  
**Response Body (`200 OK`):** `VerificationResponse` object.

#### `GET /api/v1/verifications`
Lists prior verification jobs with pagination.  
**Headers:** `Authorization: Bearer <token>`  
**Query Parameters:** `limit=20&offset=0`  
**Response Body (`200 OK`):**
```json
{
  "total": 42,
  "limit": 20,
  "offset": 0,
  "items": [
    {
      "verification_id": "7663fe3c-d18e-4bbf-8f69-1bd7b908fc3d",
      "status": "COMPLETED",
      "overall_verdict": "SUPPORTED",
      "trust_score": 1.0,
      "total_claims": 2,
      "supported_claims": 2,
      "contradicted_claims": 0,
      "unknown_claims": 0,
      "processing_time_ms": 142.5,
      "owner_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "created_at": "2026-10-02T10:15:30Z"
    }
  ]
}
```

---

### 3.3 Private Knowledge Base

#### `POST /api/v1/knowledge/upload` (Multipart File Upload)
Uploads a document file (`.txt`, `.md`, `.pdf`, `.json`, `.csv`) up to 1MB.  
**Headers:** `Authorization: Bearer <token>`  
**Form Data:**
- `file`: Raw binary file data
- `title`: (Optional) Custom title
- `owner_id`: (Optional, must match JWT caller)

**Response Body (`201 Created`):**
```json
{
  "id": "96f9ea19-7ce3-410f-9e66-7e4857650f7b",
  "title": "Corporate AI Guidelines",
  "filename": "guidelines.pdf",
  "file_type": "PDF",
  "file_size": 20480,
  "chunk_count": 4,
  "owner_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "created_at": "2026-10-02T10:20:00Z"
}
```

#### `GET /api/v1/knowledge/documents`
Lists documents owned by the caller.  
**Headers:** `Authorization: Bearer <token>`  
**Response Body (`200 OK`):** `DocumentListResponse` array.

#### `DELETE /api/v1/knowledge/documents/{id}`
Deletes a document and purges its chunks from the search index.  
**Headers:** `Authorization: Bearer <token>`  
**Response Body (`200 OK`):** `{"deleted": true, "document_id": "..."}`

#### `POST /api/v1/knowledge/query`
Executes search query against caller's private knowledge base.  
**Request Body:**
```json
{
  "query": "What is the policy for customer refunds?",
  "top_k": 5
}
```
**Response Body (`200 OK`):**
```json
{
  "query": "What is the policy for customer refunds?",
  "total_hits": 2,
  "items": [
    {
      "chunk_id": "f51be568-13bd-4b20-a5b0-7ff4b35186b5",
      "document_id": "96f9ea19-7ce3-410f-9e66-7e4857650f7b",
      "document_title": "Refund Policy 2026",
      "snippet": "Full refunds are issued within 30 days of purchase upon proof of receipt.",
      "relevance_score": 0.88,
      "chunk_index": 0
    }
  ]
}
```

---

## 4. Frontend Verification Workflow & Polling Model

For standard verifications under 2,000 characters, `POST /api/v1/verification` responds synchronously in 50–300ms.

For asynchronous or long-form document verifications:
1. **Submit:** Frontend calls `POST /api/v1/verification`.
2. **Immediate Return:** If backend accepts job asynchronously, response status is `PENDING` or `PROCESSING`.
3. **Polling Strategy:**
   - Polling interval: Every `1.0` second for up to 30 seconds.
   - Endpoint: `GET /api/v1/verification/{id}`.
   - Stop Condition: `status == "COMPLETED"` or `status == "FAILED"`.
   - Exponential Backoff: Optional backoff (`1s`, `1.5s`, `2s`, `3s`).

---

## 5. TypeScript Interface Definitions

```typescript
// =============================================================================
// VerifAI TypeScript Contract
// =============================================================================

export type UserRole = "USER" | "ANALYST" | "ADMIN";

export interface UserResponse {
  id: string;
  email: string;
  username: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: UserResponse;
}

export type VerdictType = "SUPPORTED" | "CONTRADICTED" | "UNKNOWN" | "NON_VERIFIABLE";
export type ContentType = "FACTUAL" | "OPINION" | "PREDICTION" | "NON_FACTUAL";

export interface EvidenceItem {
  id: string;
  snippet: string;
  source_title: string;
  source_url: string | null;
  retriever_name: string;
  relevance_score: number;
  authority_score?: number;
  publication_date?: string | null;
  chunk_id?: string;
  document_id?: string;
}

export interface JudgeResult {
  judge_name: string;
  judgment: VerdictType;
  confidence: number | null;
  rationale: string;
  evidence_references?: string[];
}

export interface ClaimVerification {
  id: string;
  claim_text: string;
  verdict: VerdictType;
  confidence: number | null;
  content_type: ContentType;
  is_verifiable: boolean;
  start_offset: number;
  end_offset: number;
  explanation: string;
  unknown_reason: string | null;
  evidence: EvidenceItem[];
  judges: JudgeResult[];
}

export interface VerificationResponse {
  verification_id: string;
  status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";
  overall_verdict: VerdictType;
  trust_score: number;
  total_claims: number;
  supported_claims: number;
  contradicted_claims: number;
  unknown_claims: number;
  processing_time_ms: number;
  owner_id?: string | null;
  claims: ClaimVerification[];
}

export interface ApiErrorEnvelope {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
    request_id?: string;
  };
}
```
