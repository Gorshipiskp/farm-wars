"""
Server-side random world events: pick from DB catalog, send APPLY_EVENT to engine.

See docs/specs/server/006.NIKITA.RANDOM_EVENTS_AND_RAIN_RENAME.md
"""

import logging
import os
import random

from db.loader import GameContentCatalog, RandomEvent

log = logging.getLogger("farm_wars.server.random_events")

SYSTEM_PLAYER_ID = "__world__"

EVENT_TICK_INTERVAL = int(os.environ.get("FARM_WARS_EVENT_INTERVAL", "120"))
EVENT_TRIGGER_PROBABILITY = float(os.environ.get("FARM_WARS_EVENT_PROB", "0.2"))


def effect_type_for_engine(effect_type: str) -> str:
    """Map DB effect_type to engine event_type (FLOOD legacy → RAIN)."""
    if effect_type == "FLOOD":
        return "RAIN"
    return effect_type


def maybe_random_event_action(
    catalog: GameContentCatalog,
    tick_id: int,
) -> dict | None:
    """
    With configured interval/probability, return an APPLY_EVENT action for this tick.
    """
    if EVENT_TICK_INTERVAL <= 0 or tick_id <= 0:
        return None
    if tick_id % EVENT_TICK_INTERVAL != 0:
        return None
    if random.random() > EVENT_TRIGGER_PROBABILITY:
        return None

    events = list(catalog.random_events.values())
    if not events:
        return None

    picked: RandomEvent = random.choice(events)
    engine_type = effect_type_for_engine(picked.effect_type)
    log.info(
        "Random event tick=%s id=%s effect=%s -> engine %s",
        tick_id,
        picked.event_id,
        picked.effect_type,
        engine_type,
    )
    return {
        "contract_version": "v1",
        "player_id": SYSTEM_PLAYER_ID,
        "action_type": "APPLY_EVENT",
        "payload": {
            "event_type": engine_type,
            "event_id": picked.event_id,
            "display_name": picked.display_name,
        },
        "client_ts": 0,
    }
