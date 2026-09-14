"""Tests for graceful shutdown handling under SIGTERM and SIGINT."""

import signal
import subprocess
import sys
import time
import pytest


def _run_server_and_signal(sig: signal.Signals, port: int) -> subprocess.CompletedProcess:
    """Helper to spin up uvicorn server in a subprocess and send a termination signal."""
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    started = False
    start_time = time.time()
    startup_output = []

    # Wait up to 5 seconds for application startup
    while time.time() - start_time < 5.0:
        line = proc.stdout.readline()
        if not line:
            break
        startup_output.append(line)
        if "Application startup complete" in line or "Uvicorn running" in line:
            started = True
            break

    assert started, f"Server failed to start in time. Output:\n{''.join(startup_output)}"

    # Send termination signal
    proc.send_signal(sig)

    # Read remaining shutdown output
    shutdown_output = []
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        shutdown_output.append(line)

    proc.wait(timeout=5)
    all_output = "".join(startup_output + shutdown_output)
    return proc.returncode, all_output


def test_graceful_shutdown_sigterm():
    """Verify uvicorn shuts down gracefully and runs lifespan cleanup upon SIGTERM."""
    returncode, output = _run_server_and_signal(signal.SIGTERM, port=8871)
    # On SIGTERM, standard UNIX returncode is -15 or 0
    assert returncode in (0, -signal.SIGTERM, 15)
    assert "Waiting for application shutdown" in output or "Graceful shutdown completed" in output
    assert "Application shutdown complete" in output or "Finished server process" in output


def test_graceful_shutdown_sigint():
    """Verify uvicorn shuts down gracefully and runs lifespan cleanup upon SIGINT."""
    returncode, output = _run_server_and_signal(signal.SIGINT, port=8872)
    # On SIGINT (CTRL+C), standard returncode is 0 or -2
    assert returncode in (0, -signal.SIGINT, 2)
    assert "Waiting for application shutdown" in output or "Graceful shutdown completed" in output
    assert "Application shutdown complete" in output or "Finished server process" in output
