#!/usr/bin/env bash
set -euo pipefail

# OttoBot — single-command dev bootstrap
# Launches Phoenix + uvicorn (FastAPI) + Vite (React frontend) in parallel.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# ── Guard: .env must exist ────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
  echo "ERROR: .env not found."
  echo "  Copy .env.example to .env and fill in keys:"
  echo "    cp .env.example .env"
  exit 1
fi

# ── Guard: virtual env must exist ────────────────────────────────────────────
if [ ! -f ".venv/bin/activate" ]; then
  echo "ERROR: Python virtual environment not found at .venv/"
  echo "  Create it first:"
  echo "    python3.12 -m venv .venv && source .venv/bin/activate && pip install -e .[dev]"
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

# ── PID tracking ─────────────────────────────────────────────────────────────
PIDS=()

cleanup() {
  echo ""
  echo "Shutting down all services..."
  for pid in "${PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
  echo "Done."
}
trap cleanup SIGINT SIGTERM EXIT

# ── Launch Phoenix tracing UI ─────────────────────────────────────────────────
echo "Starting Phoenix tracing server..."
python -m phoenix.server.main >/tmp/phoenix.log 2>&1 &
PIDS+=($!)

# ── Launch FastAPI / uvicorn ──────────────────────────────────────────────────
echo "Starting uvicorn (api.main:app) on port 8000..."
uvicorn api.main:app --reload --port 8000 >/tmp/uvicorn.log 2>&1 &
PIDS+=($!)

# ── Launch Vite dev server ────────────────────────────────────────────────────
echo "Starting Vite frontend on port 5173..."
(cd frontend && npm run dev) &
PIDS+=($!)

# ── Banner ────────────────────────────────────────────────────────────────────
sleep 1
echo ""
echo "======================================================"
echo "  OttoBot dev servers running"
echo "======================================================"
echo "  Phoenix tracing:  http://localhost:6006"
echo "  API health:       http://localhost:8000/health"
echo "  Frontend:         http://localhost:5173"
echo "======================================================"
echo ""
echo "Press Ctrl+C to stop all services."
echo ""

# ── Wait ──────────────────────────────────────────────────────────────────────
wait
