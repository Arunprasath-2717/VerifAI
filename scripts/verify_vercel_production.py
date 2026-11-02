#!/usr/bin/env python3
"""Read-only smoke checks for a deployed VerifAI production URL.

Usage: python3 scripts/verify_vercel_production.py https://verifai-mauve.vercel.app
No login credentials or secrets are sent. Exits nonzero on deployment failures.
"""

import argparse
import json
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


def fetch(base: str, path: str) -> tuple[int, str, bytes]:
    request = Request(
        urljoin(base.rstrip("/") + "/", path.lstrip("/")),
        headers={"User-Agent": "VerifAI-Deployment-Smoke/1.0"},
    )
    try:
        with urlopen(request, timeout=15) as response:
            return (
                response.status,
                response.headers.get("Content-Type", ""),
                response.read(3_000_000),
            )
    except HTTPError as exc:
        return exc.code, exc.headers.get("Content-Type", ""), exc.read(1000)


def run(base: str) -> int:
    failed = False
    for path, expected, mime in [
        ("/", 200, "text/html"),
        ("/login", 200, "text/html"),
        ("/signup", 200, "text/html"),
        ("/api/v1/health", 200, "application/json"),
        ("/api/v1/auth/me", 401, "application/json"),
    ]:
        try:
            status, content_type, body = fetch(base, path)
            ok = status == expected and mime in content_type
            if ok and path == "/api/v1/health":
                ok = json.loads(body).get("status") == "live"
            if ok and path in ("/", "/login"):
                ok = b'<div id="root"' in body
            print(f"{'PASS' if ok else 'FAIL'} {path}: HTTP {status}, {content_type}")
            failed |= not ok
        except (URLError, TimeoutError, ValueError) as exc:
            print(f"FAIL {path}: {type(exc).__name__}")
            failed = True

    try:
        status, content_type, body = fetch(base, "/")
        scripts = re.findall(rb'src="(/assets/[^" ]+\.js)"', body)
        if not scripts:
            raise ValueError("no built JS entrypoints found")
        for script in scripts:
            path = script.decode("ascii")
            code, mime, _ = fetch(base, path)
            ok = code == 200 and "javascript" in mime
            print(f"{'PASS' if ok else 'FAIL'} {path}: HTTP {code}")
            failed |= not ok
    except (URLError, TimeoutError, ValueError) as exc:
        print(f"FAIL bundled assets: {type(exc).__name__}")
        failed = True

    print("DEPLOYMENT " + ("FAILED" if failed else "PASSED"))
    return int(failed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "url", help="Deployed VerifAI origin, e.g. https://verifai-mauve.vercel.app"
    )
    args = parser.parse_args()
    if not args.url.startswith(("https://", "http://")):
        parser.error("expected an absolute http(s) URL")
    sys.exit(run(args.url))
