# Phase 4 — Automated Tests, CI, and Full-Stack Validation

**Date:** 2026-10-22  
**System:** Arun's `pikachu` only  
**Project:** `/home/arun/Desktop/VerifAI/VerifAI`

Phase 4 added repeatable test coverage **without altering the landing-page design,
the running development database, production credentials, or existing application records**.

## 1. Browser regression suite (no backend needed)

Location: `frontend/tests/browser_regression.py`

Run from `frontend/` after installing locked dependencies:

```bash
npm run lint
npm run build
npm run test:browser
```

Requires Python 3, Chromium or Google Chrome, and a matching ChromeDriver in
`PATH`. The test starts its own temporary Vite production preview server and
ChromeDriver instance on loopback, injects deterministic **in-memory API fixtures**
before app JavaScript runs, and cleans up its own processes.

Covered:
- Lazy-loaded application pages, authentication bootstrap and same-origin API path
- Server-issued UUID for chat creation; real model IDs sent unchanged
- Model responses and failed chat creation displayed without fabricated success
- Verification request option contract and missing-confidence/model-count handling
- Failed verification stays on the input page and displays the API error
- 1Y reports filter requests `timeframe=1Y`
- Knowledge-base title-only uploads are rejected, not "indexed"
- Mobile 390px horizontal overflow
- Public landing page, login page and signup page

**All browser checks passed locally against the production build.**
The mocks are **not** real AI results and do **not** write any database records.
The test exits with a nonzero code on any failed assertion.

## 2. Real backend regressions against disposable PostgreSQL

Backend regression checks run with `VERIFAI_TEST_DATABASE_URL` pointing to an
**isolated test-only** database. During Phase 4, a new PostgreSQL 16 container
was started on a separate loopback port, using temporary in-memory filesystem
storage; the existing `verifai-postgres` container was left untouched.

Validation on this system:
- Full backend suite: **1,146 passed, 4 warnings**
- New test database URL guard: **11 passed**
- Focused authentication, chat, and health checks: **33 passed**

The warning backlog is inherited from Starlette deprecations and unawaited
mock coroutines. The existing `backend/tests/conftest.py` guard refuses to
run tests against a configured database not explicitly named as a test database.
New guard cases cover accepted/rejected test-DB URL names.

Never run a full backend test suite against the development PostgreSQL database.
For an isolated database, use:

```bash
VERIFAI_TEST_DATABASE_URL='postgresql+asyncpg://TEST_USER:TEST_PASSWORD@127.0.0.1:TEST_PORT/verifai_test' \
  .venv/bin/pytest backend/tests -q -p no:cacheprovider -o addopts='' --tb=short
```

Substitute **dedicated disposable test-only** credentials, port and database name.
The example placeholders must not be used in production.

## 3. Real production frontend → backend → PostgreSQL smoke test

Location: `frontend/tests/full_stack_smoke.py`

Unlike the in-memory browser suite, this script runs the production frontend
against a real **testing-mode** FastAPI process connected to disposable PostgreSQL.
It uses the backend's native username/password authentication to create a
temporary test user. It then checks:

1. Real registration, login, and authenticated profile
2. A test-only knowledge-base document persisted in PostgreSQL
3. That same document rendered in the **production React UI**
4. A chat session created through the UI and fetched through the backend API
5. The reports page loading real API analytics
6. Authenticated data remaining retrievable after navigation

**All full-stack smoke checks passed locally.**

The test refuses to write unless `VERIFAI_E2E_ALLOW_MUTATIONS=1` is set, the
API is a dedicated loopback port other than 8000, and `/api/v1/ready`
confirms `environment=testing` and available PostgreSQL.

The test expects an existing testing-mode backend reachable by
`VERIFAI_E2E_API_URL` and a build of `frontend/dist/`, with CORS allowing
`http://127.0.0.1:4300`. Run via:

```bash
cd frontend
VERIFAI_E2E_ALLOW_MUTATIONS=1 \
VERIFAI_E2E_API_URL='http://127.0.0.1:58005/api/v1' \
npm run test:fullstack
```

**Never point this tool at your development or production backend.** The
test account and document exist only in the selected disposable test DB.
It does not call external LLM providers or exercise live Firebase OAuth.

## 4. GitHub Actions CI

New workflow: `.github/workflows/phase4-regression.yml`

It defines three independent jobs:
- **Frontend:** `npm ci`, TypeScript check, production build, isolated Chromium regression tests
- **Backend:** install locked Python requirements and run all `backend/tests` against a dedicated disposable PostgreSQL service
- **Fullstack:** build the frontend, run a testing-mode FastAPI service against another disposable PostgreSQL service, and run the real UI/backend/database smoke test

All test DB passwords in the CI workflow are **throwaway CI-only values** with
ephemeral service containers; **no user application secrets are consumed**.
CI runs on pushes to `Final` and `main`, and on pull requests targeting
those branches.

**Important:** Workflow YAML syntax and the local test scripts have been
validated. The GitHub-hosted workflow has **not been executed or proven green**
because these local changes have not been committed/pushed. The pre-existing
`.github/workflows/backend-ci.yml` also retains an unrelated static-analysis
backlog (Ruff errors), so it may still fail until that backlog is fixed.

## Remaining external checks

- Actual Firebase authentication/login/signup with an authorized test account
- Real provider credentials, paid LLM calls, model latency, and provider errors
- Live external retrieval services and production configuration
- Screenshots and accessibility checks across additional devices/browsers
- GitHub-hosted CI run after committing and pushing, with any runner-specific fixes

**No commits, pushes, production deployments or destructive database operations
were made in Phase 4.**
