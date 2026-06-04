"""Server-side mine defuse after winning the minesweeper mini-game."""

from __future__ import annotations

from server.world_util import find_tile, make_event


def process_clear_mine(action: dict, world_state: dict, _catalog, tick_id: int) -> dict | None:
    player_id = action.get("player_id")
    payload = action.get("payload") or {}
    tile_id = payload.get("tile_id")

    tile = find_tile(world_state, tile_id)
    if tile is None:
        return _failed(player_id, tile_id, "UNKNOWN_TILE", tick_id)

    if tile.get("owner_player_id") != player_id:
        return _failed(player_id, tile_id, "NOT_OWNER", tick_id)

    flags = tile.get("flags") or []
    if "MINED" not in flags:
        return _failed(player_id, tile_id, "NOT_MINED", tick_id)

    tile["flags"] = [f for f in flags if f != "MINED"]
    return make_event(tick_id, "MINE_CLEARED", {
        "player_id": player_id,
        "tile_id": tile_id,
    })


def _failed(player_id: str, tile_id: str | None, reason: str, tick_id: int) -> dict:
    return make_event(tick_id, "CLEAR_MINE_FAILED", {
        "player_id": player_id,
        "tile_id": tile_id,
        "reason": reason,
    })
