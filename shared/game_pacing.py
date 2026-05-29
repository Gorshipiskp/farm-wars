"""
Match pacing: server tick rate and how DB durations map to real time.

All `*_sec` fields in world state / catalog are **simulation ticks**, not wall-clock
seconds. One server tick advances the engine once per `FARM_WARS_TICK_SEC`.

Default: 4 ticks per second (0.25 s interval). Example: growth_time_sec=360 → ~90 s real.
"""

from __future__ import annotations

import os

TICKS_PER_SECOND = int(os.environ.get("FARM_WARS_TICKS_PER_SEC", "4"))


def tick_interval_sec() -> float:
    env = os.environ.get("FARM_WARS_TICK_SEC")
    if env is not None:
        return float(env)
    return 1.0 / TICKS_PER_SECOND


def ticks_for_real_seconds(seconds: float) -> int:
    return max(1, int(seconds * TICKS_PER_SECOND))


def real_seconds_for_ticks(ticks: int) -> float:
    return ticks / TICKS_PER_SECOND


# Hunger stops milk production after this many ticks without feeding (~100 s at 4 t/s).
ANIMAL_HUNGER_LIMIT_TICKS = ticks_for_real_seconds(100)
