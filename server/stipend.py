"""
Occasional Bestiki stipend so players are not stuck at zero balance.

Runs during match ticks (see match.process_tick).
"""

from __future__ import annotations

import logging
import os
import random

from db.loader import GameContentCatalog
from server.care_costs import feed_care_cost, water_care_cost
from server.world_util import make_event

log = logging.getLogger("farm_wars.server.stipend")

def _trigger_probability() -> float:
    return float(os.environ.get("FARM_WARS_STIPEND_PROB", "0.4"))


def _stipend_amount() -> int:
    return max(1, int(os.environ.get("FARM_WARS_STIPEND_AMOUNT", "5")))


def _interval_ticks() -> int:
    from shared.game_pacing import ticks_for_real_seconds

    raw = os.environ.get("FARM_WARS_STIPEND_INTERVAL")
    if raw is not None:
        return max(1, int(raw))
    return ticks_for_real_seconds(45)


def poverty_threshold(catalog: GameContentCatalog) -> int:
    """Below this balance a player may receive a stipend."""
    raw = os.environ.get("FARM_WARS_STIPEND_POVERTY")
    if raw is not None:
        return max(1, int(raw))
    care = max(water_care_cost(catalog), feed_care_cost(catalog))
    return care + 5


def apply_stipends(
    world_state: dict,
    catalog: GameContentCatalog,
    tick_id: int,
) -> list[dict]:
    """
    Rarely grant a few Bestiki to broke players. Returns game events (may be empty).
    """
    interval = _interval_ticks()
    if interval <= 0 or tick_id <= 0 or tick_id % interval != 0:
        return []
    if random.random() > _trigger_probability():
        return []

    threshold = poverty_threshold(catalog)
    amount = _stipend_amount()
    events: list[dict] = []

    for player in world_state.get("players", []):
        money = int(player.get("money_bestiki", 0))
        if money >= threshold:
            continue
        player["money_bestiki"] = money + amount
        player_id = player.get("player_id", "")
        log.info(
            "Stipend tick=%s player=%s %s -> %s B (threshold=%s)",
            tick_id,
            player_id,
            money,
            player["money_bestiki"],
            threshold,
        )
        events.append(make_event(tick_id, "STIPEND_GRANTED", {
            "player_id": player_id,
            "amount": amount,
            "balance_after": player["money_bestiki"],
            "reason": "LOW_BALANCE",
        }))

    return events
