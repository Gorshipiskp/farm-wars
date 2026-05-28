"""
Enrich client actions before engine simulate_tick.

PLACE_ON_TILE: client sends {tile_id, plant_id}; engine needs initial_health / initial_water_level.
See docs/specs/engine_cpp/002.SANYA.PLACE_ON_TILE.md
"""

import copy

from db.loader import GameContentCatalog

DEFAULT_PLANT_HEALTH = 100


def enrich_actions_for_tick(
    actions: list[dict],
    catalog: GameContentCatalog,
    tick_id: int,
) -> tuple[list[dict], list[dict]]:
    """
    Return (actions_for_engine, pre_tick_events).

    Invalid PLACE_ON_TILE (unknown plant_id) becomes CONTRACT_ERROR in pre_tick_events
    and is not passed to the engine.
    """
    enriched: list[dict] = []
    pre_events: list[dict] = []

    for action in actions:
        action_copy = copy.deepcopy(action)
        if action_copy.get("action_type") != "PLACE_ON_TILE":
            enriched.append(action_copy)
            continue

        payload = action_copy.setdefault("payload", {})
        plant_id = payload.get("plant_id")
        plant = catalog.plants.get(plant_id) if plant_id else None

        if plant is None:
            pre_events.append(_contract_error(
                tick_id,
                "MISSING_FIELD",
                f"Unknown plant_id: {plant_id}",
                "payload.plant_id",
            ))
            continue

        payload["initial_health"] = DEFAULT_PLANT_HEALTH
        payload["initial_water_level"] = plant.initial_water_level
        enriched.append(action_copy)

    return enriched, pre_events


def _contract_error(tick_id: int, code: str, message: str, field_path: str | None) -> dict:
    return {
        "contract_version": "v1",
        "event_type": "CONTRACT_ERROR",
        "server_tick": tick_id,
        "payload": {
            "error_code": code,
            "message": message,
            "field_path": field_path,
        },
    }
