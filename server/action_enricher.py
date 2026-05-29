"""
Enrich client actions before engine simulate_tick.

PLACE_ON_TILE: docs/specs/engine_cpp/002.SANYA.PLACE_ON_TILE.md
START_RECIPE: docs/specs/gameplay/003.NIKITA.PLAYABLE_FARM_LOOP_V2.md
"""

import copy
import logging

from db.loader import GameContentCatalog
from server.world_util import (
    consume_product,
    contract_error,
    find_player,
    find_tile,
    make_event,
)

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

        elif action_type == "FEED_ANIMAL":
            event = _enrich_feed_animal(action_copy, world_state, catalog, tick_id)
            if event is not None:
                pre_events.append(event)
                continue
            enriched.append(action_copy)

        elif action_type in ("BUY_PRODUCT", "BUY_ANIMAL", "APPLY_SABOTAGE"):
            log.error(
                "%s reached enricher (should be server-only): %s",
                action_type,
                action_copy.get("payload"),
            )
            pre_events.append(contract_error(
                tick_id,
                "INVALID_TYPE",
                f"{action_type} is server-only, not an engine action",
                "action_type",
            ))
        else:
            enriched.append(action_copy)

    return enriched, pre_events


def _enrich_place_on_tile(action: dict, catalog: GameContentCatalog, tick_id: int) -> dict | None:
    payload = action.setdefault("payload", {})
    plant_id = payload.get("plant_id")
    plant = catalog.plants.get(plant_id) if plant_id else None

    if plant is None:
        return contract_error(
            tick_id, "MISSING_FIELD", f"Unknown plant_id: {plant_id}", "payload.plant_id"
        )

    payload["initial_health"] = DEFAULT_PLANT_HEALTH
    payload["initial_water_level"] = plant.initial_water_level
    payload["growth_time_sec"] = plant.growth_time_sec
    payload["water_decay_per_tick"] = plant.water_decay_per_tick
    payload["seed_product_id"] = plant.seed_product_id
    payload["crop_product_id"] = plant.product_id
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
        return contract_error(
            tick_id, "MISSING_FIELD", "factory_id and recipe_id required", "payload"
        )

    recipe = catalog.get_recipe(recipe_id)
    if recipe is None:
        return _recipe_rejected(
            tick_id, action["player_id"], factory_id, recipe_id, "UNKNOWN_RECIPE"
        )

    factory = _find_factory(world_state, factory_id)
    if factory is None:
        return contract_error(tick_id, "MISSING_FIELD", f"Factory not found: {factory_id}", "payload.factory_id")

    if factory.get("factory_type") != recipe.building_type:
        return _recipe_rejected(
            tick_id,
            action["player_id"],
            factory_id,
            recipe_id,
            "WRONG_BUILDING_TYPE",
        )

    player = find_player(world_state, action["player_id"])
    if player is None:
        return contract_error(
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

    if factory.get("active_recipe_id"):
        queue = factory.setdefault("queue", [])
        queue.append({
            "recipe_id": recipe_id,
            "duration_sec": recipe.production_time_sec,
        })
        return make_event(tick_id, "RECIPE_QUEUED", {
            "player_id": action["player_id"],
            "factory_id": factory_id,
            "recipe_id": recipe_id,
        })

    payload["duration_sec"] = recipe.production_time_sec
    payload["output_product_id"] = recipe.output_product_id
    return None


def _enrich_feed_animal(
    action: dict,
    world_state: dict,
    catalog: GameContentCatalog,
    tick_id: int,
) -> dict | None:
    payload = action.setdefault("payload", {})
    tile_id = payload.get("tile_id")
    player_id = action.get("player_id")

    tile = find_tile(world_state, tile_id)
    if tile is None:
        return _feed_failed(tick_id, player_id, tile_id, "UNKNOWN_TILE")

    if tile.get("owner_player_id") != player_id:
        return _feed_failed(tick_id, player_id, tile_id, "NOT_OWNER")

    if tile.get("zone_type") != "ANIMAL":
        return _feed_failed(tick_id, player_id, tile_id, "WRONG_ZONE")

    if tile.get("occupant_type") != "ANIMAL" or not tile.get("occupant_id"):
        return _feed_failed(tick_id, player_id, tile_id, "NO_ANIMAL")

    animal_id = tile.get("occupant_id")
    animal = catalog.animals.get(animal_id)
    if animal is None:
        return _feed_failed(tick_id, player_id, tile_id, "UNKNOWN_ANIMAL")

    feed_id = animal.feed_product_id
    if not feed_id:
        return _feed_failed(tick_id, player_id, tile_id, "NO_FEED_PRODUCT")

    player = find_player(world_state, player_id)
    if player is None:
        return contract_error(
            tick_id, "MISSING_FIELD", f"Player not found: {player_id}", "player_id"
        )

    if not consume_product(player, feed_id, 1):
        return _feed_failed(tick_id, player_id, tile_id, "NOT_ENOUGH_FEED")

    payload["animal_id"] = animal_id
    payload["production_interval_sec"] = animal.production_interval_sec
    payload["product_id"] = animal.product_id
    return None


def _feed_failed(tick_id: int, player_id: str, tile_id: str | None, reason: str) -> dict:
    return make_event(tick_id, "FEED_FAILED", {
        "player_id": player_id,
        "tile_id": tile_id,
        "reason": reason,
    })


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


def _recipe_rejected(
    tick_id: int,
    player_id: str,
    factory_id: str,
    recipe_id: str,
    reason: str,
) -> dict:
    return make_event(tick_id, "RECIPE_REJECTED", {
        "player_id": player_id,
        "factory_id": factory_id,
        "recipe_id": recipe_id,
        "reason": reason,
    })
