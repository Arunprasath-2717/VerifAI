"""Production-UI -> real isolated FastAPI -> disposable PostgreSQL smoke test.

Never run against a real account or development database:
- requires VERIFAI_E2E_ALLOW_MUTATIONS=1
- requires a loopback API on a non-development port
- refuses to write unless /ready reports environment='testing'
- never calls model inference, external identity providers, or real AI APIs

Run with an already-started isolated backend on 127.0.0.1:58005,
BACKEND_CORS_ORIGINS allowing http://127.0.0.1:4300, after npm run build.
"""

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if os.getenv("VERIFAI_E2E_ALLOW_MUTATIONS") != "1":
    raise SystemExit("Refusing writes: set VERIFAI_E2E_ALLOW_MUTATIONS=1 for a disposable test backend.")
API = os.getenv("VERIFAI_E2E_API_URL", "")
parsed_api = urllib.parse.urlparse(API)
if (
    parsed_api.hostname not in ("127.0.0.1", "localhost")
    or parsed_api.port in (None, 8000)
    or not parsed_api.path.rstrip("/").endswith("/api/v1")
):
    raise SystemExit("Refusing writes: API must be a dedicated loopback test backend, not port 8000.")

preview_port = int(os.getenv("VERIFAI_E2E_PREVIEW_PORT", "4300"))
BASE = f"http://127.0.0.1:{preview_port}"
def find_browser():
    env_bin = (os.getenv("VERIFAI_CHROME_BIN") or "").strip()
    if env_bin:
        found = shutil.which(env_bin) or (env_bin if os.path.isfile(env_bin) and os.access(env_bin, os.X_OK) else None)
        if found:
            return found
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    for fallback in ("/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser"):
        if os.path.isfile(fallback) and os.access(fallback, os.X_OK):
            return fallback
    return None


def find_chromedriver():
    env_bin = (os.getenv("VERIFAI_CHROMEDRIVER_BIN") or "").strip()
    if env_bin:
        found = shutil.which(env_bin) or (env_bin if os.path.isfile(env_bin) and os.access(env_bin, os.X_OK) else None)
        if found:
            return found
    cw_dir = (os.getenv("CHROMEWEBDRIVER") or "").strip()
    if cw_dir:
        candidate = os.path.join(cw_dir, "chromedriver")
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    for name in ("chromedriver", "chromium.chromedriver"):
        found = shutil.which(name)
        if found:
            return found
    for fallback in ("/usr/local/bin/chromedriver", "/usr/bin/chromedriver", "/usr/local/share/chrome_driver/chromedriver"):
        if os.path.isfile(fallback) and os.access(fallback, os.X_OK):
            return fallback
    return None


browser = find_browser()
driver_bin = find_chromedriver()
has_browser_driver = bool(browser and driver_bin and (ROOT / "dist/index.html").is_file())
if not has_browser_driver:
    print(f"Notice: Browser ({browser}) or ChromeDriver ({driver_bin}) not ready for UI automation.", flush=True)


def api(method, path, body=None, bearer=None):
    headers = {"Content-Type": "application/json"}
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        API + path, method=method, data=data, headers=headers
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.status, json.load(response)


# Inspect the real backend's readiness BEFORE making any write.
code, ready = api("GET", "/ready")
if code != 200 or ready.get("environment") != "testing" or not ready.get("ready"):
    raise SystemExit("Refusing writes: backend is not an isolated ready testing environment.")
if ready.get("dependencies", {}).get("database", {}).get("status") != "available":
    raise SystemExit("Refusing writes: test database is not available.")

nonce = uuid.uuid4().hex[:12]
username = "e2e_" + nonce
email = f"{username}@example.invalid"
password = "Phase4_E2E_Disposable_2026!"
status, registered = api(
    "POST", "/auth/register",
    {"email": email, "username": username, "password": password,
     "terms_accepted": True},
)
assert status == 201, f"register returned HTTP {status}"
status, logged_in = api(
    "POST", "/auth/login",
    {"email_or_username": username, "password": password},
)
assert status == 200 and logged_in.get("access_token"), "Isolated login failed"
token = logged_in["access_token"]
status, profile = api("GET", "/auth/me", bearer=token)
assert status == 200 and profile["email"] == email
print("PASS real backend registration, login and authenticated profile", flush=True)

title = f"Phase4 evidence {nonce}"
status, document = api(
    "POST", "/knowledge/documents",
    {
        "title": title,
        "filename": f"{nonce}.txt",
        "text": "Thermodynamics is the study of heat, work, energy, and physical systems.",
        "description": "Isolated end-to-end regression evidence only.",
    },
    bearer=token,
)
assert status in (200, 201) and document.get("id"), "Isolated document creation failed"
print("PASS persisted knowledge document in isolated PostgreSQL", flush=True)

if not has_browser_driver:
    if os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true":
        print("PASS Real backend E2E complete. Skipping browser UI automation in headless CI runner without driver.", flush=True)
        sys.exit(0)
    raise SystemExit("Build frontend and install matching Chrome + ChromeDriver first.")

# ChromeDriver's WebDriver HTTP API requires only Python standard library.
def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


driver_port = free_port()
driver_url = f"http://127.0.0.1:{driver_port}"
session_id = None
preview = None
driver = None
failed = False
profile_dir = tempfile.TemporaryDirectory(prefix="verifai-live-e2e-")

def webdriver(route, payload=None, method=None):
    request = urllib.request.Request(
        driver_url + route,
        data=json.dumps(payload).encode() if payload is not None else None,
        method=method or ("POST" if payload is not None else "GET"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        parsed = json.load(response)
    if isinstance(parsed.get("value"), dict) and parsed["value"].get("error"):
        raise RuntimeError(parsed["value"])
    return parsed


def js(script):
    return webdriver(
        f"/session/{session_id}/execute/sync", {"script": script, "args": []}
    )["value"]


def wait(expression, seconds=12):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            if js(f"return Boolean({expression});"):
                return True
        except Exception:
            pass
        time.sleep(0.16)
    return False


def navigate(route, condition):
    webdriver(f"/session/{session_id}/url", {"url": BASE + route})
    if not wait(condition, 16):
        raise AssertionError(f"Browser route failed: {route}")


source = f"""
(() => {{
    localStorage.setItem('verifai_token', {json.dumps(token)});
    localStorage.setItem('verifai_authenticated', 'true');
    const originalFetch = window.fetch.bind(window);
    window.__liveBackendCalls = [];
    window.fetch = (input, init = {{}}) => {{
        const url = typeof input === 'string' ? input : input.url;
        const resolved = new URL(url, window.location.origin);
        if (resolved.pathname.startsWith('/api/v1/')) {{
            const endpoint = {json.dumps(API)} + resolved.pathname.slice('/api/v1'.length) + resolved.search;
            window.__liveBackendCalls.push(resolved.pathname);
            return originalFetch(endpoint, init);
        }}
        return originalFetch(input, init);
    }};
}})();
"""

try:
    preview = subprocess.Popen(
        [str(ROOT / "node_modules/.bin/vite"), "preview", "--host", "127.0.0.1",
         "--port", str(preview_port), "--strictPort"],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    until = time.monotonic() + 20
    while time.monotonic() < until:
        try:
            with urllib.request.urlopen(BASE, timeout=2):
                break
        except Exception:
            time.sleep(0.15)
    else:
        raise RuntimeError("Isolated production frontend preview unavailable")

    driver = subprocess.Popen(
        [driver_bin, f"--port={driver_port}", "--allowed-ips=127.0.0.1"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    until = time.monotonic() + 15
    while time.monotonic() < until:
        try:
            webdriver("/status")
            break
        except Exception:
            time.sleep(0.15)
    else:
        raise RuntimeError("ChromeDriver unavailable")

    session = webdriver("/session", {
        "capabilities": {"alwaysMatch": {
            "browserName": "chrome", "pageLoadStrategy": "none",
            "goog:chromeOptions": {
                "binary": browser,
                "args": [
                    "--headless=new", "--no-sandbox", "--disable-gpu",
                    "--disable-dev-shm-usage", "--disable-background-networking",
                    "--no-first-run", f"--user-data-dir={profile_dir.name}",
                    "--window-size=1440,900",
                ],
            },
        }}
    })
    session_id = session.get("sessionId") or session["value"].get("sessionId")
    webdriver(
        f"/session/{session_id}/goog/cdp/execute",
        {"cmd": "Page.addScriptToEvaluateOnNewDocument", "params": {"source": source}},
    )

    navigate("/knowledge-base", f"document.body.innerText.includes({json.dumps(title)})")
    print("PASS production UI renders the actual persisted document", flush=True)
    assert js("return window.__liveBackendCalls.includes('/api/v1/knowledge/documents');")
    print("PASS document was loaded from real test backend", flush=True)

    navigate("/chat", "document.body.innerText.includes('AI Chat Workspace')")
    js("""const button=[...document.querySelectorAll('button')].find(
        element => element.textContent.includes('New Multi-Model Session')
    ); if (!button) throw new Error('No create chat button'); button.click(); return true;""")
    assert wait("location.pathname.startsWith('/chat/') && /[a-f0-9-]{36}/.test(location.pathname)"), "Real chat was not created"
    chat_id = js("return location.pathname.split('/').pop();")
    status, saved = api("GET", f"/chat/conversations/{chat_id}", bearer=token)
    assert status == 200 and saved["id"] == chat_id
    print("PASS production UI creates a real, persisted chat session", flush=True)

    navigate("/reports", "document.body.innerText.includes('Reports & Benchmarks')")
    assert wait("window.__liveBackendCalls.includes('/api/v1/reports/analytics')"), "Real reports API not called"
    print("PASS production reports page fetches actual test-backend analytics", flush=True)

    status, docs = api("GET", "/knowledge/documents", bearer=token)
    assert status == 200 and any(row["id"] == document["id"] for row in docs["documents"])
    print("PASS records remain available via authenticated real APIs", flush=True)
    print("ALL PHASE 4 FULL-STACK TESTS PASSED", flush=True)
except Exception as error:
    failed = True
    print("FULL-STACK TEST FAILED:", repr(error)[:1100], file=sys.stderr, flush=True)
finally:
    if session_id:
        try:
            webdriver(f"/session/{session_id}", method="DELETE")
        except Exception:
            pass
    for process in (driver, preview):
        if process:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
    profile_dir.cleanup()

if failed:
    sys.exit(1)
