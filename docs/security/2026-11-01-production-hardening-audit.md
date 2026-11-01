# VerifAI — Production hardening audit and repair log

**Date:** 2026-11-01. **Environment:** Pikachu working tree.
No production migration, code commit, push, or deployment was performed.
This document records local source inspection and test evidence, not a penetration-test certification.

## Changes made

- Added frontend/src/utils/safeExternalUrl.ts and applied HTTP(S)-only validation to verification primary-source links. Invalid schemes, malformed URLs and embedded credentials are rejected.
- Replaced automatic Chrome extension content-script execution on all URLs with user-initiated injection using activeTab and scripting permissions. Authentication tokens are not passed to injected content scripts.
- Removed unused mock-only History, Reports, Audit pages and services/api/daranya.ts after confirming no application imports reference them. Live HistoryPage and ReportsPage remain.
- Removed project-specific Firebase configuration fallbacks from frontend/src/lib/firebase.ts and backend/app/core/config.py. Added frontend/.env.example. Updated mock Firebase test project identifiers.
- Corrected responsive CSS class selectors in frontend/src/pages/DashboardMocha.css.
- Updated backend/tests/test_api_boundary_matrix.py to use an authenticated test principal, preserving ingestion authorization behavior.
- Added targeted source-link and extension permission regression tests.

## Verification results

| Check | Result |
|---|---|
| Frontend TypeScript lint | PASS |
| Frontend production build | PASS |
| Frontend smoke suite | PASS: 5 checkpoints |
| Frontend/extension security regression tests | PASS: 3 |
| Backend auth, ingestion and DB-session focused tests | PASS: 50 |
| Backend API boundary matrix after fixture repair | PASS: 292 |
| Firebase and consent focused tests after config cleanup | PASS: 8 |
| Full backend suite BEFORE boundary fixture repair | 1240 passed, 162 failed; 4 warnings |

The full-suite number is not a new post-fix full-suite result. Many failures were legacy tests expecting anonymous ingestion. Further independent failures remain in authentication test isolation, BYOK/provider integration, CLI, retrieval settings, verification accuracy, leaderboard and test database schema.

## Dependency audit

npm audit --omit=dev: 9 findings (8 high, 1 moderate), notably Firebase and transitive libraries.
An attempt to plan npm audit fix was stopped by EALLOWREMOTE (registry tarball fetch denied). No dependency upgrades were applied. Do not mark vulnerabilities resolved.

## Outstanding P0 security work

1. Web session migration: server-side sessions, hashed rotating refresh tokens, revocation, secure HttpOnly cookies, CSRF checks, frontend and SSE changes.
2. Extension-specific short-lived JWT with restricted audience and scope, separate exchange endpoint and negative tests.
3. Real ingestion database migration: **not approved**. Backup and inventory 807 historic ownerless rows; rehearse restoration and migration against a copy, with explicit sign-off.
4. BYOK encryption and decryption ownership tests, secret scanning and provider key rotation. The operator must rotate keys; do not print or copy them into logs.
5. Resolve all backend suite failures, then rerun full backend and frontend browser tests.
6. Remediate dependency advisories and test real runtime paths.
7. Deploy a restrictive CSP as a frontend HTTP response header; verify actual production assets and Firebase workflows.
8. Harden provider outbound connections, SSRF redirects, AI trust boundaries and secure model orchestration.
9. Distributed rate limits, account lockouts, monitoring, incident response, encrypted backups and tested restoration.

## Constraints

- Keep production database untouched until explicit approval.
- No unrelated working tree files (classifier, semantic judging, media assets) were reverted or replaced.
- This audit is not a claim of production readiness.
- No commit, staging, push, or deployment performed.
