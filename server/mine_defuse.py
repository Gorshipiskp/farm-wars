"""Server-side mine defuse / minesweeper loss on the farm."""

from __future__ import annotations

from server.farm_grid import adjacent_plant_tiles, clear_plant_on_tile
from server.world_util import find_tile, make_event


def process_clear_mine(action: dict, world_state: dict, _catalog, tick_id: int) -> dict | None:
    player_id = action.get("player_id")
    payload = action.get("payload") or {}
    tile_id = payload.get("tile_id")

    tile = find_tile(world_state, tile_id)
    if tile is None:
        return _clear_failed(player_id, tile_id, "UNKNOWN_TILE", tick_id)

    if tile.get("owner_player_id") != player_id:
        return _clear_failed(player_id, tile_id, "NOT_OWNER", tick_id)

    flags = tile.get("flags") or []
    if "MINED" not in flags:
        return _clear_failed(player_id, tile_id, "NOT_MINED", tick_id)

    tile["flags"] = [f for f in flags if f != "MINED"]
    return make_event(tick_id, "MINE_CLEARED", {
        "player_id": player_id,
        "tile_id": tile_id,
    })


def process_minesweeper_lost(action: dict, world_state: dict, _catalog, tick_id: int) -> list[dict]:
    player_id = action.get("player_id")
    payload = action.get("payload") or {}
    tile_id = payload.get("tile_id")

    tile = find_tile(world_state, tile_id)
    if tile is None:
        return [_lost_failed(player_id, tile_id, "UNKNOWN_TILE", tick_id)]

    if tile.get("owner_player_id") != player_id:
        return [_lost_failed(player_id, tile_id, "NOT_OWNER", tick_id)]

    flags = tile.get("flags") or []
    if "MINED" not in flags:
        return [_lost_failed(player_id, tile_id, "NOT_MINED", tick_id)]

    events: list[dict] = []
    destroyed: list[str] = []
    for neighbor in adjacent_plant_tiles(world_state, tile_id, player_id, radius=1):
        plant_id = clear_plant_on_tile(neighbor)
        if plant_id:
            destroyed.append(neighbor["tile_id"])
            events.append(make_event(tick_id, "PLANT_DIED", {
                "player_id": player_id,
                "tile_id": neighbor["tile_id"],
                "plant_id": plant_id,
                "cause": "MINESWEEPER_BLAST",
            }))

    events.append(make_event(tick_id, "MINESWEEPER_BLAST", {
        "player_id": player_id,
        "tile_id": tile_id,
        "destroyed_tile_ids": destroyed,
    }))
    return events


def _clear_failed(player_id: str, tile_id: str | None, reason: str, tick_id: int) -> dict:
    return make_event(tick_id, "CLEAR_MINE_FAILED", {
        "player_id": player_id,
        "tile_id": tile_id,
        "reason": reason,
    })


def _lost_failed(player_id: str, tile_id: str | None, reason: str, tick_id: int) -> dict:
    return make_event(tick_id, "MINESWEEPER_LOST_FAILED", {
        "player_id": player_id,
        "tile_id": tile_id,
        "reason": reason,
    })
