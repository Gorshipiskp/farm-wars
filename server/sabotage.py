"""
Server-side PvP sabotage (MVP): APPLY_SABOTAGE without engine.

See docs/specs/server/008.NIKITA.PVP_SABOTAGE_MVP.md
"""

import logging

from db.loader import GameContentCatalog
from server.world_util import find_player, find_tile, make_event

log = logging.getLogger("farm_wars.server.sabotage")


def process_apply_sabotage(
    action: dict,
    world_state: dict,
    catalog: GameContentCatalog,
    tick_id: int,
) -> dict | None:
    player_id = action.get("player_id")
    payload = action.get("payload") or {}
    sabotage_id = payload.get("sabotage_id")
    target_tile_id = payload.get("target_tile_id")

    sabotage = catalog.sabotages.get(sabotage_id) if sabotage_id else None
    if sabotage is None:
        return _failed(player_id, target_tile_id, sabotage_id, "UNKNOWN_SABOTAGE", tick_id)

    player = find_player(world_state, player_id)
    if player is None:
        return make_event(tick_id, "CONTRACT_ERROR", {
            "error_code": "MISSING_FIELD",
            "message": f"Player not found: {player_id}",
            "field_path": "player_id",
        })

    tile = find_tile(world_state, target_tile_id)
    if tile is None:
        return _failed(player_id, target_tile_id, sabotage_id, "UNKNOWN_TILE", tick_id)

    target_owner = tile.get("owner_player_id")
    if target_owner == player_id:
        return _failed(player_id, target_tile_id, sabotage_id, "OWN_TILE", tick_id)
    if not target_owner:
        return _failed(player_id, target_tile_id, sabotage_id, "NO_OWNER", tick_id)

    cost = sabotage.cost_bestiki
    money = player.get("money_bestiki", 0)
    if money < cost:
        return _failed(
            player_id,
            target_tile_id,
            sabotage_id,
            "NOT_ENOUGH_MONEY",
            tick_id,
            required=cost,
            available=money,
        )

    player["money_bestiki"] = money - cost
    effect = _apply_effect(tile, sabotage.sabotage_type)

    log.info(
        "APPLY_SABOTAGE ok player=%s -> tile=%s type=%s effect=%s paid=%s",
        player_id,
        target_tile_id,
        sabotage_id,
        effect,
        cost,
    )
    return make_event(tick_id, "SABOTAGE_APPLIED", {
        "player_id": player_id,
        "target_player_id": target_owner,
        "target_tile_id": target_tile_id,
        "sabotage_id": sabotage_id,
        "sabotage_type": sabotage.sabotage_type,
        "effect": effect,
        "is_hidden": bool(sabotage.is_hidden),
        "cost_paid": cost,
    })


def _apply_effect(tile: dict, sabotage_type: str) -> str:
    if sabotage_type == "WATER_SABOTAGE":
        water = tile.get("water_level")
        if water is None:
            return "NO_WATER_FIELD"
        tile["water_level"] = max(0, int(water) - 30)
        return "WATER_REDUCED"

    if sabotage_type == "DISEASE":
        if tile.get("occupant_type") != "PLANT":
            return "NO_PLANT"
        health = tile.get("health") or 100
        health -= 40
        if health <= 0:
            tile["occupant_type"] = "EMPTY"
            tile["occupant_id"] = None
            tile["health"] = None
            tile["growth_elapsed_sec"] = None
            tile["growth_time_sec"] = None
            tile["water_decay_per_tick"] = None
            return "PLANT_KILLED"
        tile["health"] = health
        flags = tile.setdefault("flags", [])
        if "INFECTED" not in flags:
            flags.append("INFECTED")
        return "PLANT_DAMAGED"

    if sabotage_type == "MINE":
        flags = tile.setdefault("flags", [])
        if "MINED" in flags:
            return "ALREADY_MINED"
        flags.append("MINED")
        if tile.get("occupant_type") == "PLANT":
            health = tile.get("health") or 100
            tile["health"] = max(0, health - 25)
        return "MINE_PLACED"

    return "UNKNOWN_TYPE"


def _failed(
    player_id: str,
    target_tile_id: str | None,
    sabotage_id: str | None,
    reason: str,
    tick_id: int,
    required: int = 0,
    available: int = 0,
) -> dict:
    payload = {
        "player_id": player_id,
        "target_tile_id": target_tile_id,
        "sabotage_id": sabotage_id,
        "reason": reason,
    }
    if reason == "NOT_ENOUGH_MONEY":
        payload["required"] = required
        payload["available"] = available
    return make_event(tick_id, "SABOTAGE_FAILED", payload)
