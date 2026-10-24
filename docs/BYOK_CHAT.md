# VerifAI — Multi-provider BYOK & Review-Loop Chat

This is the existing authenticated VerifAI workspace, not a mock application.

## Connect a real provider

1. Open http://localhost:3000/chat. If logged out, the application sends you to
   login and returns to the requested chat page after successful authentication.
   On the Google form, select the intended Google account yourself and approve
   the account-provider consent flow.
2. In the **BYOK connections** sidebar, choose **Add API key** for Groq,
   OpenRouter or NVIDIA NIM. Existing custom HTTPS providers configured in
   **Workspace Settings → AI Providers** also appear in chat. Use the official
   provider dashboard to create a key if you don't have one.
3. Paste the key directly into the application (never into source code or this
   chat). Click **Save & test**. The credential is encrypted per authenticated
   owner using the backend's `PROVIDER_CREDENTIAL_ENCRYPTION_KEY`.
4. Successful provider validation updates the status to **Verified** and
   triggers a fresh authenticated `/providers/chat-models` discovery request.
   Key storage by itself is **Saved**, not **Connected**. Failed checks and
   model-catalog errors remain visible and do not unlock invented models.
5. **Catalogued is not working.** For each candidate in **Connected models**,
   choose **TEST & SELECT**. This runs a real, bounded completion using your
   saved key. Only a non-empty successful inference permits adding that model
   to the separate **Selected & tested models** workspace. Failed/rate-limited
   models remain unselected, with an explanation and a retry action. Tests
   consume a small portion of the provider's quota. Model readiness is checked
   again after catalog refresh or a key change.
6. Select up to three working models, then send a *single* prompt. Their
   upstream requests run concurrently with failure isolation. The user sees
   independent model cards, status, latency, and failures. After those requests
   complete, one already-selected working model receives a bounded, sanitized
   set of the answers and generates an organized consolidated response.
   If this synthesis fails, the UI receives an honest extractive fallback.
7. VerifAI's evidence orchestrator runs on the synthesis when two or more
   model answers are available and verification is requested (the chat UI
   requests it by default). **Agreement between models does not establish
   truth.** Labels distinguish evidence-supported claims from unverified or
   review-required outputs, with a verification link only when a real job
   exists. PRD and architecture recommendations are proposals, not facts
   certified by an external authority.
8. Conversation history persists individual model results and the synthesis
   in PostgreSQL. Reloading restores all of them. Deletion requires
   confirmation and successful backend deletion.

## Supported integration types

VerifAI has first-party integration paths for OpenAI, Anthropic Claude,
Google Gemini, Groq, OpenRouter, NVIDIA NIM, Mistral, DeepSeek, Perplexity,
xAI, Together AI, Fireworks, Cerebras, DeepInfra, SambaNova and Moonshot.
A saved custom public HTTPS OpenAI-compatible API can also be connected.

- Claude and Gemini use their respective **native** model discovery and
  completion APIs. Other listed integrations use official OpenAI-compatible
  endpoints and their native account access controls.
- A listed API model is *not* proof that it supports text completions or
  is affordable. Only a successful **TEST & SELECT** completion can place a
  model into a response slot. Billing and quota are the user's responsibility.
- OpenRouter continues to restrict selectable routes to **explicitly :free**
  text models with verified zero-price metadata. Other providers may require
  paid credit.
- Fixed built-in provider keys cannot be redirected to a user-supplied URL.
  Unlisted providers can use the separate HTTPS custom endpoint flow, with
  private-network and localhost destinations rejected.

## Cross-model project synthesis and loop engineering

1. Select one to three *tested* responder models in the dedicated response
   lanes (for example a GPT model, Gemini and Claude Sonnet).
2. In **Synthesis studio**, select an independently tested **editor model**,
   or leave automatic selection enabled to reuse the first responding model.
   The editor can be a *fourth* provider/model, independent of contributors.
3. Choose the desired deliverable: **Project idea**, **PRD**, **Architecture**
   or **Balanced synthesis**.
4. Choose **0, 1 or 2** bounded critique-and-revision cycles. The app will
   make at most three parallel initial inferences, one synthesis inference,
   and two more per selected review cycle (a distinct responding model critiques
   the synthesis when available; the editor revises). Failed cycles terminate.
5. Read the independent responses and the consolidated answer separately.
   Reviewable cycle notes, succeeded/failed revisions, provenance and the
   optional external-evidence result persist with the conversation.

The output is a reasoned *proposal*, not an objectively proven "best" idea.
Model agreement alone is never labeled factual verification; claims can only
be labeled evidence-supported after a separate evidence assessment.
No provider is guaranteed to be up or free at every moment.

## Groq, OpenRouter and NVIDIA NIM policies

- Groq: user-scoped key test at
  `https://api.groq.com/openai/v1/models`; inference at
  `https://api.groq.com/openai/v1/chat/completions`. Model names come from
  the provider's discovery response, excluding obvious audio/guard variants.
  Any free-tier eligibility, quota, and rate limiting depend on the account.
- OpenRouter: user-scoped key test/discovery at
  `https://openrouter.ai/api/v1/models`; inference at
  `https://openrouter.ai/api/v1/chat/completions`.
  Only explicitly suffixed `:free` text-chat models with explicit zero input
  and output token pricing are selectable; requests for paid routes are rejected
  **before** recording or sending prompts in the BYOK execution path.
- NVIDIA hosted NIM: official endpoint
  `https://integrate.api.nvidia.com/v1`, with
  `GET /v1/models` and `POST /v1/chat/completions`. The model catalog does
  not prove quota, pricing, or working completion; use **TEST & SELECT**.
  The account owner pays or uses available NVIDIA credits according to the
  provider's terms.
- The old custom-provider form incorrectly suggested
  `http://localhost:8000/v1` (VerifAI's own backend). A previously saved
  provider named NVIDIA with that exact legacy placeholder now directs its
  *test* to the official hosted NVIDIA endpoint. After a successful
  validation the safer endpoint is persisted on the existing encrypted
  provider credential. The user does not need to expose or paste their
  saved key into the chat or repository.
- Other custom OpenAI-compatible providers require public HTTPS endpoints.
  The backend rejects unsafe localhost, private-network, credential-in-URL,
  and other invalid destinations before transmitting a bearer key.
  Self-hosted NIM in an internal network requires a separately secured HTTPS
  gateway; it is not enabled through a generic localhost URL.
- An apparently connected model can still return a provider error or rate
  limit. The application surfaces that outcome instead of showing fake
  success. Free-model availability varies.

## Security and architecture

- Authentication is required to save, test, unlink, or discover credentials.
- Credentials are encrypted at rest with Fernet, associated with each user's
  account, and never sent back to the frontend. The UI gets a masked hint.
- Groq, OpenRouter, NVIDIA NIM and custom HTTPS execution use
  **request-local** decrypted keys scoped to
  the message's authenticated owner. Other users' credentials and server-wide
  provider keys are not silently substituted.
- No provider secrets are saved to Git or displayed in errors. Upstream error
  response bodies are not echoed to users by these adapters.
- A server-side safety gate rejects likely pasted API keys, passwords,
  bearer tokens, private keys, and credential-bearing connection strings
  *before* creating messages or invoking providers. Conversation titles are
  checked too; SSE does not acknowledge a rejected sensitive prompt.
- Legacy conversation context containing recognizable credentials is omitted
  from outbound context. Unexpected credential-looking provider output is
  redacted before persistence, synthesis, or UI display.
- These conservative pattern checks are defense-in-depth, **not a guarantee**
  against every kind of confidential or personal data. Users should not paste
  sensitive material into third-party-model prompts.
- For all providers, the chat runner constructs request-local adapters
  with the authenticated owner's decrypted credential only. Unlinked keys
  are rejected before persisting chat prompts; server-level keys are never
  borrowed by another account. The live SSE route uses the same preflight.
- A deliberate synthesis/review loop may consume additional provider quota:
  the UI shows the maximum request count before submission, and the backend
  limits review rounds to two with bounded output sizes.
- The probe endpoint is authenticated and rate limited. Each smoke test
  validates that a user owns a verified key and that the model belongs to the
  current eligible provider catalog; it never reuses a server-global key.
- Providers receive the selected prompt; their retention/training policies
  apply. VerifAI does not guarantee external providers never retain input.
- Requests are non-streaming for now; the UI correctly reports “Generating…”
  until each request returns and does not fabricate token-by-token streaming.
- Conversation context includes a bounded amount of saved prior user messages
  and real previous model outputs. Chat history is persisted in the original
  application's PostgreSQL tables.

## Validation performed (2026-10-23)

- TypeScript and Vite production build: passed.
- Isolated production-browser regression: passed, including Groq key
  save/test/model refresh, free OpenRouter prompt selection, failed chat
  creation, reports, verification, public routes, and 390px mobile layout.
- Groq/OpenRouter/NVIDIA and custom provider backend isolated tests:
  passed using `httpx.MockTransport`. No user credential was used in tests.
- Full backend suite: **1,169 passed**, 4 preexisting warnings, on a disposable
  PostgreSQL database, not the real development database.
- Separate full-stack smoke: passed with production React bundle, real
  testing-mode FastAPI, isolated PostgreSQL, and disposable test login.
- Live development-server health/readiness: HTTP 200.
- The browser checks guest deep-link preservation for post-login return
  to /chat, saved chat reply restoration after reload, confirmed deletion,
  provider-settings transient errors and credential revocation.
- **Not performed**: actual Google account authorization or external
  Groq/OpenRouter/NVIDIA completions using a personally supplied real key.
  Real smoke tests now happen on demand in the authenticated UI after a user
  clicks TEST & SELECT, so provider quotas are not spent automatically on
  every page visit. The isolated integration suite simulates concurrent
  upstream completions and verifies source/owner isolation.

Do not hardcode personal account identifiers, Google credentials, or provider
keys in the repository. No commits, pushes, or public deployments are part
of this change set.
