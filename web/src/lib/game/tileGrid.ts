import { FARM_COLS } from "./constants";
import type { TileState } from "$lib/api/types";

/** Garden tiles in stable grid order (matches server plant-tile sort). */
export function plantTilesOrdered(tiles: TileState[]): TileState[] {
  return tiles
    .filter((t) => t.zone_type === "PLANT")
    .sort((a, b) => a.tile_id.localeCompare(b.tile_id));
}

export function animalTilesOrdered(tiles: TileState[]): TileState[] {
  return tiles
    .filter((t) => t.zone_type === "ANIMAL")
    .sort((a, b) => a.tile_id.localeCompare(b.tile_id));
}

export function plantGridPosition(
  tileId: string,
  plantTiles: TileState[],
  cols: number = FARM_COLS,
): { col: number; row: number } | null {
  const ids = plantTiles.map((t) => t.tile_id);
  const idx = ids.indexOf(tileId);
  if (idx < 0) return null;
  return { col: idx % cols, row: Math.floor(idx / cols) };
}

/** Chebyshev distance on the plant grid (square splash). */
export function tilesWithinPlantRadius(
  centerTileId: string,
  plantTiles: TileState[],
  radius: number,
  cols: number = FARM_COLS,
): TileState[] {
  const center = plantGridPosition(centerTileId, plantTiles, cols);
  if (!center) return [];
  return plantTiles.filter((t) => {
    const pos = plantGridPosition(t.tile_id, plantTiles, cols);
    if (!pos) return false;
    const dist = Math.max(Math.abs(pos.col - center.col), Math.abs(pos.row - center.row));
    return dist <= radius;
  });
}

export function isEmptyPenTile(tile: TileState): boolean {
  return tile.zone_type === "ANIMAL" && (!tile.occupant_type || tile.occupant_type === "EMPTY");
}

/** Plant tiles adjacent on the farm grid (Chebyshev), excluding center. */
export function adjacentPlantTiles(
  centerTileId: string,
  plantTiles: TileState[],
  cols: number = FARM_COLS,
): TileState[] {
  const center = plantGridPosition(centerTileId, plantTiles, cols);
  if (!center) return [];
  return plantTiles.filter((t) => {
    if (t.tile_id === centerTileId) return false;
    const pos = plantGridPosition(t.tile_id, plantTiles, cols);
    if (!pos) return false;
    const dist = Math.max(Math.abs(pos.col - center.col), Math.abs(pos.row - center.row));
    return dist === 1;
  });
}
