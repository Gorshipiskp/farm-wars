import { get } from "svelte/store";
import { api } from "$lib/api/client";
import { ApiError } from "$lib/api/errors";
import type { CatalogRecipe, PlayerState, TileState, WorldState } from "$lib/api/types";
import { seedProductIdForPlant, plantIds } from "$lib/game/catalogData";
import { factoryForRecipe, factoryLabel } from "$lib/game/factories";
import { inventoryAmount, isSellableProduct } from "$lib/game/inventory";
import { productLabel, seedLabelFromPlantId } from "$lib/game/labels";
import { FARM_COLS, WATERING_CAN_RADIUS } from "$lib/game/constants";
import { findTile, isEnemyTile, plantTilesForOwner } from "$lib/game/tiles";
import { tilesWithinPlantRadius } from "$lib/game/tileGrid";
import { matchFinished, selectedTileId, worldState } from "$lib/stores/game";
import {
  selectedAnimalId,
  selectedPlantId,
  selectedRecipeId,
  selectedSellProductId,
} from "$lib/stores/matchUi";
import { catalog, matchId, playerId, statusMessage } from "$lib/stores/session";
import { applySync } from "$lib/sync/applySync";
import { applyOptimisticAction } from "$lib/sync/optimistic";
import { requestSync } from "$lib/sync/requestSync";
import { pushToast } from "$lib/stores/toasts";

function myPlayer(world: WorldState | null): PlayerState | null {
  const pid = get(playerId);
  if (!world || !pid) return null;
  return world.players.find((p) => p.player_id === pid) ?? null;
}

function resolvePlantForPlace(player: PlayerState | null): string | null {
  if (!player) return null;
  const cat = get(catalog);
  const preferred = get(selectedPlantId);
  const seedPid = seedProductIdForPlant(cat, preferred);
  if (inventoryAmount(player, seedPid) >= 1) return preferred;
  for (const plantId of plantIds(cat)) {
    if (inventoryAmount(player, seedProductIdForPlant(cat, plantId)) >= 1) {
      return plantId;
    }
  }
  return null;
}

async function sendAction(
  actionType: string,
  payload: Record<string, unknown>,
): Promise<void> {
  if (get(matchFinished)) {
    pushToast("Матч уже окончен", "info");
    return;
  }
  const mid = get(matchId);
  const pid = get(playerId);
  if (!mid || !pid) return;

  const action = api.makeAction(pid, actionType, payload);
  const world = get(worldState);
  const cat = get(catalog);
  const optimistic = applyOptimisticAction(world, pid, cat, action);
  if (optimistic) {
    worldState.set(optimistic);
  }

  try {
    const res = await api.submitAction(mid, pid, action);
    if (res.sync) {
      applySync(res.sync);
    } else {
      await requestSync();
    }
  } catch (e) {
    await requestSync();
    const msg = e instanceof ApiError ? e.message : String(e);
    statusMessage.set(msg);
    pushToast(msg, "error");
  }
}

function selectedTile(world: WorldState | null): TileState | null {
  return findTile(world, get(selectedTileId));
}

/** Полив грядок или кормление животного — по типу выбранной клетки. */
export async function sendCare(): Promise<void> {
  const tileId = get(selectedTileId);
  if (!tileId) {
    pushToast("Сначала выбери клетку", "warn");
    return;
  }
  const world = get(worldState);
  const tile = findTile(world, tileId);
  if (!tile) return;

  if (tile.zone_type === "ANIMAL") {
    if (tile.occupant_type !== "ANIMAL") {
      pushToast("В загоне нет животного — купи или перетащи с панели", "warn");
      return;
    }
    await sendFeedOnTile(tileId);
    return;
  }

  if (tile.zone_type !== "PLANT") {
    pushToast("Уход только для грядок и загона", "warn");
    return;
  }
  await sendWaterArea(tileId);
}

/** @deprecated Use sendCare */
export async function sendWater(): Promise<void> {
  await sendCare();
}

export async function sendWaterArea(centerTileId: string): Promise<void> {
  const world = get(worldState);
  const pid = get(playerId);
  const center = findTile(world, centerTileId);
  if (!center || center.zone_type !== "PLANT" || center.owner_player_id !== pid) {
    pushToast("Лейка — только по огороду", "warn");
    return;
  }
  const plantTiles = plantTilesForOwner(world, pid ?? "");
  const splash = tilesWithinPlantRadius(
    centerTileId,
    plantTiles,
    WATERING_CAN_RADIUS,
    world?.map?.width ?? FARM_COLS,
  );
  await sendAction("WATER_AREA", {
    tile_id: centerTileId,
    radius: WATERING_CAN_RADIUS,
  });
}

export async function sendPlantOnTile(tileId: string, plantId?: string): Promise<void> {
  selectedTileId.set(tileId);
  const world = get(worldState);
  const player = myPlayer(world);
  const pid = plantId ?? get(selectedPlantId);
  const cat = get(catalog);
  const seedPid = seedProductIdForPlant(cat, pid);
  if (!player || inventoryAmount(player, seedPid) < 1) {
    pushToast("Нет таких семян в сумке", "warn");
    return;
  }
  selectedPlantId.set(pid);
  await sendAction("PLACE_ON_TILE", { tile_id: tileId, plant_id: pid });
}

export async function sendPlant(): Promise<void> {
  const tileId = get(selectedTileId);
  if (!tileId) {
    pushToast("Сначала выбери грядку", "warn");
    return;
  }
  const world = get(worldState);
  const plantId = resolvePlantForPlace(myPlayer(world));
  if (!plantId) {
    pushToast("Нет семян — загляни в магазин", "warn");
    return;
  }
  await sendPlantOnTile(tileId, plantId);
}

export async function sendHarvestOnTile(tileId: string): Promise<void> {
  selectedTileId.set(tileId);
  await sendAction("HARVEST_PLANT", { tile_id: tileId });
}

export async function sendHarvest(): Promise<void> {
  const tileId = get(selectedTileId);
  if (!tileId) {
    pushToast("Сначала выбери грядку", "warn");
    return;
  }
  await sendHarvestOnTile(tileId);
}

export async function sendWaterOnTile(tileId: string): Promise<void> {
  selectedTileId.set(tileId);
  await sendWaterArea(tileId);
}

export async function sendBuyProduct(productId: string): Promise<void> {
  await sendAction("BUY_PRODUCT", { product_id: productId, amount: 1 });
}

export async function sendSellAmount(productId: string, amount: number): Promise<void> {
  selectedSellProductId.set(productId);
  const world = get(worldState);
  const player = myPlayer(world);
  const have = inventoryAmount(player, productId);
  const sell = Math.min(Math.max(1, Math.floor(amount)), have);
  if (!player || sell < 1) {
    pushToast("Нет такого товара", "warn");
    return;
  }
  if (!isSellableProduct(productId, get(catalog))) {
    pushToast("Не продаётся на рынке", "warn");
    return;
  }
  await sendAction("SELL_PRODUCT", { product_id: productId, amount: sell });
}

export async function sendSellProduct(productId: string): Promise<void> {
  await sendSellAmount(productId, 1);
}

export async function sendSell(): Promise<void> {
  const world = get(worldState);
  const player = myPlayer(world);
  if (!player) return;
  let productId = get(selectedSellProductId);
  if (productId && inventoryAmount(player, productId) < 1) {
    productId = null;
  }
  if (!productId) {
    const cat = get(catalog);
    for (const item of player.inventory) {
      const pid = item.product_id;
      if (isSellableProduct(pid, cat) && item.amount > 0) {
        productId = pid;
        break;
      }
    }
  }
  if (!productId) {
    pushToast("Нечего продать — сначала собери урожай", "warn");
    return;
  }
  await sendAction("SELL_PRODUCT", { product_id: productId, amount: 1 });
}

export async function sendRecipeFor(recipeId: string): Promise<void> {
  const world = get(worldState);
  const pid = get(playerId);
  const cat = get(catalog);
  const recipe = cat?.recipes?.find((r) => r.recipe_id === recipeId) ?? null;
  if (!recipe) {
    pushToast("Неизвестный рецепт", "warn");
    return;
  }
  const factory = factoryForRecipe(world, pid, recipe);
  if (!factory) {
    pushToast("Нет завода для этого рецепта", "warn");
    return;
  }
  if (factory.active_recipe_id) {
    pushToast(`${factoryLabel(factory.factory_type)} занят — рецепт в очереди`, "info");
  }
  selectedRecipeId.set(recipeId);
  await sendAction("START_RECIPE", {
    factory_id: factory.factory_id,
    recipe_id: recipeId,
  });
}

export async function sendRecipe(): Promise<void> {
  const recipeId = get(selectedRecipeId) || "bread";
  await sendRecipeFor(recipeId);
}

export async function sendBuyAnimalOnTile(tileId: string, animalId?: string): Promise<void> {
  selectedTileId.set(tileId);
  const world = get(worldState);
  const tile = findTile(world, tileId);
  if (!tile) return;
  if (tile.zone_type !== "ANIMAL") {
    pushToast("Животное — только в загон", "warn");
    return;
  }
  if (tile.occupant_type && tile.occupant_type !== "EMPTY") {
    pushToast("Загон занят", "warn");
    return;
  }
    const aid = animalId ?? get(selectedAnimalId) ?? "cow";
  selectedAnimalId.set(aid);
  await sendAction("BUY_ANIMAL", { tile_id: tileId, animal_id: aid });
}

export async function sendBuyAnimal(): Promise<void> {
  const tileId = get(selectedTileId);
  if (!tileId) {
    pushToast("Выбери пустой загон", "warn");
    return;
  }
  await sendBuyAnimalOnTile(tileId);
}

export async function sendFeedOnTile(tileId: string): Promise<void> {
  selectedTileId.set(tileId);
  const world = get(worldState);
  const tile = findTile(world, tileId);
  if (!tile || tile.occupant_type !== "ANIMAL") {
    pushToast("Перетащи корм на загон с животным", "warn");
    return;
  }
  await sendAction("FEED_ANIMAL", { tile_id: tileId });
}

/** @deprecated Use sendCare */
export async function sendFeed(): Promise<void> {
  await sendCare();
}

export async function sendSabotageOnTile(tileId: string, sabotageId: string): Promise<void> {
  selectedTileId.set(tileId);
  const world = get(worldState);
  const tile = findTile(world, tileId);
  const pid = get(playerId);
  if (!tile || !isEnemyTile(tile, pid)) {
    pushToast("Саботаж только по клетке соперника", "warn");
    return;
  }
  await sendAction("APPLY_SABOTAGE", {
    sabotage_id: sabotageId,
    target_tile_id: tileId,
  });
}

export async function sendClearMine(tileId: string): Promise<void> {
  await sendAction("CLEAR_MINE", { tile_id: tileId });
}

export async function sendSabotage(sabotageId: string): Promise<void> {
  const tileId = get(selectedTileId);
  if (!tileId) {
    pushToast("Выбери клетку соперника", "warn");
    return;
  }
  await sendSabotageOnTile(tileId, sabotageId);
}

export function selectPlant(plantId: string): void {
  selectedPlantId.set(plantId);
  pushToast(`Семена: ${seedLabelFromPlantId(plantId, get(catalog))}`, "info");
}

export function selectSellProduct(productId: string): void {
  selectedSellProductId.set(productId);
}

export function selectRecipe(recipeId: string): void {
  selectedRecipeId.set(recipeId);
}

export function selectAnimal(animalId: string): void {
  selectedAnimalId.set(animalId);
}

export function syncSellSelection(player: PlayerState | null): void {
  if (!player) {
    selectedSellProductId.set(null);
    return;
  }
  const cat = get(catalog);
  const cur = get(selectedSellProductId);
  if (cur && inventoryAmount(player, cur) > 0 && isSellableProduct(cur, cat)) return;
  for (const item of player.inventory) {
    if (isSellableProduct(item.product_id, cat) && item.amount > 0) {
      selectedSellProductId.set(item.product_id);
      return;
    }
  }
  selectedSellProductId.set(null);
}

export function recipeById(recipeId: string): CatalogRecipe | null {
  const cat = get(catalog);
  return cat?.recipes?.find((r) => r.recipe_id === recipeId) ?? null;
}
