"""
PyInstaller entry point: Farm Wars server + bundled web UI.

Built by: bash scripts/build-release.sh
"""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from server.main import run

if __name__ == "__main__":
    raise SystemExit(run())
