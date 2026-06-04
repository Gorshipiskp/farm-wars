"""
Resolve project paths for development and PyInstaller bundles.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def bundle_dir() -> Path:
    """Read-only bundled assets (PyInstaller _MEIPASS or repo root)."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parents[1]


def install_dir() -> Path:
    """Directory beside the executable (one-folder) or repo root in dev."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def user_data_dir() -> Path:
    if os.environ.get("FARM_WARS_PORTABLE", "").strip() in ("1", "true", "yes"):
        path = install_dir() / "data"
    elif os.name == "nt":
        base = os.environ.get("LOCALAPPDATA")
        path = Path(base) / "FarmWars" if base else Path.home() / "FarmWars"
    else:
        path = Path.home() / ".local" / "share" / "farm-wars"
    path.mkdir(parents=True, exist_ok=True)
    return path


def repo_db_path() -> Path:
    return Path(__file__).resolve().parents[1] / "db" / "farm_wars.db"


def default_db_path() -> str:
    explicit = os.environ.get("FARM_WARS_DB_PATH", "").strip()
    if explicit:
        return explicit
    if not is_frozen():
        dev_db = repo_db_path()
        if dev_db.is_file():
            return str(dev_db)
    return str(user_data_dir() / "farm_wars.db")


def bundled_db_path() -> Path:
    return bundle_dir() / "db" / "farm_wars.db"


def schema_path() -> Path:
    return bundle_dir() / "db" / "schema.sql"


def seed_path() -> Path:
    return bundle_dir() / "db" / "seed_minimal.sql"


def web_dist_dir() -> Path | None:
    for base in (bundle_dir(), install_dir()):
        dist = base / "web" / "dist"
        if dist.is_dir() and (dist / "index.html").is_file():
            return dist
    return None


def fixture_world_path() -> Path:
    return bundle_dir() / "fixtures" / "world_state" / "minimal_world.json"


def _create_db_from_sql(target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()
    conn = sqlite3.connect(target)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(schema_path().read_text(encoding="utf-8"))
        seed = seed_path()
        if seed.is_file():
            conn.executescript(seed.read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()


def ensure_user_db() -> str:
    """Copy or create SQLite DB in user data; return path string."""
    db_path = Path(default_db_path())
    if db_path.is_file():
        return str(db_path)

    bundled = bundled_db_path()
    if bundled.is_file():
        shutil.copy2(bundled, db_path)
        return str(db_path)

    if schema_path().is_file():
        _create_db_from_sql(db_path)
        return str(db_path)

    raise FileNotFoundError(
        "Database not found. Run: py tools/init_db.py --seed "
        "or reinstall Farm Wars."
    )


def prepend_engine_search_paths() -> None:
    """Help import engine_core.pyd next to the exe or in engine_cpp/build."""
    from shared.engine_build_paths import ensure_engine_on_syspath

    if is_frozen():
        exe_dir = str(install_dir())
        if exe_dir not in sys.path:
            sys.path.insert(0, exe_dir)
    ensure_engine_on_syspath(str(install_dir() if is_frozen() else bundle_dir()))
