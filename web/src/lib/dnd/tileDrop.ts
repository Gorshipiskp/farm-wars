import {
  sendBuyAnimalOnTile,
  sendHarvestOnTile,
  sendPlantOnTile,
  sendSabotageOnTile,
  sendWaterArea,
} from "$lib/actions/gameActions";
import { WATER_LOW_THRESHOLD } from "$lib/game/pacing";
import { isEmptyPenTile } from "$lib/game/tileGrid";
import { seedProductIdForPlant } from "$lib/game/catalogData";
import { inventoryAmount } from "$lib/game/inventory";
import { findTile, isEnemyTile } from "$lib/game/tiles";
import type { DragPayload } from "./types";
import type { PlayerState, TileState, WorldState } from "$lib/api/types";
import { get } from "svelte/store";
import { catalog } from "$lib/stores/session";
import { pushToast } from "$lib/stores/toasts";

function isEmptyPlantTile(tile: TileState): boolean {
  return (
    tile.zone_type !== "ANIMAL" &&
    (!tile.occupant_type || tile.occupant_type === "EMPTY")
  );
}

function isRipe(tile: TileState): boolean {
  const elapsed = tile.growth_elapsed_sec ?? 0;
  const needed = tile.growth_time_sec ?? 0;
  return needed > 0 && elapsed >= needed;
}

function needsWater(tile: TileState): boolean {
  const w = tile.water_level;
  return (
    w != null &&
    w < WATER_LOW_THRESHOLD &&
    !isEmptyPlantTile(tile) &&
    tile.zone_type !== "ANIMAL"
  );
}

export function canDropOnTile(
  payload: DragPayload,
  tile: TileState,
  myPlayerId: string,
  player: PlayerState | null,
): boolean {
  const own = tile.owner_player_id === myPlayerId;
  const enemy = isEnemyTile(tile, myPlayerId);
  const cat = get(catalog);

  if (payload.kind === "seed") {
    if (!own || !isEmptyPlantTile(tile) || !player) return false;
    const seedPid = seedProductIdForPlant(cat, payload.plantId);
    return inventoryAmount(player, seedPid) >= 1;
  }
  if (payload.kind === "harvest") {
    if (own && isRipe(tile)) return true;
    return false;
  }
  if (payload.kind === "sabotage") {
    return enemy;
  }
  if (payload.kind === "watering_can") {
    return own && tile.zone_type === "PLANT";
  }
  if (payload.kind === "animal") {
    if (!own || !isEmptyPenTile(tile) || !player) return false;
    const spec = cat?.animals?.find((a) => a.animal_id === payload.animalId);
    const price = spec?.price ?? 0;
    return (player.money_bestiki ?? 0) >= price;
  }
  return false;
}

export async function handleTileDrop(
  tileId: string,
  payload: DragPayload,
  world: WorldState | null,
  myPlayerId: string,
  player: PlayerState | null,
): Promise<void> {
  const tile = findTile(world, tileId);
  if (!tile) return;

  if (payload.kind === "seed") {
    if (!canDropOnTile(payload, tile, myPlayerId, player)) {
      pushToast("Сюда нельзя посадить", "warn");
      return;
    }
    await sendPlantOnTile(tileId, payload.plantId);
    return;
  }

  if (payload.kind === "harvest") {
    if (canDropOnTile(payload, tile, myPlayerId, player)) {
      await sendHarvestOnTile(tileId);
      return;
    }
    if (tile.owner_player_id === myPlayerId && needsWater(tile)) {
      await sendWaterArea(tileId);
      return;
    }
    pushToast("Перетащи урожай на рынок или на созревшую грядку", "warn");
    return;
  }

  if (payload.kind === "sabotage") {
    if (!canDropOnTile(payload, tile, myPlayerId, player)) {
      pushToast("Саботаж — только по клетке соперника", "warn");
      return;
    }
    await sendSabotageOnTile(tileId, payload.sabotageId);
    return;
  }

  if (payload.kind === "watering_can") {
    if (!canDropOnTile(payload, tile, myPlayerId, player)) {
      pushToast("Лейка — только по огороду", "warn");
      return;
    }
    await sendWaterArea(tileId);
    return;
  }

  if (payload.kind === "animal") {
    if (!canDropOnTile(payload, tile, myPlayerId, player)) {
      pushToast("Перетащи на пустой загон", "warn");
      return;
    }
    await sendBuyAnimalOnTile(tileId, payload.animalId);
  }
}
