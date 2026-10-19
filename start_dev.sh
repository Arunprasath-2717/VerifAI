#!/usr/bin/env bash
# ==============================================================================
# VerifAI — Local Fullstack Dev Services Launcher
# Ensures Postgres (5432) and FastAPI Backend (8000) are healthy and active.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== VerifAI Services Initialization ==="

# 1. Check / Start PostgreSQL container
if ! docker ps --format '{{.Names}}' | grep -q 'verifai-postgres'; then
  echo "[+] Starting verifai-postgres container on port 5432..."
  docker compose up -d db
  sleep 3
else
  echo "[✓] PostgreSQL container is running on port 5432."
fi

# 2. Check / Start FastAPI backend on port 8000
if ! lsof -i :8000 >/dev/null 2>&1 && ! curl -s http://localhost:8000/api/v1/health >/dev/null 2>&1; then
  echo "[+] Launching FastAPI backend on http://localhost:8000..."
  nohup "$SCRIPT_DIR/.venv/bin/python" -m uvicorn app.main:app --app-dir "$SCRIPT_DIR/backend" --host 0.0.0.0 --port 8000 > /tmp/verifai_backend.log 2>&1 &
  sleep 2
else
  echo "[✓] FastAPI backend is already active on port 8000."
fi

# 3. Verify health
echo "[+] Performing health checks..."
if curl -s http://localhost:8000/api/v1/health | grep -q '"status":"live"'; then
  echo "[✓] Backend health verified: http://localhost:8000"
else
  echo "[!] Warning: Backend health check did not return expected response."
fi

# 4. Check / Start Frontend dev server on port 3000
if ! lsof -i :3000 >/dev/null 2>&1 && ! curl -s http://localhost:3000 >/dev/null 2>&1; then
  echo "[+] Launching Frontend dev server on http://localhost:3000..."
  (cd "$SCRIPT_DIR/frontend" && nohup npm run dev > /tmp/verifai_frontend.log 2>&1 &)
  sleep 3
fi

if curl -s http://localhost:3000 >/dev/null 2>&1; then
  echo "[✓] Frontend server active: http://localhost:3000"
  if curl -s http://localhost:3000/api/v1/health | grep -q '"status":"live"'; then
    echo "[✓] Vite proxy forward verified: http://localhost:3000/api/v1/health -> 200 OK"
  fi
else
  echo "[!] Warning: Frontend dev server failed to respond on http://localhost:3000."
fi

echo "=== VerifAI Services Ready ==="
