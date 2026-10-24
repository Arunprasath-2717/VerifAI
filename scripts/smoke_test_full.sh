#!/usr/bin/env bash
# ==============================================================================
# VerifAI — Unified Pre-Push & CI Smoke Test Suite
# Validates both Backend and Frontend contracts before pushing or making PRs.
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

echo "======================================================================"
echo "          VerifAI Fullstack Pre-Flight Smoke Verification             "
echo "======================================================================"

# Determine Python binary
if [[ -x "$REPO_ROOT/.venv/bin/python" ]]; then
  PYTHON="$REPO_ROOT/.venv/bin/python"
else
  PYTHON="python3"
fi

# 1. Backend In-Process Smoke Test
echo ""
echo "[Step 1/4] Running Backend Smoke Test..."
PYTHONPATH="$REPO_ROOT/backend" "$PYTHON" "$REPO_ROOT/scripts/smoke_test.py"
echo "✓ Backend ASGI and HTTP contracts verified."

# 2. Frontend TypeScript Check
echo ""
echo "[Step 2/4] Checking Frontend TypeScript Typing..."
(
  cd "$REPO_ROOT/frontend"
  npm run lint
)
echo "✓ Frontend type checks passed."

# 3. Frontend Production Build
echo ""
echo "[Step 3/4] Building Frontend Production Distribution..."
(
  cd "$REPO_ROOT/frontend"
  npm run build
)
echo "✓ Frontend production bundle created successfully."

# 4. Frontend Production Smoke Test
echo ""
echo "[Step 4/4] Probing Frontend Production Preview Server..."
(
  cd "$REPO_ROOT/frontend"
  "$PYTHON" "$REPO_ROOT/frontend/tests/smoke_test_frontend.py"
)
echo "✓ Frontend production preview verified."

echo ""
echo "======================================================================"
echo " [SUCCESS] Fullstack smoke tests passed! Ready for push & PR.         "
echo "======================================================================"
