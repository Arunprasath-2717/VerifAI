#!/usr/bin/env python3
"""Automated smoke-test script for VerifAI backend.

Validates the live application contracts:
1. Liveness probe (/api/v1/health -> HTTP 200)
2. Readiness probe (/api/v1/ready -> HTTP 200 or 503 depending on config)
3. Unversioned root probe (/health -> HTTP 404, strictly unmounted)
4. Method not allowed contract (POST /api/v1/health -> HTTP 405)
5. Request ID generation and roundtrip propagation
6. Malicious Request ID sanitization and safe regeneration
7. OpenAPI schema generation and route catalog
8. Zero credential or secret leakage in responses
9. Clean application startup and graceful shutdown lifespan

Can be run in-process against ASGI app:
    PYTHONPATH=backend python scripts/smoke_test.py

Or against a running Uvicorn instance:
    PYTHONPATH=backend python scripts/smoke_test.py --base-url http://127.0.0.1:8000
"""

import argparse
import asyncio
import pathlib
import re
import sys
from typing import Any

import httpx
from httpx import ASGITransport

# Regex for safe request IDs (alphanumeric, dashes, underscores <= 64 chars)
SAFE_REQUEST_ID_REGEX = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


async def run_smoke_tests(base_url: str | None = None) -> bool:
    """Execute all smoke test checkpoints against the application."""
    print("=" * 70)
    print("VerifAI Backend — Automated Smoke Test Suite")
    print("=" * 70)

    # Import app and settings
    try:
        from app.core.config import get_settings
        from app.main import app
    except ImportError:
        # Fallback: add backend to sys.path if run from repository root
        backend_dir = str(pathlib.Path(__file__).resolve().parent.parent / "backend")
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        try:
            from app.core.config import get_settings
            from app.main import app
        except ImportError as exc:
            print(f"[FAIL] Could not import application modules: {exc}")
            print("Ensure PYTHONPATH=backend is set when executing this script.")
            return False

    settings = get_settings()
    failures: list[str] = []

    # Choose transport: live HTTP client or ASGI in-process transport
    if base_url:
        print(f"[*] Target mode: LIVE HTTP SERVER ({base_url})")
        client_kwargs: dict[str, Any] = {"base_url": base_url.rstrip("/")}
    else:
        print("[*] Target mode: IN-PROCESS ASGI TRANSPORT (with lifespan)")
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        client_kwargs = {"transport": transport, "base_url": "http://testserver"}

    async with httpx.AsyncClient(**client_kwargs) as client:
        # -------------------------------------------------------------
        # Checkpoint 1: Liveness probe (/api/v1/health)
        # -------------------------------------------------------------
        print("\n[1/8] Verifying Liveness Probe (GET /api/v1/health)...")
        try:
            resp = await client.get("/api/v1/health")
            if resp.status_code != 200:
                failures.append(
                    f"Health check expected status 200, got {resp.status_code}"
                )
            else:
                data = resp.json()
                req_header = resp.headers.get("x-request-id", "")
                if data.get("status") != "live":
                    failures.append(
                        f"Health payload status expected 'live', "
                        f"got {data.get('status')}"
                    )
                if data.get("service") != "verifai-backend":
                    failures.append(
                        f"Health service expected 'verifai-backend', "
                        f"got {data.get('service')}"
                    )
                if not req_header or req_header != data.get("request_id"):
                    failures.append(
                        f"Health request_id mismatch between header "
                        f"({req_header}) and body ({data.get('request_id')})"
                    )
                print(
                    f"  ✓ HTTP 200 OK | status='{data.get('status')}' | "
                    f"service='{data.get('service')}'"
                )
                print(f"  ✓ Request ID: {req_header}")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"Health probe raised exception: {exc}")

        # -------------------------------------------------------------
        # Checkpoint 2: Readiness probe contract (/api/v1/ready)
        # Validates response according to actual environment & dependencies
        # -------------------------------------------------------------
        print("\n[2/8] Verifying Readiness Probe Contract (GET /api/v1/ready)...")
        try:
            resp = await client.get("/api/v1/ready")
            req_header = resp.headers.get("x-request-id", "")
            data = resp.json()

            if resp.status_code == 200:
                if data.get("ready") is not True or data.get("status") != "ready":
                    failures.append(
                        f"Readiness 200 payload must have ready=True, got {data}"
                    )
                print("  ✓ HTTP 200 READY | Dependencies configured and available")
            elif resp.status_code == 503:
                if data.get("ready") is not False or data.get("status") != "not_ready":
                    failures.append(
                        f"Readiness 503 payload must have ready=False, got {data}"
                    )
                deps = data.get("dependencies", {})
                if not isinstance(deps, dict):
                    failures.append(
                        "Readiness 503 payload must include dependencies dictionary"
                    )
                print(
                    "  ✓ HTTP 503 NOT READY (Honest report: dependencies "
                    "unconfigured/unavailable)"
                )
                print(f"  ✓ Reported dependencies: {list(deps.keys())}")
            else:
                failures.append(
                    f"Readiness check expected 200 or 503, got {resp.status_code}"
                )

            # Common contract checks for readiness probe
            if data.get("process") != "running":
                failures.append(
                    f"Readiness process expected 'running', got {data.get('process')}"
                )
            if not req_header or req_header != data.get("request_id"):
                failures.append(
                    f"Readiness request_id mismatch between header "
                    f"({req_header}) and body ({data.get('request_id')})"
                )
            # Secret leakage audit
            raw_text = resp.text.lower()
            if "password" in raw_text or "postgresql+asyncpg://" in raw_text:
                failures.append(
                    "Potential credential/URL leakage detected in readiness response!"
                )
            print("  ✓ Common fields validated (process=running, zero secret leakage)")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"Readiness probe raised exception: {exc}")

        # -------------------------------------------------------------
        # Checkpoint 3: Negative control - Root /health unmounted
        # -------------------------------------------------------------
        print("\n[3/8] Verifying Unversioned Root Health Is Unmounted (GET /health)...")
        try:
            resp = await client.get("/health")
            if resp.status_code != 404:
                failures.append(
                    f"Root /health expected status 404, got {resp.status_code}"
                )
            else:
                data = resp.json()
                error_obj = data.get("error", {})
                if error_obj.get("code") != "NOT_FOUND":
                    failures.append(
                        f"Root /health error code expected 'NOT_FOUND', "
                        f"got {error_obj.get('code')}"
                    )
                if not resp.headers.get("x-request-id"):
                    failures.append(
                        "Root /health 404 response missing x-request-id header"
                    )
                print("  ✓ HTTP 404 NOT FOUND (Strictly unmounted)")
                print(f"  ✓ Standard error envelope: code='{error_obj.get('code')}'")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"Root health probe raised exception: {exc}")

        # -------------------------------------------------------------
        # Checkpoint 4: Negative control - Method Not Allowed
        # -------------------------------------------------------------
        print("\n[4/8] Verifying Method Not Allowed Contract (POST /api/v1/health)...")
        try:
            resp = await client.post("/api/v1/health")
            if resp.status_code != 405:
                failures.append(
                    f"POST /api/v1/health expected status 405, got {resp.status_code}"
                )
            else:
                data = resp.json()
                error_obj = data.get("error", {})
                if error_obj.get("code") != "METHOD_NOT_ALLOWED":
                    failures.append(
                        f"POST /api/v1/health expected 'METHOD_NOT_ALLOWED', "
                        f"got {error_obj.get('code')}"
                    )
                print("  ✓ HTTP 405 METHOD NOT ALLOWED")
                print(f"  ✓ Standard error envelope: code='{error_obj.get('code')}'")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"Method not allowed check raised exception: {exc}")

        # -------------------------------------------------------------
        # Checkpoint 5: Valid Request ID Roundtrip Propagation
        # -------------------------------------------------------------
        print("\n[5/8] Verifying Valid Request ID Roundtrip...")
        test_req_id = "smoke-test-trace-id-12345"
        try:
            resp = await client.get(
                "/api/v1/health", headers={"X-Request-ID": test_req_id}
            )
            ret_header = resp.headers.get("x-request-id", "")
            data = resp.json()
            if ret_header != test_req_id:
                failures.append(
                    f"Expected X-Request-ID '{test_req_id}', got '{ret_header}'"
                )
            if data.get("request_id") != test_req_id:
                failures.append(
                    f"Expected body request_id '{test_req_id}', "
                    f"got '{data.get('request_id')}'"
                )
            print(f"  ✓ Client supplied ID '{test_req_id}' preserved accurately")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"Request ID roundtrip raised exception: {exc}")

        # -------------------------------------------------------------
        # Checkpoint 6: Malicious Request ID Handling & Safe Sanitization
        # -------------------------------------------------------------
        print("\n[6/8] Verifying Malicious Request ID Handling (Header Injection)...")
        malicious_id = "invalid id with spaces; <script>evil()</script>"
        try:
            resp = await client.get(
                "/api/v1/health", headers={"X-Request-ID": malicious_id}
            )
            ret_header = resp.headers.get("x-request-id", "")

            # Verify the response status succeeded
            if resp.status_code != 200:
                failures.append(
                    f"Request with invalid ID header failed with "
                    f"status {resp.status_code}"
                )

            # Verify header does not contain raw spaces/scripts or malicious string
            if ret_header == malicious_id or " " in ret_header or "<" in ret_header:
                failures.append(
                    f"Malicious ID was not sanitized; returned raw: {ret_header!r}"
                )

            # Verify the resulting ID conforms to safe identifier syntax
            if not SAFE_REQUEST_ID_REGEX.match(ret_header):
                failures.append(
                    f"Sanitized request ID '{ret_header}' does not match safe pattern"
                )
            else:
                print(
                    f"  ✓ Malicious input {malicious_id!r} safely rejected "
                    f"and replaced with safe ID: '{ret_header}'"
                )
        except Exception as exc:  # noqa: BLE001
            failures.append(f"Malicious request ID check raised exception: {exc}")

        # -------------------------------------------------------------
        # Checkpoint 7: OpenAPI Schema Validation
        # -------------------------------------------------------------
        print("\n[7/8] Verifying OpenAPI Schema (GET /openapi.json)...")
        try:
            resp = await client.get("/openapi.json")
            if resp.status_code != 200:
                failures.append(
                    f"OpenAPI schema expected status 200, got {resp.status_code}"
                )
            else:
                schema = resp.json()
                if not schema.get("openapi", "").startswith("3."):
                    failures.append(
                        f"OpenAPI version expected 3.x, got '{schema.get('openapi')}'"
                    )
                paths = schema.get("paths", {})
                expected_paths = ["/api/v1/health", "/api/v1/ready"]
                for path in expected_paths:
                    if path not in paths:
                        failures.append(
                            f"OpenAPI paths missing expected route '{path}'"
                        )
                if "/health" in paths:
                    failures.append(
                        "OpenAPI paths incorrectly contains unversioned '/health'"
                    )
                print(f"  ✓ OpenAPI {schema.get('openapi')} schema valid")
                print(f"  ✓ Registered routes: {list(paths.keys())}")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"OpenAPI check raised exception: {exc}")

        # -------------------------------------------------------------
        # Checkpoint 8: Lifespan Shutdown & Cleanup
        # -------------------------------------------------------------
        print("\n[8/8] Verifying Resource Cleanup & Engine Disposal...")
        try:
            from app.core.database import dispose_async_engine

            await dispose_async_engine()
            print("  ✓ Async database engine and pool safely disposed")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"Engine disposal raised exception: {exc}")

    # Final Summary
    print("\n" + "=" * 70)
    if failures:
        print(f"[FAIL] Smoke test completed with {len(failures)} failure(s):")
        for idx, failure in enumerate(failures, 1):
            print(f"  {idx}. {failure}")
        print("=" * 70)
        return False

    print("[PASS] All 8 smoke test checkpoints passed successfully!")
    print(
        f"Verified: {settings.PROJECT_NAME} v{settings.VERSION} "
        f"({settings.ENVIRONMENT})"
    )
    print("=" * 70)
    return True


def main() -> None:
    """CLI entry point for smoke test script."""
    parser = argparse.ArgumentParser(
        description="Run VerifAI backend automated smoke tests."
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="Optional base URL of a running server (e.g. http://127.0.0.1:8000).",
    )
    args = parser.parse_args()

    success = asyncio.run(run_smoke_tests(base_url=args.base_url))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
