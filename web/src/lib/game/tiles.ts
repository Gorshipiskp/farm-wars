import type { PlayerState, TileState, WorldState } from "$lib/api/types";
import { animalTilesOrdered, plantTilesOrdered } from "./tileGrid";

export function tilesForOwner(world: WorldState | null, ownerId: string): TileState[] {
  if (!world?.map?.tiles) return [];
  const tiles = world.map.tiles.filter((t) => t.owner_player_id === ownerId);
  tiles.sort((a, b) => {
    const za = a.zone_type === "PLANT" ? 0 : 1;
    const zb = b.zone_type === "PLANT" ? 0 : 1;
    if (za !== zb) return za - zb;
    return a.tile_id.localeCompare(b.tile_id);
  });
  return tiles;
}

export function plantTilesForOwner(world: WorldState | null, ownerId: string): TileState[] {
  return plantTilesOrdered(tilesForOwner(world, ownerId));
}

export function animalTilesForOwner(world: WorldState | null, ownerId: string): TileState[] {
  return animalTilesOrdered(tilesForOwner(world, ownerId));
}

export function opponents(world: WorldState | null, myPlayerId: string): PlayerState[] {
  if (!world?.players) return [];
  return world.players.filter((p) => p.player_id !== myPlayerId);
}

export function findTile(world: WorldState | null, tileId: string | null): TileState | null {
  if (!world || !tileId) return null;
  return world.map.tiles.find((t) => t.tile_id === tileId) ?? null;
}

export function isEnemyTile(tile: TileState | null, myPlayerId: string): boolean {
  if (!tile) return false;
  return tile.owner_player_id !== myPlayerId;
}

export function ensureViewOpponent(
  world: WorldState | null,
  myPlayerId: string,
  current: string | null,
): string | null {
  const opps = opponents(world, myPlayerId);
  if (!opps.length) return null;
  const ids = new Set(opps.map((p) => p.player_id));
  if (current && ids.has(current)) return current;
  return opps[0].player_id;
}

export function opponentDisplayName(
  world: WorldState | null,
  myPlayerId: string,
  opponentId: string | null,
): string {
  if (!opponentId) return "соперника";
  for (const p of opponents(world, myPlayerId)) {
    if (p.player_id === opponentId) {
      return (p.display_name || p.player_id).trim();
    }
  }
  return opponentId;
}
