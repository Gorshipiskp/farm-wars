# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — run via scripts/build-release.sh"""

import glob
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

ROOT = Path(SPECPATH).resolve().parent

datas = [
    (str(ROOT / "web" / "dist"), "web/dist"),
    (str(ROOT / "db" / "farm_wars.db"), "db"),
    (str(ROOT / "db" / "schema.sql"), "db"),
    (str(ROOT / "db" / "seed_minimal.sql"), "db"),
    (
        str(ROOT / "fixtures" / "world_state" / "minimal_world.json"),
        "fixtures/world_state",
    ),
]

binaries = []
for pattern in (
    ROOT / "engine_cpp" / "build" / "Release" / "engine_core*.pyd",
    ROOT / "engine_cpp" / "build" / "engine_core*.pyd",
):
    for path in sorted(glob.glob(str(pattern))):
        binaries.append((path, "."))

hiddenimports = (
    collect_submodules("server")
    + collect_submodules("db")
    + collect_submodules("shared")
    + collect_submodules("engine_core_stub")
    + ["engine_core"]
)

a = Analysis(
    [str(ROOT / "tools" / "release_entry.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pygame", "matplotlib", "numpy", "pandas", "PIL"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="FarmWars",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="FarmWars",
)
