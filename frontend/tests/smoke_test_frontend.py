#!/usr/bin/env python3
"""Automated frontend smoke test.

Validates the production Vite build:
1. Verifies dist/index.html exists and contains necessary HTML structure and asset tags.
2. Starts the Vite preview server on an ephemeral loopback port.
3. Verifies HTTP 200 response on root route (/).
4. Verifies linked JS and CSS production bundles load successfully with correct MIME types.
5. Verifies SPA routing fallback (deep links /login, /dashboard, /verify, /reports, /models).
6. Gracefully terminates preview server.
"""

import http.client
import os
import re
import socket
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

FRONTEND_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = FRONTEND_DIR / "dist"
INDEX_HTML = DIST_DIR / "index.html"


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_build_artifacts() -> list[str]:
    print("[1/5] Checking production build artifacts...")
    if not INDEX_HTML.is_file():
        raise RuntimeError(f"dist/index.html not found at {INDEX_HTML}. Run 'npm run build' first.")
    
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert '<div id="root">' in html or '<div id="root"' in html, "Missing #root element in index.html"
    
    # Extract asset paths
    assets = re.findall(r'(?:src|href)="(/assets/[^"]+)"', html)
    assert len(assets) > 0, "No bundled assets found in index.html"
    print(f"  ✓ Build artifacts valid. Found {len(assets)} bundled references in index.html.")
    return assets


def run_smoke_test():
    print("=" * 70)
    print("VerifAI Frontend — Automated Smoke Test Suite")
    print("=" * 70)

    assets = test_build_artifacts()
    port = get_free_port()
    base_url = f"http://127.0.0.1:{port}"

    print(f"[2/5] Starting Vite preview server on port {port}...")
    preview_proc = subprocess.Popen(
        ["npx", "vite", "preview", "--port", str(port), "--host", "127.0.0.1", "--strictPort"],
        cwd=FRONTEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        # Wait for server to become responsive
        max_attempts = 30
        connected = False
        for attempt in range(max_attempts):
            try:
                with urllib.request.urlopen(f"{base_url}/", timeout=1) as resp:
                    if resp.status == 200:
                        connected = True
                        break
            except Exception:
                time.sleep(0.2)
        
        if not connected:
            stdout, stderr = preview_proc.communicate(timeout=2)
            raise RuntimeError(f"Vite preview server failed to start on {base_url}:\n{stderr}\n{stdout}")
        
        print("  ✓ Vite preview server active and responsive.")

        # Test root endpoint
        print("[3/5] Verifying root endpoint (GET /)...")
        with urllib.request.urlopen(f"{base_url}/", timeout=5) as resp:
            content_type = resp.headers.get("Content-Type", "")
            body = resp.read().decode("utf-8")
            assert resp.status == 200, f"Expected 200, got {resp.status}"
            assert "text/html" in content_type, f"Expected text/html, got {content_type}"
            assert "VerifAI" in body, "Expected title/branding 'VerifAI' in HTML"
        print("  ✓ Root route successfully returns HTML with VerifAI application mount.")

        # Test bundled assets
        print(f"[4/5] Verifying bundled static assets ({len(assets)} files)...")
        for asset in assets:
            asset_url = f"{base_url}{asset}"
            with urllib.request.urlopen(asset_url, timeout=5) as resp:
                assert resp.status == 200, f"Failed to fetch {asset_url}: status {resp.status}"
                c_type = resp.headers.get("Content-Type", "")
                if asset.endswith(".js"):
                    assert "javascript" in c_type, f"Invalid MIME for JS: {c_type}"
                elif asset.endswith(".css"):
                    assert "css" in c_type, f"Invalid MIME for CSS: {c_type}"
        print("  ✓ All bundled scripts and stylesheets loaded with correct MIME types.")

        # Test client SPA routes (Vite preview history fallback)
        print("[5/5] Verifying client SPA routing fallback...")
        routes = ["/login", "/signup", "/dashboard", "/verify", "/reports", "/models", "/terms", "/privacy"]
        for route in routes:
            with urllib.request.urlopen(f"{base_url}{route}", timeout=5) as resp:
                assert resp.status == 200, f"Route {route} failed with {resp.status}"
                body = resp.read().decode("utf-8")
                assert "root" in body, f"Route {route} did not return SPA index.html"
        print(f"  ✓ Validated {len(routes)} client routes successfully serve SPA shell.")

        print("=" * 70)
        print("[PASS] All Frontend Smoke Test checkpoints passed successfully!")
        print("=" * 70)
        return True

    finally:
        print("[*] Terminating preview server...")
        preview_proc.terminate()
        try:
            preview_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            preview_proc.kill()
        print("  ✓ Cleanup complete.")


if __name__ == "__main__":
    try:
        success = run_smoke_test()
        sys.exit(0 if success else 1)
    except Exception as exc:
        print(f"\n[FAIL] Frontend Smoke Test failed: {exc}")
        sys.exit(1)
