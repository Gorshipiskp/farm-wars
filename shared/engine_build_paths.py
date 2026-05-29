"""
Locate built engine_core extension (.pyd / .so) for import.

MSVC (Windows): engine_cpp/build/Release/
GCC / Ninja single-config: engine_cpp/build/
"""

from __future__ import annotations

import glob
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def engine_build_dirs(root: str | None = None) -> list[str]:
    """Directories to prepend to sys.path when searching for engine_core."""
    base = root or ROOT
    build = os.path.join(base, "engine_cpp", "build")
    dirs = [
        os.path.join(build, "Release"),
        os.path.join(build, "Debug"),
        build,
    ]
    seen: set[str] = set()
    out: list[str] = []
    for d in dirs:
        if os.path.isdir(d) and d not in seen:
            seen.add(d)
            out.append(d)
    return out


def find_engine_module_file(root: str | None = None) -> str | None:
    """Return path to engine_core*.pyd or .so if present."""
    base = root or ROOT
    patterns = [
        os.path.join(base, "engine_cpp", "build", "Release", "engine_core*.pyd"),
        os.path.join(base, "engine_cpp", "build", "engine_core*.pyd"),
        os.path.join(base, "engine_cpp", "build", "engine_core*.so"),
        os.path.join(base, "engine_cpp", "build", "Release", "engine_core*.so"),
    ]
    for pattern in patterns:
        matches = sorted(glob.glob(pattern))
        if matches:
            return matches[0]
    return None


def ensure_engine_on_syspath(root: str | None = None) -> str | None:
    """Add build dirs to sys.path. Returns directory containing the module file, if any."""
    for d in engine_build_dirs(root):
        if d not in sys.path:
            sys.path.insert(0, d)
    path = find_engine_module_file(root)
    if path:
        return os.path.dirname(path)
    return None
