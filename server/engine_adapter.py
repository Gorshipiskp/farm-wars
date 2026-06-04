"""Resolve engine_core C++ module or Python stub for simulate_tick."""

import sys

from shared.paths import prepend_engine_search_paths

prepend_engine_search_paths()


def get_simulate_tick():
    try:
        import engine_core

        return engine_core.simulate_tick, "engine_core"
    except ImportError:
        from engine_core_stub.stub import simulate_tick

        return simulate_tick, "engine_core_stub"
