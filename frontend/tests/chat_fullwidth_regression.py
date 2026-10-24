"""Focused, hermetic Chat Workspace width checks at desktop and mobile sizes.

Uses the established browser mock fixture without running dashboard assertions.
No live credentials or external provider requests are involved.
"""
from pathlib import Path
import subprocess
import json
import time
import sys
import base64

original = Path(__file__).with_name('browser_regression.py')
text = original.read_text()
prefix = text.split('\ntry:\n    if not (ROOT / "dist/index.html").is_file():', 1)[0]
exec(compile(prefix, str(original), "exec"), globals())

failed = False
try:
    if not (ROOT / 'dist/index.html').is_file():
        raise RuntimeError('Build frontend with npm run build first.')
    preview = subprocess.Popen(
        [str(ROOT / "node_modules/.bin/vite"), "preview",
         "--host", "127.0.0.1", "--port", str(PREVIEW_PORT), "--strictPort"],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    wait_http(BASE + '/')
    proc = subprocess.Popen(
        [driver, f"--port={PORT}", "--allowed-ips=127.0.0.1"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    wait_http(DRIVER + "/status")
    options = {
        "binary": browser,
        "args": [
            "--headless=new", "--no-sandbox", "--disable-gpu",
            "--disable-dev-shm-usage", "--disable-extensions",
            "--disable-background-networking", "--no-first-run",
            "--window-size=1920,960", f"--user-data-dir={profile_dir.name}"
        ]
    }
    session = call("/session", {
        "capabilities": {"alwaysMatch": {
            "browserName": "chrome", "pageLoadStrategy": "none",
            "goog:chromeOptions": options
        }}
    })
    sid = session.get("sessionId") or session["value"].get("sessionId")
    call(f"/session/{sid}/goog/cdp/execute", {
        "cmd": "Page.addScriptToEvaluateOnNewDocument",
        "params": {"source": JS}
    })

    for width in (1920, 1440, 1024, 768, 390):
        call(f"/session/{sid}/window/rect", {"width": width, "height": 960})
        assert wait(f"innerWidth==={width}", 4), f"Viewport did not resize: {width}"
        if width == 1920:
            assert nav("/chat", "document.querySelector('[data-testid=chat-workspace-root]')!==null"), "Chat route unavailable"
        else:
            assert wait("document.querySelector('[data-testid=chat-workspace-root]')!==null"), f"Chat missing at {width}px"
        metrics = js("""const root=document.querySelector('[data-testid=chat-workspace-root]');
          const bar=document.querySelector('.verifai-topbar-frame');
          const shell=document.querySelector('.verifai-workspace-container');
          const r=root.getBoundingClientRect(), b=bar.getBoundingClientRect(),s=shell.getBoundingClientRect();
          return {left:r.left,right:r.right,barLeft:b.left,barRight:b.right,
            shellLeft:s.left,shellRight:s.right,
            viewport:innerWidth,overflow:document.documentElement.scrollWidth-innerWidth,
            sidebar:getComputedStyle(document.querySelector('.verifai-sidebar-column')).display};""")
        print(f"CHAT_WIDTH_{width}", metrics, flush=True)
        assert abs(metrics['left']-metrics['barLeft']) < 2, f"Left gap at {width}"
        assert abs(metrics['right']-metrics['barRight']) < 2, f"Right gap at {width}"
        assert abs(metrics['right']-metrics['shellRight']) < 2, f"Nested right cap at {width}"
        assert abs(metrics['left']-metrics['shellLeft']) < 2, f"Nested left cap at {width}"
        assert metrics['overflow'] <= 2, f"Horizontal overflow at {width}: {metrics}"
        if width >= 1024:
            assert metrics['viewport']-metrics['right']<=32, f"Excessive outer right gutter at {width}"
    print("PASS chat fills app shell and avoids horizontal overflow across five breakpoints", flush=True)

    call(f"/session/{sid}/window/rect", {"width": 1440, "height": 960})
    js('document.querySelector(\'button[aria-label="Switch to Dark Theme"]\')?.click();return true;')
    assert wait("document.documentElement.classList.contains('dark')",4), "Dark mode switch failed"
    dark = js("""const r=document.querySelector('[data-testid=chat-workspace-root]').getBoundingClientRect();
       const b=document.querySelector('.verifai-topbar-frame').getBoundingClientRect();
       return {left:r.left,right:r.right,barLeft:b.left,barRight:b.right};""")
    assert abs(dark['left']-dark['barLeft'])<2 and abs(dark['right']-dark['barRight'])<2, f"Dark chat misaligned: {dark}"
    print("PASS dark theme chat width", flush=True)

except Exception as exc:
    failed=True
    print('FAIL targeted chat width:',repr(exc),file=sys.stderr,flush=True)
finally:
    if sid:
        try:
            call(f"/session/{sid}",method="DELETE")
        except Exception:
            pass
    for owned in (proc,preview):
        if owned:
            owned.terminate()
            try: owned.wait(timeout=3)
            except subprocess.TimeoutExpired:
                owned.kill()
                owned.wait()
    profile_dir.cleanup()

if failed:
    sys.exit(1)
