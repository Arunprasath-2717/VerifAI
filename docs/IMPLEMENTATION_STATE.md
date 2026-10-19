# Implementation State

Last updated: 2026-10-20 (recovery session 2)

## Environment
- Backend tests must target the isolated `verifai_test` database via a `DATABASE_URL` override (see ARCHITECTURE.md).
- `backend/.env` points at the real `verifai` database (4 users, 1,777 verifications, 5 consents). Do not run tests, migrations, or seeds against it.
- Sandbox blocks localhost sockets; use escalated execution for DB-backed runs.

## Confirmed defects
1. **Auth bypass (critical):** `POST /api/v1/auth/google` issued a session token for any email with no identity proof. `AuthenticationService.authenticate_google` swallowed token-verification errors (`except Exception: pass`) and trusted caller-supplied email/google_id. Reproduced against `verifai_test`: anonymous request returned HTTP 200 with access_token.
2. **Unauthenticated BYOK storage:** `backend/app/api/v1/endpoints/providers.py` keeps user keys in a process-local dict (`_USER_PROVIDER_CONFIGS`): not persisted, not encrypted, not shared across workers.
3. **Discontinued/invented model IDs:** `backend/app/api/v1/endpoints/models.py` lists IDs such as `gpt-5.6-sol`; frontend `ChatPage.tsx` and `VerifyPage.tsx` use `claude-3-5`, `gemini-1-5`, `gemini-1.5-pro`; `config.py` defaults to `claude-3-5-sonnet`, `gemini-1.5-flash`.
4. **Token-budget regression (fixed in session 1):** missing `Any` import in `schemas/verification.py`.
5. **Pre-existing mypy errors:** 4 in `providers.py` (`_mask_key` receives `SecretStr | None`; status literal mismatch).

## Completed this session
- Reproduced defect 1 (see above). Fix in progress.

## Next actions
1. Remove `/auth/google` endpoint, `authenticate_google`, `GoogleAuthRequest`, and frontend `googleAuth` (unused by UI). Google sign-in continues through Firebase `/auth/firebase`.
2. Add regression test: anonymous `/auth/google` must not issue a token.
3. Review consent enforcement on `/auth/firebase` and `/legal/consent`.
4. BYOK: replace in-memory provider store with encrypted persistence.
5. Model registry: replace invented IDs with verified, configurable entries.
