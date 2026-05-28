"""
Enrich client actions before engine simulate_tick.

PLACE_ON_TILE: docs/specs/engine_cpp/002.SANYA.PLACE_ON_TILE.md
START_RECIPE: docs/specs/gameplay/003.NIKITA.PLAYABLE_FARM_LOOP_V2.md
"""

import copy
import logging

from db.loader import GameContentCatalog

log = logging.getLogger("farm_wars.server.enricher")

DEFAULT_PLANT_HEALTH = 100


def enrich_actions_for_tick(
    actions: list[dict],
    world_state: dict,
    catalog: GameContentCatalog,
    tick_id: int,
) -> tuple[list[dict], list[dict]]:
    """
    Return (actions_for_engine, pre_tick_events).
    Invalid actions are not passed to the engine; events describe the failure.
    """
    enriched: list[dict] = []
    pre_events: list[dict] = []

    for action in actions:
        action_copy = copy.deepcopy(action)
        action_type = action_copy.get("action_type")

        if action_type == "PLACE_ON_TILE":
            event = _enrich_place_on_tile(action_copy, catalog, tick_id)
            if event is not None:
                pre_events.append(event)
                continue
            enriched.append(action_copy)

        elif action_type == "START_RECIPE":
            event = _enrich_start_recipe(action_copy, world_state, catalog, tick_id)
            if event is not None:
                pre_events.append(event)
                continue
            enriched.append(action_copy)

        elif action_type in ("BUY_PRODUCT", "HARVEST_PLANT"):
            log.error(
                "%s reached enricher (should be server-only): %s",
                action_type,
                action_copy.get("payload"),
            )
            pre_events.append({
                "contract_version": "v1",
                "event_type": "CONTRACT_ERROR",
                "server_tick": tick_id,
                "payload": {
                    "error_code": "INVALID_TYPE",
                    "message": f"{action_type} is server-only, not an engine action",
                    "field_path": "action_type",
                },
            })
        else:
            enriched.append(action_copy)

    return enriched, pre_events


def _enrich_place_on_tile(action: dict, catalog: GameContentCatalog, tick_id: int) -> dict | None:
    payload = action.setdefault("payload", {})
    plant_id = payload.get("plant_id")
    plant = catalog.plants.get(plant_id) if plant_id else None

    if plant is None:
        return _contract_error(
            tick_id, "MISSING_FIELD", f"Unknown plant_id: {plant_id}", "payload.plant_id"
        )

    payload["initial_health"] = DEFAULT_PLANT_HEALTH
    payload["initial_water_level"] = plant.initial_water_level
    return None


def _enrich_start_recipe(
    action: dict,
    world_state: dict,
    catalog: GameContentCatalog,
    tick_id: int,
) -> dict | None:
    payload = action.setdefault("payload", {})
    factory_id = payload.get("factory_id")
    recipe_id = payload.get("recipe_id")

    if not factory_id or not recipe_id:
        return _contract_error(
            tick_id, "MISSING_FIELD", "factory_id and recipe_id required", "payload"
        )

    recipe = catalog.get_recipe(recipe_id)
    if recipe is None:
        return _recipe_rejected(
            tick_id, action["player_id"], factory_id, recipe_id, "UNKNOWN_RECIPE"
        )

    factory = _find_factory(world_state, factory_id)
    if factory is None:
        return _contract_error(tick_id, "MISSING_FIELD", f"Factory not found: {factory_id}", "payload.factory_id")

    if factory.get("factory_type") != recipe.building_type:
        return _recipe_rejected(
            tick_id,
            action["player_id"],
            factory_id,
            recipe_id,
            "WRONG_BUILDING_TYPE",
        )

    player = _find_player(world_state, action["player_id"])
    if player is None:
        return _contract_error(
            tick_id, "MISSING_FIELD", f"Player not found: {action['player_id']}", "player_id"
        )

    if not _consume_ingredients(player, recipe):
        return _recipe_rejected(
            tick_id,
            action["player_id"],
            factory_id,
            recipe_id,
            "NOT_ENOUGH_INGREDIENTS",
        )

    payload["duration_sec"] = recipe.production_time_sec
    return None


def _find_player(world_state: dict, player_id: str) -> dict | None:
    for player in world_state.get("players", []):
        if player.get("player_id") == player_id:
            return player
    return None


def _consume_ingredients(player: dict, recipe) -> bool:
    """Deduct recipe ingredients if player has enough. Returns False if not."""
    inventory = player.get("inventory", [])
    amounts = {i["product_id"]: i["amount"] for i in inventory}
    for ing in recipe.ingredients:
        if amounts.get(ing.product_id, 0) < ing.amount:
            return False
    for ing in recipe.ingredients:
        remaining = amounts[ing.product_id] - ing.amount
        amounts[ing.product_id] = remaining
    new_inv = []
    for product_id, amount in amounts.items():
        if amount > 0:
            new_inv.append({"product_id": product_id, "amount": amount})
    player["inventory"] = new_inv
    return True


def _find_factory(world_state: dict, factory_id: str) -> dict | None:
    for factory in world_state.get("factories", []):
        if factory.get("factory_id") == factory_id:
            return factory
    return None


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


def _recipe_rejected(
    tick_id: int,
    player_id: str,
    factory_id: str,
    recipe_id: str,
    reason: str,
) -> dict:
    return {
        "contract_version": "v1",
        "event_type": "RECIPE_REJECTED",
        "server_tick": tick_id,
        "payload": {
            "player_id": player_id,
            "factory_id": factory_id,
            "recipe_id": recipe_id,
            "reason": reason,
        },
    }
