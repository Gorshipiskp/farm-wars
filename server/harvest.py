"""
Server-side harvest: HARVEST_PLANT without engine.

See docs/specs/gameplay/004.NIKITA.HARVEST_AND_RECIPE_INGREDIENTS.md
"""

import logging

from db.loader import GameContentCatalog
from server.plant_util import resolve_plant_id

log = logging.getLogger("farm_wars.server.harvest")

HARVEST_MIN_WATER = 50
HARVEST_YIELD = 2


def process_harvest_plant(
    action: dict,
    world_state: dict,
    catalog: GameContentCatalog,
    tick_id: int,
) -> dict:
    player_id = action.get("player_id")
    payload = action.get("payload") or {}
    tile_id = payload.get("tile_id")

    if not tile_id:
        return _failed(tick_id, player_id, tile_id, "MISSING_TILE")

    tile = _find_tile(world_state, tile_id)
    if tile is None:
        return _failed(tick_id, player_id, tile_id, "UNKNOWN_TILE")

    if tile.get("owner_player_id") != player_id:
        return _failed(tick_id, player_id, tile_id, "NOT_OWNER")

    if tile.get("occupant_type") != "PLANT":
        return _failed(tick_id, player_id, tile_id, "NO_PLANT")

    water = tile.get("water_level") or 0
    if water < HARVEST_MIN_WATER:
        return _failed(tick_id, player_id, tile_id, "NOT_READY")

    plant_id = resolve_plant_id(tile.get("occupant_id"))
    plant = catalog.plants.get(plant_id) if plant_id else None
    if plant is None:
        return _contract_error(tick_id, f"Unknown plant on tile: {plant_id}")

    player = _find_player(world_state, player_id)
    if player is None:
        return _contract_error(tick_id, f"Player not found: {player_id}")

    product_id = plant.product_id
    _add_inventory(player, product_id, HARVEST_YIELD)

    tile["occupant_type"] = "EMPTY"
    tile["occupant_id"] = None
    tile["health"] = None

    log.info(
        "HARVEST ok player=%s tile=%s product=%s x%d",
        player_id, tile_id, product_id, HARVEST_YIELD,
    )
    return {
        "contract_version": "v1",
        "event_type": "PLANT_HARVESTED",
        "server_tick": tick_id,
        "payload": {
            "player_id": player_id,
            "tile_id": tile_id,
            "product_id": product_id,
            "amount": HARVEST_YIELD,
        },
    }


def _find_tile(world_state: dict, tile_id: str) -> dict | None:
    for tile in world_state.get("map", {}).get("tiles", []):
        if tile.get("tile_id") == tile_id:
            return tile
    return None


def _find_player(world_state: dict, player_id: str) -> dict | None:
    for player in world_state.get("players", []):
        if player.get("player_id") == player_id:
            return player
    return None


def _add_inventory(player: dict, product_id: str, amount: int) -> None:
    for item in player.get("inventory", []):
        if item.get("product_id") == product_id:
            item["amount"] += amount
            return
    player.setdefault("inventory", []).append({
        "product_id": product_id,
        "amount": amount,
    })


def _failed(tick_id: int, player_id: str, tile_id: str | None, reason: str) -> dict:
    log.info("HARVEST failed player=%s tile=%s reason=%s", player_id, tile_id, reason)
    return {
        "contract_version": "v1",
        "event_type": "HARVEST_FAILED",
        "server_tick": tick_id,
        "payload": {
            "player_id": player_id,
            "tile_id": tile_id,
            "reason": reason,
        },
    }


def _contract_error(tick_id: int, message: str) -> dict:
    return {
        "contract_version": "v1",
        "event_type": "CONTRACT_ERROR",
        "server_tick": tick_id,
        "payload": {
            "error_code": "INVALID_TYPE",
            "message": message,
            "field_path": None,
        },
    }
