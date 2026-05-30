import type { GameCatalog, PlayerState, TileState, WorldState } from "$lib/api/types";
import { seedProductIdForPlant } from "$lib/game/catalogData";
import { FARM_COLS, WATERING_CAN_RADIUS } from "$lib/game/constants";
import { inventoryAmount, isSellableProduct } from "$lib/game/inventory";
import { sellUnitPrice } from "$lib/game/prices";
import { tilesWithinPlantRadius } from "$lib/game/tileGrid";
import { plantTilesForOwner } from "$lib/game/tiles";
import { TICKS_PER_SECOND } from "$lib/game/pacing";
import type { PlayerAction } from "$lib/api/types";

function cloneWorld(world: WorldState): WorldState {
  return structuredClone(world);
}

function myPlayer(world: WorldState, playerId: string): PlayerState | null {
  return world.players.find((p) => p.player_id === playerId) ?? null;
}

function updateTile(world: WorldState, tileId: string, patch: Partial<TileState>): void {
  const tile = world.map.tiles.find((t) => t.tile_id === tileId);
  if (tile) Object.assign(tile, patch);
}

function addInv(player: PlayerState, productId: string, amount: number): void {
  const item = player.inventory.find((i) => i.product_id === productId);
  if (item) item.amount += amount;
  else player.inventory.push({ product_id: productId, amount });
}

function takeInv(player: PlayerState, productId: string, amount: number): boolean {
  if (inventoryAmount(player, productId) < amount) return false;
  for (const item of player.inventory) {
    if (item.product_id === productId) {
      item.amount -= amount;
      break;
    }
  }
  player.inventory = player.inventory.filter((i) => i.amount > 0);
  return true;
}

function spendMoney(player: PlayerState, cost: number): boolean {
  if ((player.money_bestiki ?? 0) < cost) return false;
  player.money_bestiki -= cost;
  return true;
}

function feedCareCost(catalog: GameCatalog | null): number {
  const feed = catalog?.products?.find((p) => p.product_id === "feed");
  return Math.max(1, feed?.price ?? 3);
}

function waterCareCost(catalog: GameCatalog | null): number {
  const feed = feedCareCost(catalog);
  return feed > 1 ? feed - 1 : 2;
}

function shopBuyPrice(catalog: GameCatalog | null, productId: string): number {
  const p = catalog?.products?.find((x) => x.product_id === productId);
  return p?.price ?? p?.base_sell_price ?? 0;
}

function animalPrice(catalog: GameCatalog | null, animalId: string): number {
  const spec = catalog?.animals?.find((a) => a.animal_id === animalId);
  if (spec?.price != null) return spec.price;
  const milk = catalog?.products?.find((p) => p.product_id === "milk");
  return (milk?.price ?? 10) * 5;
}

/**
 * Predict world state after a successful action (best-effort; server sync reconciles).
 */
export function applyOptimisticAction(
  world: WorldState | null,
  playerId: string,
  catalog: GameCatalog | null,
  action: Pick<PlayerAction, "action_type" | "payload">,
): WorldState | null {
  if (!world) return null;
  const next = cloneWorld(world);
  const player = myPlayer(next, playerId);
  if (!player) return null;

  const type = action.action_type;
  const payload = action.payload ?? {};

  if (type === "WATER_AREA") {
    const centerId = String(payload.tile_id ?? "");
    const plantTiles = plantTilesForOwner(next, playerId);
    const splash = tilesWithinPlantRadius(
      centerId,
      plantTiles,
      Number(payload.radius ?? WATERING_CAN_RADIUS),
      next.map?.width ?? FARM_COLS,
    );
    const cost = waterCareCost(catalog);
    if (!spendMoney(player, cost)) return null;
    for (const t of splash) {
      updateTile(next, t.tile_id, { water_level: 100 });
    }
    return next;
  }

  if (type === "WATER_PLANT") {
    const tileId = String(payload.tile_id ?? "");
    if (!spendMoney(player, waterCareCost(catalog))) return null;
    updateTile(next, tileId, { water_level: 100 });
    return next;
  }

  if (type === "FEED_ANIMAL") {
    const tileId = String(payload.tile_id ?? "");
    if (!spendMoney(player, feedCareCost(catalog))) return null;
    updateTile(next, tileId, {
      hunger_ticks: 0,
      production_elapsed_sec: 0,
    });
    return next;
  }

  if (type === "PLACE_ON_TILE") {
    const tileId = String(payload.tile_id ?? "");
    const plantId = String(payload.plant_id ?? "");
    const seedPid = seedProductIdForPlant(catalog, plantId);
    if (!takeInv(player, seedPid, 1)) return null;
    updateTile(next, tileId, {
      occupant_type: "PLANT",
      occupant_id: plantId,
      health: 100,
      water_level: 50,
      growth_elapsed_sec: 0,
      growth_time_sec: 120,
      water_decay_per_tick: 1,
    });
    return next;
  }

  if (type === "HARVEST_PLANT") {
    const tileId = String(payload.tile_id ?? "");
    const tile = next.map.tiles.find((t) => t.tile_id === tileId);
    if (!tile?.occupant_id) return null;
    const pl = catalog?.plants?.find((p) => p.plant_id === tile.occupant_id);
    const cropId = pl?.product_id ?? tile.occupant_id;
    addInv(player, cropId, 1);
    updateTile(next, tileId, {
      occupant_type: "EMPTY",
      occupant_id: null,
      water_level: null,
      growth_elapsed_sec: null,
      growth_time_sec: null,
      health: null,
    });
    return next;
  }

  if (type === "BUY_PRODUCT") {
    const productId = String(payload.product_id ?? "");
    const amount = Math.max(1, Number(payload.amount ?? 1));
    const price = shopBuyPrice(catalog, productId) * amount;
    if (!spendMoney(player, price)) return null;
    addInv(player, productId, amount);
    return next;
  }

  if (type === "SELL_PRODUCT") {
    const productId = String(payload.product_id ?? "");
    const amount = Math.max(1, Number(payload.amount ?? 1));
    if (!isSellableProduct(productId, catalog)) return null;
    const unit = sellUnitPrice(productId, catalog);
    if (!takeInv(player, productId, amount)) return null;
    player.money_bestiki = (player.money_bestiki ?? 0) + unit * amount;
    return next;
  }

  if (type === "BUY_ANIMAL") {
    const tileId = String(payload.tile_id ?? "");
    const animalId = String(payload.animal_id ?? "cow");
    const price = animalPrice(catalog, animalId);
    if (!spendMoney(player, price)) return null;
    const productByAnimal: Record<string, string> = {
      cow: "milk",
      chicken: "egg",
      sheep: "wool",
      pig: "pork",
    };
    updateTile(next, tileId, {
      occupant_type: "ANIMAL",
      occupant_id: animalId,
      health: 100,
      hunger_ticks: 0,
      production_elapsed_sec: 0,
      production_interval_sec: 100,
      product_id: productByAnimal[animalId] ?? "milk",
    });
    return next;
  }

  if (type === "START_RECIPE") {
    const recipeId = String(payload.recipe_id ?? "");
    const factoryId = String(payload.factory_id ?? "");
    const recipe = catalog?.recipes?.find((r) => r.recipe_id === recipeId);
    const factory = next.factories.find((f) => f.factory_id === factoryId);
    if (!recipe || !factory) return null;
    for (const ing of recipe.ingredients ?? []) {
      if (!takeInv(player, ing.product_id, ing.amount)) return null;
    }
    const wallSec = (recipe as { production_time_sec?: number }).production_time_sec ?? 30;
    factory.active_recipe_id = recipeId;
    factory.remaining_time_sec = Math.max(1, Math.floor(wallSec * TICKS_PER_SECOND));
    return next;
  }

  if (type === "APPLY_SABOTAGE") {
    const sabId = String(payload.sabotage_id ?? "");
    const sab = catalog?.sabotages?.find((s) => s.sabotage_id === sabId);
    const price = sab?.price ?? 0;
    if (!spendMoney(player, price)) return null;
    const targetId = String(payload.target_tile_id ?? "");
    const target = next.map.tiles.find((t) => t.tile_id === targetId);
    if (!target || target.owner_player_id === playerId) return null;

    const sabType = (sab as { sabotage_type?: string } | undefined)?.sabotage_type;
    if (sabType === "WATER_SABOTAGE" || sabId === "poison_water") {
      const water = target.water_level;
      if (water != null) {
        target.water_level = Math.max(0, water - 30);
      }
    } else if (sabType === "MINE" || sabId === "mine_tile") {
      const flags = target.flags ?? [];
      if (!flags.includes("MINED")) target.flags = [...flags, "MINED"];
    } else if (sabType === "DISEASE" || sabId === "spread_disease") {
      if (target.occupant_type === "PLANT") {
        const health = (target.health ?? 100) - 40;
        target.health = Math.max(0, health);
        const flags = target.flags ?? [];
        if (!flags.includes("INFECTED")) target.flags = [...flags, "INFECTED"];
      }
    }
    return next;
  }

  return null;
}
