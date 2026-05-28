"""Resolve engine_core C++ module or Python stub for simulate_tick."""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE_BUILD = os.path.join(ROOT, "engine_cpp", "build", "Release")

if os.path.isdir(ENGINE_BUILD) and ENGINE_BUILD not in sys.path:
    sys.path.insert(0, ENGINE_BUILD)


def get_simulate_tick():
    try:
        import engine_core

        return engine_core.simulate_tick, "engine_core"
    except ImportError:
        from engine_core_stub.stub import simulate_tick

        return simulate_tick, "engine_core_stub"
