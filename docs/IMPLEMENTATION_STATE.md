# Implementation State

Last updated: 2026-10-20 (recovery session 3)

## Environment
- Backend tests must target the isolated `verifai_test` database via a `DATABASE_URL` override.
- `backend/.env` points at the real `verifai` database. Do not run tests, migrations, or seeds against it.
- Sandbox blocks localhost sockets; use escalated execution for DB-backed runs.
- `PROVIDER_CREDENTIAL_ENCRYPTION_KEY` must be set for BYOK credential storage (503 otherwise).

## Commits (recovery series on top of `30a1714`)
- `dcf69f2` feat(budget): token budgets, daily quota, analysis cache, usage ledger
- `403b197` fix(providers): persist encrypted user API credentials
- `d506c36` fix(lint): resolve auth Ruff violations
- `136ba42` fix(auth): enforce Firebase consent server-side
- `a7fec77` fix(lint): wrap token-budget lines over 88 columns

## Verified results (session 3)
- Backend: `pytest backend/tests` on `verifai_test`: 1134 passed.
- Benchmark: `pytest benchmark/tests`: 61 passed.
- `mypy backend/app benchmark`: clean.
- `ruff check scripts benchmark`: clean. `ruff format --check backend scripts benchmark`: 11 files would reformat (mostly pre-existing, including `alembic/versions/d57e9de0b8e6`).
- `ruff check backend`: 84 errors remain, mostly E501 in `api/v1/endpoints/models.py` (31, pre-existing at `30a1714`), `schemas/legal.py` (8, pre-existing), `dashboard.py`, `reports.py`, `schemas/dashboard.py`, `legal.py`, `orchestrator.py`, `repositories/user_consent.py`. The token-budget E501 regression from `dcf69f2` is fixed.
- Frontend: `tsc --noEmit` exit 0; `vite build` succeeds (chunk-size warning only).

## Confirmed defects
1. **Auth bypass (fixed, `30a1714`):** unauthenticated `/auth/google` issued sessions for any email.
2. **Unauthenticated BYOK storage (fixed, `403b197`):** keys were in a process-local dict. Now Fernet-encrypted in `user_provider_credentials`, owner-scoped.
3. **Firebase consent gap (fixed, `136ba42`):** new accounts could be provisioned without Terms acceptance; outdated consent was not enforced. Now enforced before provisioning with `TERMS_REACCEPTANCE_REQUIRED` (403).
4. **Discontinued/invented model IDs (OPEN, Task B blocked):** `models.py`, `ChatPage.tsx`, `VerifyPage.tsx`, `mockBackendData.ts`, `config.py` `DEFAULT_LLM_MODELS`. Not verifiable here (no web search, no provider keys). Do not replace with other guessed IDs.
5. **Mypy errors in `providers.py` (fixed by Task A rewrite).**

## Blockers
- Live Google/Firebase OAuth flow: needs real Firebase project config and a browser session.
- Live provider calls (BYOK validation, model verification): need user keys and network access.
- Model registry verification: needs official provider docs or model-list API access.

## Next actions
1. Task B: verify model IDs against official provider docs or model-list APIs, then replace invented IDs with a backend-owned registry.
2. Lint debt: fix E501 in `models.py`, `legal.py`, `dashboard.py`, `reports.py`, and related files (out of scope for session 3).
3. Frontend consent UI: confirm the signup and Firebase flows surface `TERMS_REACCEPTANCE_REQUIRED` and the 400 `terms_accepted` error.
