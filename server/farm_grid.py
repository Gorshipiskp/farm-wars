"""Plant-grid helpers (4 columns, matches web FARM_COLS)."""

from __future__ import annotations

FARM_PLANT_COLS = 4


def plant_tiles_for_owner(world_state: dict, owner_player_id: str) -> list[dict]:
    tiles = world_state.get("map", {}).get("tiles", [])
    return sorted(
        [
            t
            for t in tiles
            if t.get("zone_type") == "PLANT" and t.get("owner_player_id") == owner_player_id
        ],
        key=lambda t: t["tile_id"],
    )


def _grid_pos(tile_id: str, plant_tiles: list[dict], cols: int) -> tuple[int, int] | None:
    ids = [t["tile_id"] for t in plant_tiles]
    if tile_id not in ids:
        return None
    idx = ids.index(tile_id)
    return idx % cols, idx // cols


def adjacent_plant_tiles(
    world_state: dict,
    center_tile_id: str,
    owner_player_id: str,
    *,
    radius: int = 1,
) -> list[dict]:
    """Neighboring PLANT-zone tiles on the farm grid (Chebyshev distance)."""
    plant_tiles = plant_tiles_for_owner(world_state, owner_player_id)
    center = _grid_pos(center_tile_id, plant_tiles, FARM_PLANT_COLS)
    if center is None:
        return []
    cx, cy = center
    out: list[dict] = []
    for tile in plant_tiles:
        pos = _grid_pos(tile["tile_id"], plant_tiles, FARM_PLANT_COLS)
        if pos is None:
            continue
        dist = max(abs(pos[0] - cx), abs(pos[1] - cy))
        if 0 < dist <= radius:
            out.append(tile)
    return out


def clear_plant_on_tile(tile: dict) -> str | None:
    """Remove plant from tile. Returns plant_id if one was cleared."""
    if tile.get("occupant_type") != "PLANT":
        return None
    plant_id = tile.get("occupant_id")
    tile["occupant_type"] = "EMPTY"
    tile["occupant_id"] = None
    tile["health"] = None
    tile["water_level"] = None
    tile["growth_elapsed_sec"] = None
    tile["growth_time_sec"] = None
    tile["water_decay_per_tick"] = None
    return plant_id
