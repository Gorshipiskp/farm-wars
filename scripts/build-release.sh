#!/usr/bin/env bash
# Build portable Farm Wars for Windows (folder release/out/FarmWars/).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Farm Wars — release build"
echo "    Root: $ROOT"

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "ERROR: '$1' not found in PATH" >&2
    exit 1
  fi
}

need_cmd python
need_cmd npm

PY="${PYTHON:-python}"
if command -v py >/dev/null 2>&1; then
  PY="py"
fi

echo "==> Python deps (release)"
"$PY" -m pip install -q -r requirements-release.txt
"$PY" -m pip install -q pybind11 2>/dev/null || true

echo "==> SQLite database"
"$PY" tools/init_db.py --seed

echo "==> C++ engine (optional; stub used if this fails)"
if "$PY" tools/build_engine.py 2>/dev/null; then
  echo "    Engine: C++ module built"
else
  echo "    Engine: using Python stub (OK for play)"
fi

echo "==> Web client (npm run build)"
cd web
if [[ ! -d node_modules ]]; then
  npm ci
fi
npm run build
cd "$ROOT"

if [[ ! -f web/dist/index.html ]]; then
  echo "ERROR: web/dist/index.html missing after build" >&2
  exit 1
fi

echo "==> PyInstaller"
"$PY" -m PyInstaller release/farm_wars.spec --noconfirm --distpath release/out/dist --workpath release/out/build

OUT="$ROOT/release/out/dist/FarmWars"
if [[ ! -f "$OUT/FarmWars.exe" ]]; then
  echo "ERROR: FarmWars.exe not found in $OUT" >&2
  exit 1
fi

# Portable data folder + launchers beside exe
mkdir -p "$OUT/data"

cat > "$OUT/Play-FarmWars.bat" <<'BAT'
@echo off
cd /d "%~dp0"
set FARM_WARS_PORTABLE=1
set FARM_WARS_OPEN_BROWSER=1
start "" "FarmWars.exe"
BAT

cat > "$OUT/Play-FarmWars.sh" <<'SH'
#!/usr/bin/env bash
cd "$(dirname "$0")"
export FARM_WARS_PORTABLE=1
export FARM_WARS_OPEN_BROWSER=1
exec ./FarmWars.exe
SH
chmod +x "$OUT/Play-FarmWars.sh" 2>/dev/null || true

cat > "$OUT/README.txt" <<'TXT'
Farm Wars — portable build
==========================

1. Double-click Play-FarmWars.bat (or FarmWars.exe)
2. Browser opens at http://127.0.0.1:8765/
3. Create a match, share the join code on your LAN

Other PCs on the same Wi‑Fi: open http://YOUR_LAN_IP:8765/
(LAN IP is printed in the console window.)

Data (saves/DB): folder "data" next to this exe (portable mode).

To play without browser UI from source: bash scripts/play.sh
TXT

echo ""
echo "=============================================="
echo " DONE: $OUT"
echo " Run:  $OUT/Play-FarmWars.bat"
echo "   or: bash \"$OUT/Play-FarmWars.sh\""
echo "=============================================="
