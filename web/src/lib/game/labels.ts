import { get } from "svelte/store";
import type { CatalogPlant, GameCatalog, TileState } from "$lib/api/types";
import {
  ANIMAL_HUNGER_WARN_TICKS,
  ANIMAL_PRODUCTION_HUNGER_TICKS,
  WATER_LOW_THRESHOLD,
} from "$lib/game/pacing";
import { canHarvestPlant, growthPercent, isRipeTile } from "$lib/game/visuals";
import { catalog } from "$lib/stores/session";

const PRODUCT_RU: Record<string, string> = {
  wheat: "Пшеница",
  corn: "Кукуруза",
  potato: "Картофель",
  tomato: "Помидор",
  carrot: "Морковь",
  sunflower: "Подсолнечник",
  wheat_seed: "Семена пшеницы",
  corn_seed: "Семена кукурузы",
  potato_seed: "Семена картофеля",
  tomato_seed: "Семена томата",
  carrot_seed: "Семена моркови",
  sunflower_seed: "Семена подсолнечника",
  flour: "Мука",
  bread: "Хлеб",
  cake: "Торт",
  cheese: "Сыр",
  butter: "Масло",
  sausage: "Колбаса",
  pie: "Пирог",
  soup: "Суп",
  omelette: "Омлет",
  milk: "Молоко",
  egg: "Яйцо",
  wool: "Шерсть",
  pork: "Свинина",
  feed: "Корм",
};

const ANIMAL_RU: Record<string, string> = {
  cow: "Корова",
  chicken: "Курица",
  sheep: "Овца",
  pig: "Свинья",
};

const ANIMAL_PRODUCT_FALLBACK: Record<string, string> = {
  cow: "milk",
  chicken: "egg",
  sheep: "wool",
  pig: "pork",
};

function fromCatalog(productId: string, cat: GameCatalog | null): string | null {
  if (!cat?.products) return null;
  const p = cat.products.find((x) => x.product_id === productId);
  if (p?.display_name) return p.display_name;
  if (!cat.plants) return null;
  for (const pl of cat.plants) {
    if (pl.seed_product_id === productId && pl.seed_display_name) return pl.seed_display_name;
    if (pl.product_id === productId && pl.crop_display_name) return pl.crop_display_name;
    if (pl.product_id === productId && pl.display_name) return pl.display_name;
  }
  return null;
}

export function productLabel(productId: string): string {
  const cat = get(catalog);
  return fromCatalog(productId, cat) ?? PRODUCT_RU[productId] ?? productId;
}

export function cropLabel(plantId: string | null | undefined): string {
  if (!plantId) return "?";
  const cat = get(catalog);
  const pl = cat?.plants?.find((p) => p.plant_id === plantId);
  if (pl?.crop_display_name) return pl.crop_display_name;
  if (pl?.display_name) return pl.display_name;
  if (pl?.product_id) return productLabel(pl.product_id);
  return productLabel(plantId);
}

export function animalLabel(animalId: string | null | undefined): string {
  if (!animalId) return "Животное";
  const cat = get(catalog);
  const a = cat?.animals?.find((x) => x.animal_id === animalId);
  return a?.display_name ?? ANIMAL_RU[animalId] ?? animalId;
}

export function animalProductId(
  animalId: string | null | undefined,
  cat: GameCatalog | null = null,
): string {
  if (!animalId) return "milk";
  const resolved = cat ?? get(catalog);
  const a = resolved?.animals?.find((x) => x.animal_id === animalId);
  return a?.product_id ?? ANIMAL_PRODUCT_FALLBACK[animalId] ?? animalId;
}

/** Product name in lower case for hints («курица · яйцо 40%»). */
export function animalYieldNoun(
  animalId: string | null | undefined,
  cat: GameCatalog | null = null,
): string {
  return productLabel(animalProductId(animalId, cat)).toLowerCase();
}

export function seedLabelFromPlantId(plantId: string, cat: GameCatalog | null): string {
  const pl = cat?.plants?.find((p) => p.plant_id === plantId);
  if (pl?.seed_display_name) return pl.seed_display_name;
  return productLabel(pl?.seed_product_id ?? `${plantId}_seed`);
}

export function tileHint(
  tile: TileState | null,
  selectedPlantId: string,
  myPlayerId: string | null,
  cat: GameCatalog | null = null,
): string {
  if (!tile) {
    return "Выбери грядку — кликни по клетке (своя или соперника)";
  }
  if (myPlayerId && tile.owner_player_id !== myPlayerId) {
    const flags = tile.flags ?? [];
    if (flags.includes("MINED")) {
      return "Клетка соперника · подозрительно (мина?)";
    }
    return "Клетка соперника · саботаж (X)";
  }
  const myFlags = tile.flags ?? [];
  if (myFlags.includes("MINED")) {
    return "Мина на грядке — кликни, чтобы открыть сапёр";
  }
  if (tile.zone_type === "ANIMAL") {
    const occ = tile.occupant_type ?? "EMPTY";
    if (occ === "EMPTY" || !occ) {
      return "Пустой загон · купи животное (C) или перетащи с панели";
    }
    const name = animalLabel(tile.occupant_id);
    const hunger = tile.hunger_ticks ?? 0;
    if (hunger >= ANIMAL_PRODUCTION_HUNGER_TICKS) {
      return `${name} · голодна — покорми (W)`;
    }
    if (hunger >= ANIMAL_HUNGER_WARN_TICKS) {
      return `${name} · пора кормить (W)`;
    }
    const prodElapsed = tile.production_elapsed_sec ?? 0;
    const prodNeeded = tile.production_interval_sec ?? 0;
    if (prodNeeded > 0) {
      const pct = Math.min(100, Math.floor((prodElapsed * 100) / prodNeeded));
      const yieldNoun = animalYieldNoun(tile.occupant_id, cat);
      return `${name} · ${yieldNoun} ${pct}% · уход (W)`;
    }
    return `${name} · уход (W)`;
  }
  const occ = tile.occupant_type ?? "EMPTY";
  const water = tile.water_level;
  if (occ === "EMPTY" || !occ) {
    return `Пустая грядка · посадить: ${seedLabelFromPlantId(selectedPlantId, cat)} (T)`;
  }
  const name = cropLabel(tile.occupant_id);
  const pct = growthPercent(tile);
  const ripe = isRipeTile(tile);
  if (ripe) {
    if (!canHarvestPlant(tile)) {
      return `${name} · созрело, но мало воды — сначала полей (W), потом (H)`;
    }
    return `${name} · СОЗРЕЛО — собери урожай (H)`;
  }
  if (water != null && water < WATER_LOW_THRESHOLD) {
    return `${name} · рост ${pct}% · нужен полив (W)`;
  }
  if (pct >= 72) {
    return `${name} · почти созрело (${pct}%)`;
  }
  if (pct > 0) {
    return `${name} · рост ${pct}%`;
  }
  return `На грядке: ${name} · только посажено`;
}
