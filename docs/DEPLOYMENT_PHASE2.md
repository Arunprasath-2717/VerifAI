# Phase 2: Backend readiness and deployment configuration

The Docker Compose stack has **no built-in database password or JWT signing secret**. It does not start until the required values are provided. By default the backend and PostgreSQL publish their ports only on `127.0.0.1`, and the image no longer bind-mounts the backend source directory.

## Configure the project

From the repository root on your own system:

```bash
cp .env.example .env
chmod 600 .env
openssl rand -hex 32
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Use independently generated values for `JWT_SECRET`, `POSTGRES_PASSWORD`, and `PROVIDER_CREDENTIAL_ENCRYPTION_KEY` in the **local, untracked** root `.env` file. Never commit them, paste them into chat, or include them in build arguments.

**Important:** If encrypted provider credentials already exist, **reuse your existing** `PROVIDER_CREDENTIAL_ENCRYPTION_KEY`. Replacing it without a rotation process makes those stored credentials unreadable. For PostgreSQL, use a strong URL-safe password (hex generated with `openssl rand -hex 32` is convenient) because Compose uses the password in the database connection URL.

Adjust `ENVIRONMENT`, `BACKEND_CORS_ORIGINS`, and other settings for the target installation. Use `ENVIRONMENT=production` only with production-safe configuration. Production and staging now refuse to start if their database schema cannot be initialized.

## Validate without starting the containers

```bash
docker compose config --quiet
```

The command fails if a required secret is missing. It does **not** validate the cryptographic quality of supplied values. Do not print or share the expanded Compose configuration; it contains secrets.

After deploying through your normal authorized workflow, check:

```bash
curl --fail --silent http://127.0.0.1:8000/api/v1/ready
```

`/api/v1/health` is **liveness** only, and `/api/v1/ready` is a **readiness** check that validates PostgreSQL connectivity, the database-backed knowledge storage path, and local authentication configuration. Authentication readiness does **not** perform a live Firebase/JWKS login or validate credentials against external services.

## Exposure and security

- PostgreSQL binds to `127.0.0.1:5432` by default. Set `POSTGRES_BIND_PORT` for a different host port if needed. Avoid exposing the database publicly.
- The backend binds to `127.0.0.1:8000` by default. If remote access is required, place it behind a properly configured TLS reverse proxy, and explicitly set `BACKEND_BIND_HOST` only after securing that network path.
- The Compose stack no longer bind-mounts `./backend` over installed application code. Use the local development script for hot reload, or a separate explicit dev-only override.
- `.dockerignore` excludes `.env` files from container build context, including files inside `backend/`.
- Provider credential encryption is mandatory in this Compose deployment; a missing or invalid Fernet value will prevent successful credential encryption.
- Keep the `verifai_pgdata` volume and your existing database backups. This phase does **not** migrate or delete data.

## Running backend tests safely

**Use a separate test database.** The original test fixtures could connect to the application's configured development PostgreSQL database. During the Phase 2 test run, verification rows appeared in that development database at the same time as the suite; no existing records were deleted or automatically cleaned up because they cannot safely be distinguished from user records based on timestamps alone.

To prevent this happening again, the backend pytest bootstrap now refuses to run against a configured database that is not clearly a test database. Provide `VERIFAI_TEST_DATABASE_URL` pointing to an **existing isolated** PostgreSQL database whose name begins with `test_` or ends with `_test`:

```bash
VERIFAI_TEST_DATABASE_URL='postgresql+asyncpg://TEST_USER:TEST_PASSWORD@127.0.0.1:5432/verifai_test' .venv/bin/pytest backend/tests -q
```

Replace the example placeholders locally (never commit real credentials). This command expects an existing, dedicated test database. The SQLite `:memory:` override is suitable for *hermetic unit tests only* if the required driver is installed; it is not a drop-in replacement for every integration test. The guard also allows tests to collect when no database is configured, but does not make database-dependent tests automatically work without one.

This is deployment hardening, **not** a claim that the project has undergone a complete production security audit. Network ingress, TLS, backups, credential rotation, external identity-provider behavior, and operational monitoring still require environment-specific verification.
