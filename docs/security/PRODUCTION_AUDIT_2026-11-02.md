# VerifAI engineering audit — 2 November 2026

## Scope and evidence

Repository: `Arunprasath-2717/VerifAI`; working branch `Final`. This is a release **candidate audit**, not a guarantee of absence of all defects or a certification of a deployed production environment. Previously existing changes in the same working tree were preserved.

Review included backend application and tests, authorization and owner scoping, Firebase and local account provisioning, multi-judge verification and bounded concurrency, token budgets, persistent knowledge storage, benchmark provenance, frontend browser smoke coverage, extension permissions, supply-chain dependencies, database migrations, and CI pipeline. Automated tests and tooling substantially supplement but do not replace a line-by-line human review of every method and runtime path.

## Confirmed fixes

| Area | Defect / failure mode | Correction |
|---|---|---|
| Auth — Firebase direct JWT | Raw Firebase bearer token could auto-create a local user and skip mandatory terms acceptance | Refuse raw-token enrollment; require consent-checked `/auth/firebase` exchange, and recheck current consent for direct JWT access |
| Auth — subject handling | Firebase `sub` shaped like a UUID could resolve as an unrelated internal user ID | Always derive provider-scoped UUIDv5 for Firebase subjects |
| Auth — account linking | Matching email automatically returned unrelated existing local account (potential unauthorized access) | Refuse collision; explicit future account-linking protocol required |
| Auth — registration durability | Account and consent records committed separately, potentially leaving an orphaned user on consent persistence failure | Flush both records and commit atomically; roll back entire transaction on error |
| Verification concurrency | Claims were sequential despite bounded-concurrency setting | Bounded asynchronous processing where no shared database session is used; preserve response and audit ordering |
| Token budgets | Non-atomic `can_spend` then `reserve` path could fail under parallel calls | Atomic reservation with safe unavailable-judge fallback on exhaustion |
| Knowledge base quotas | Old process-local ephemeral quota test did not match durable DB implementation | Enforce per-owner persistent byte cap in SQL and serialize PostgreSQL concurrent writes by advisory transaction lock |
| Legal consent | SQLite roundtrips could yield naive timestamps | Normalize API consent timestamp to UTC |
| Claim classification / evidence | Ambiguous numeric/year comparisons and geographic superlative routing yielded wrong or misleading expectations | Conservative abstention for ambiguous claims; factual routing for measurable superlatives; regression coverage |
| Benchmark integrity | Check incorrectly assumed weighted upstream overall scores must match an unweighted mean | Source-weighted test coverage and bounded source-score validation |
| Frontend security tests | TypeScript test import failed under Node runner; tests omitted from CI | Explicit TypeScript extension and automated CI security test target |
| Dependency security | npm advisories including transitive gRPC; `certifi` trust-store vulnerability | Updated lockfiles, transitive gRPC override and pinned fixed `certifi`; confirmed repeat audits |
| Static typing | Six mypy errors across benchmark, provider discovery and chat service | Corrected type annotations/normalization; zero mypy errors across 128 backend source files |
| CI completeness | Core workflow ran smoke subset without full backend suite or type/security gates | Full hermetic backend suite, mypy, frontend security tests, npm audit, and SQLite driver pinned in dev dependencies |
| HTTP compatibility | Deprecated HTTP status constant emitted warnings | Migrated application usage to HTTP 422 Unprocessable Content constant |
| Isolated tests | Ingestion fixture accessed a fresh database before startup initialized schema | Enter TestClient lifespan explicitly and release it reliably; test independently after database tests |
| Security scan hygiene | Silent cleanup and false-positive credential flags in Bandit | Log cleanup failures; document legitimate OAuth bearer and Firebase-only password sentinel exceptions |

## Verification commands

- `ruff check backend scripts benchmark`
- `ruff format --check backend scripts benchmark`
- `mypy backend/app --follow-imports=silent --ignore-missing-imports`
- `python -m compileall -q backend`
- `python -m pytest -q backend/tests` with isolated file-backed SQLite and isolated PostgreSQL test database
- `python -m pytest -q benchmark/tests` and `python scripts/benchmark_tool.py validate`
- `npm ci --legacy-peer-deps`, `npm run lint`, `npm run build`, `npm run test:security`, `npm run test:smoke`, `npm run test:browser`
- `npm audit --json`, `pip-audit --local`, `bandit -r backend/app`
- `alembic -c alembic.ini upgrade head` on isolated PostgreSQL 16 container

## Verified outcomes

- Python 3.14 SQLite full backend run (after auth hardening): **1,412 passed; 1 PostgreSQL-specific skipped; 0 failed**.
- Python 3.12 isolated clean-container backend run: **1,412 passed; 1 PostgreSQL-specific skipped; 0 failed** (read-only repository caused one harmless pytest cache warning).
- Python 3.14 PostgreSQL full backend run (after final cleanup and security checks): **1,413 passed; 0 failed; 1 external Starlette deprecation warning**.
- Focused tests after final HTTP status update: **77 passed, 0 failed**.
- Independent ingestion/database regression after correcting TestClient lifespan: **23 passed, 0 failed**.
- Benchmark tests: **61 passed**; dataset validation **100 cases valid**.
- Frontend: locked install, TypeScript, production build, security, smoke, Chromium browser integration: **passed**.
- Node 22 security test compatibility: **3 passed**.
- Ruff, format, compile, pip dependency consistency, Git whitespace and mypy: **passed**.
- npm and Python dependency vulnerability scans: **0 currently known vulnerabilities in the scanned environment**.
- Bandit: **0 findings** on final scan after improving cleanup logging and documenting three legitimate B106 false positives (`token_type="bearer"` and Firebase-only empty password). This is not proof of zero security risk.
- Source-pattern scan: only credential-shaped strings in test fixtures; no matching patterns in scanned production source. This is not exhaustive secret discovery.

## Outstanding validation and cautions

1. Runtime checks have been performed with test credentials/mocks. Real third-party providers, quota exhaustion behavior on production accounts, and external production configuration have not been exercised end-to-end.
2. PostgreSQL upgrade passed from an empty isolated schema. Migration with the user's actual historical production data, backup/restore rehearsal, and rollback strategy remain unverified.
3. Browser regression uses intercepted/mock API calls. Functional full-stack tests use isolated databases; neither substitutes for live deployment and operational monitoring.
4. Automatic linking of an existing password account to a Firebase identity is intentionally disabled to prevent takeover; a verified, authenticated linking flow must be designed separately if that product feature is desired.
5. The latest PostgreSQL full-suite run emitted **one external Starlette/HTTPX deprecation warning**; mock-coroutine and application HTTP 422 deprecations were eliminated from that run. SQLite event-loop teardown warnings can still appear in non-production SQLite tests. These are not zero-warning runs.
6. Performance and concurrency under real traffic, penetration testing, external secret-manager configuration, cloud health checks, and real disaster recovery are still outstanding. GitHub-hosted CI remains an independent approval gate.
7. Other agents can still find defects. A finite test suite cannot establish a bound such as “fewer than three possible errors.”

## Release gate

Do not claim production certification or merge solely on these local runs. Push reviewed changes as a pull request and require clean remote CI and a production-like staged rollout, with verified auth, migrations, backups, provider integration, and alerts. The report should be updated with final rerun totals and PR/CI links when available.

## GitHub Actions follow-up — CI environment isolation

The first pushed audit commit (`c0b95db`) triggered GitHub Actions run 41342582002. The Node 22 frontend job passed, but the Python 3.12 backend job failed in the isolated readiness success test (`test_readiness_probe_database_available_mocked`), preventing the full suite from starting. The GitHub runner had Firebase enabled by default but did not provide `FIREBASE_PROJECT_ID`; the readiness endpoint correctly and safely returned HTTP 503. The test had incorrectly assumed a fully configured identity provider. The test now supplies its own explicit, test-only auth configuration and requires no real Firebase project for its successful-readiness case, while separate negative tests retain the 503 configuration guard. The exact CI environment failure was reproduced locally and the targeted 21-test database/health group passed after correction. Remote CI on the updated commit remains the final acceptance gate.
