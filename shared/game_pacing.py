"""
Match pacing: server tick rate and how DB durations map to real time.

World-state `*_sec` counters (e.g. `remaining_time_sec`, `growth_time_sec` on tiles)
are **simulation ticks** — decremented once per server tick.

Catalog exceptions (converted at enrich time):
- `plants.growth_time_sec` — already stored as ticks in SQLite.
- `recipes.production_time_sec` — wall-clock seconds → `ticks_for_real_seconds()`.

Default: 2 ticks per second (0.5 s interval). Example: plant growth_time_sec=360 → ~180 s real.
"""

from __future__ import annotations

import os

TICKS_PER_SECOND = int(os.environ.get("FARM_WARS_TICKS_PER_SEC", "2"))


def tick_interval_sec() -> float:
    env = os.environ.get("FARM_WARS_TICK_SEC")
    if env is not None:
        return float(env)
    return 1.0 / TICKS_PER_SECOND


def ticks_for_real_seconds(seconds: float) -> int:
    return max(1, int(seconds * TICKS_PER_SECOND))


def real_seconds_for_ticks(ticks: int) -> float:
    return ticks / TICKS_PER_SECOND


# Production runs only while hunger_ticks stays below this (fed window after FEED_ANIMAL).
ANIMAL_PRODUCTION_HUNGER_TICKS = 40

# Hunger stops all animal processing after this many ticks without feeding (~100 s wall-clock).
ANIMAL_HUNGER_LIMIT_TICKS = ticks_for_real_seconds(100)

# Stipend: see server/stipend.py (interval ~45s wall, 40% chance if balance is low).
