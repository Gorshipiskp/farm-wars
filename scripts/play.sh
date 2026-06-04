#!/usr/bin/env bash
# Run Farm Wars from source (no PyInstaller): server + built web UI in browser.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PY="${PYTHON:-python}"
if command -v py >/dev/null 2>&1; then
  PY="py"
fi

echo "==> Farm Wars — play from source"

if [[ ! -f db/farm_wars.db ]]; then
  echo "==> Creating database"
  "$PY" tools/init_db.py --seed
fi

if [[ ! -f web/dist/index.html ]]; then
  if ! command -v npm >/dev/null 2>&1; then
    echo "ERROR: web/dist missing and npm not installed." >&2
    echo "Install Node.js or run: cd web && npm run build" >&2
    exit 1
  fi
  echo "==> Building web client (first time)"
  (cd web && npm ci && npm run build)
fi

export FARM_WARS_OPEN_BROWSER=1
export FARM_WARS_HOST="${FARM_WARS_HOST:-0.0.0.0}"
export FARM_WARS_PORT="${FARM_WARS_PORT:-8765}"

echo "==> Starting server (Ctrl+C to stop)"
echo "    Local: http://127.0.0.1:${FARM_WARS_PORT}/"
exec "$PY" -m server
