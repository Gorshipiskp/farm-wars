#!/usr/bin/env python3
"""
Build engine_core C++ module (CMake + pybind11).

Supports MSVC (Visual Studio) and GCC (MinGW on Windows, g++ on Linux).

Usage (from repo root):
    py tools/build_engine.py
    py tools/build_engine.py --toolchain gcc
    py tools/build_engine.py --toolchain msvc
    py tools/build_engine.py --toolchain auto

Windows + python.org: use MSVC (default). GCC/MinGW needs MSYS2 Python (same ABI).

Linux: GCC (g++) is used by default when MSVC is unavailable.
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = ROOT / "engine_cpp"
BUILD_DIR = ENGINE_DIR / "build"

IS_WINDOWS = platform.system() == "Windows"


def _run(cmd: list[str], *, env: dict | None = None, cwd: Path | None = None) -> None:
    print("+", " ".join(cmd))
    result = subprocess.run(
        cmd,
        cwd=str(cwd or ROOT),
        env=env,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def find_python() -> str:
    return sys.executable


def get_pybind11_cmake_dir(python: str) -> str:
    out = subprocess.check_output(
        [python, "-c", "import pybind11; print(pybind11.get_cmake_dir())"],
        text=True,
        cwd=ROOT,
    ).strip()
    if not out:
        raise SystemExit("pybind11 not found. Run: py -m pip install pybind11")
    return out


def find_cmake() -> str:
    """CMake from PATH, then common install locations."""
    cmake = shutil.which("cmake")
    if cmake:
        return cmake

    if IS_WINDOWS:
        candidates = [
            Path(r"C:\Program Files\CMake\bin\cmake.exe"),
            Path(r"C:\Program Files (x86)\CMake\bin\cmake.exe"),
        ]
        vs_roots = list(Path(r"C:\Program Files\Microsoft Visual Studio\2022").glob("*/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe"))
        candidates.extend(vs_roots)
        for p in candidates:
            if p.is_file():
                return str(p)

    raise SystemExit(
        "CMake not found. Install one of:\n"
        "  - CMake: https://cmake.org/download/\n"
        "  - Visual Studio 2022 with C++ and CMake component\n"
        "  - MSYS2: pacman -S mingw-w64-ucrt-x86_64-cmake mingw-w64-ucrt-x86_64-gcc"
    )


def find_gcc_toolchain() -> tuple[str, str]:
    """Return (c_compiler, cxx_compiler) executables."""
    cxx = shutil.which("g++") or shutil.which("c++")
    cc = shutil.which("gcc") or shutil.which("cc")
    if not cxx:
        raise SystemExit(
            "g++ not found in PATH.\n"
            "Windows (MSYS2): pacman -S mingw-w64-ucrt-x86_64-gcc\n"
            "Linux: sudo apt install build-essential"
        )
    if not cc:
        cc = cxx
    return cc, cxx


def cmake_path(path: str) -> str:
    """CMake-safe path (forward slashes; avoids \\U escape errors on Windows)."""
    return Path(path).resolve().as_posix()


def find_mingw_make(cxx: str) -> str | None:
    """Program for MinGW Makefiles / Unix Makefiles (mingw32-make or make)."""
    for name in ("mingw32-make", "make", "gmake"):
        found = shutil.which(name)
        if found:
            return found
    cxx_dir = Path(cxx).resolve().parent
    for name in ("mingw32-make.exe", "make.exe", "mingw32-make", "make"):
        candidate = cxx_dir / name
        if candidate.is_file():
            return str(candidate)
    return None


def find_vcvars64() -> Path | None:
    if not IS_WINDOWS:
        return None
    for edition in ("Community", "Professional", "Enterprise", "BuildTools"):
        p = Path(rf"C:\Program Files\Microsoft Visual Studio\2022\{edition}\VC\Auxiliary\Build\vcvars64.bat")
        if p.is_file():
            return p
    return None


def msvc_environment() -> dict[str, str]:
    """Run vcvars64 and merge env into os.environ copy."""
    vcvars = find_vcvars64()
    if vcvars is None:
        raise SystemExit(
            "MSVC not found. Install Visual Studio 2022 Build Tools with "
            "'Desktop development with C++', or use: py tools/build_engine.py --toolchain gcc"
        )
    print(f"MSVC environment: {vcvars}")
    cmd = f'"{vcvars}" >nul 2>&1 && set'
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit("vcvars64.bat failed")

    env = os.environ.copy()
    for line in proc.stdout.splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            env[key] = value
    return env


def detect_toolchain(requested: str) -> str:
    if requested != "auto":
        return requested

    if IS_WINDOWS:
        if find_vcvars64() is not None and shutil.which("cl"):
            return "msvc"
        if shutil.which("g++"):
            return "gcc"
        if find_vcvars64() is not None:
            return "msvc"
        return "gcc"

    if shutil.which("g++") or shutil.which("gcc"):
        return "gcc"
    if find_vcvars64() is not None:
        return "msvc"
    return "gcc"


def warn_gcc_on_windows_python() -> None:
    exe = Path(sys.executable).resolve()
    low = str(exe).lower()
    if "msys" in low or "mingw" in low or "ucrt64" in low:
        return
    print(
        "WARNING: Official Windows Python is built with MSVC.\n"
        "         MinGW g++ modules often fail to import (ABI mismatch).\n"
        "         Prefer: py tools/build_engine.py --toolchain msvc\n"
        "         Or use Python from MSYS2 when building with gcc.\n",
        file=sys.stderr,
    )


def configure_and_build(toolchain: str, cmake: str, pybind11_dir: str, python: str) -> None:
    if BUILD_DIR.exists():
        pass
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    if toolchain == "gcc":
        if IS_WINDOWS:
            warn_gcc_on_windows_python()
        cc, cxx = find_gcc_toolchain()
        env = os.environ.copy()
        ninja = shutil.which("ninja")
        if ninja:
            generator = "Ninja"
            make_program = None
        elif IS_WINDOWS:
            generator = "MinGW Makefiles"
            make_program = find_mingw_make(cxx)
            if not make_program:
                raise SystemExit(
                    "make / mingw32-make not found (required for MinGW Makefiles).\n"
                    "Install make next to g++, or: pacman -S mingw-w64-ucrt-x86_64-make"
                )
        else:
            generator = "Unix Makefiles"
            make_program = find_mingw_make(cxx)

        configure_cmd = [
            cmake,
            f"-S{ENGINE_DIR}",
            f"-B{BUILD_DIR}",
            f"-G{generator}",
            "-DCMAKE_BUILD_TYPE=Release",
            f"-DPYTHON_EXECUTABLE={cmake_path(python)}",
            f"-Dpybind11_DIR={cmake_path(pybind11_dir)}",
            f"-DCMAKE_C_COMPILER={cmake_path(cc)}",
            f"-DCMAKE_CXX_COMPILER={cmake_path(cxx)}",
        ]
        if make_program:
            configure_cmd.append(f"-DCMAKE_MAKE_PROGRAM={cmake_path(make_program)}")
            print(f"Make: {make_program}")
        _run(configure_cmd, env=env)
        _run([cmake, "--build", str(BUILD_DIR)], env=env)

    elif toolchain == "msvc":
        env = msvc_environment()
        configure_cmd = [
            cmake,
            f"-S{ENGINE_DIR}",
            f"-B{BUILD_DIR}",
            f"-DPYTHON_EXECUTABLE={cmake_path(python)}",
            f"-Dpybind11_DIR={cmake_path(pybind11_dir)}",
        ]
        _run(configure_cmd, env=env)
        _run([cmake, "--build", str(BUILD_DIR), "--config", "Release"], env=env)

    else:
        raise SystemExit(f"Unknown toolchain: {toolchain}")


def print_artifact() -> None:
    sys.path.insert(0, str(ROOT))
    from shared.engine_build_paths import find_engine_module_file

    path = find_engine_module_file(str(ROOT))
    if path:
        print(f"\n=== Build successful ===\nModule: {path}")
    else:
        print("\n=== Build finished ===\nModule not found under engine_cpp/build — check build log.")
        for sub in ("Release", ""):
            d = BUILD_DIR / sub if sub else BUILD_DIR
            if d.is_dir():
                print(f"  Contents of {d}:")
                for f in sorted(d.glob("engine_core*")):
                    print(f"    {f.name}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build engine_core C++ extension")
    parser.add_argument(
        "--toolchain",
        choices=("auto", "msvc", "gcc"),
        default="auto",
        help="Compiler toolchain (default: auto-detect)",
    )
    parser.add_argument("--clean", action="store_true", help="Remove engine_cpp/build before configure")
    args = parser.parse_args()

    print("=== Building engine_core (C++ module) ===")
    python = find_python()
    print(f"Python: {python}")

    toolchain = detect_toolchain(args.toolchain)
    print(f"Toolchain: {toolchain}")

    cmake = find_cmake()
    print(f"CMake: {cmake}")

    pybind11_dir = get_pybind11_cmake_dir(python)
    print(f"pybind11: {pybind11_dir}")

    if args.clean and BUILD_DIR.exists():
        print(f"Cleaning {BUILD_DIR}")
        shutil.rmtree(BUILD_DIR)

    configure_and_build(toolchain, cmake, pybind11_dir, python)
    print_artifact()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
