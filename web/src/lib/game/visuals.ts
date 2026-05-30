import type { TileState } from "$lib/api/types";
import {
  ANIMAL_HUNGER_WARN_TICKS,
  ANIMAL_PRODUCTION_HUNGER_TICKS,
  WATER_CRITICAL_THRESHOLD,
  WATER_LOW_THRESHOLD,
} from "$lib/game/pacing";

export type CareUrgency = "ok" | "low" | "critical";

/** Цвета культур (как в client/ui.py PRODUCT_COLORS). */
export const PRODUCT_COLORS: Record<string, string> = {
  wheat: "#e6c85a",
  corn: "#f0d246",
  potato: "#d2aa78",
  tomato: "#dc463c",
  carrot: "#e68c32",
  sunflower: "#ffdc32",
  flour: "#f5f0dc",
  bread: "#d29650",
  cake: "#ffb4c8",
  cheese: "#ffeb78",
  butter: "#fff5b4",
  sausage: "#b45a46",
  pie: "#c87850",
  soup: "#c8643c",
  omelette: "#ffe696",
  milk: "#f0f8ff",
  egg: "#fffae6",
  wool: "#c8c8d2",
  pork: "#dcaaa0",
  feed: "#a0825a",
};

const PLANT_EMOJI: Record<string, string> = {
  wheat: "🌾",
  corn: "🌽",
  potato: "🥔",
  tomato: "🍅",
  carrot: "🥕",
  sunflower: "🌻",
};

const ANIMAL_EMOJI: Record<string, string> = {
  cow: "🐄",
  chicken: "🐔",
  sheep: "🐑",
  pig: "🐷",
};

const PRODUCT_EMOJI: Record<string, string> = {
  wheat: "🌾",
  corn: "🌽",
  potato: "🥔",
  tomato: "🍅",
  carrot: "🥕",
  sunflower: "🌻",
  milk: "🥛",
  egg: "🥚",
  wool: "🧶",
  pork: "🥓",
  flour: "🌾",
  bread: "🍞",
  cake: "🎂",
  cheese: "🧀",
  butter: "🧈",
  feed: "🌿",
};

export function normalizePlantId(occupantId: string | null | undefined): string {
  if (!occupantId) return "wheat";
  for (const pid of Object.keys(PLANT_EMOJI)) {
    if (occupantId === pid || occupantId.includes(pid)) return pid;
  }
  return occupantId;
}

export function plantEmoji(plantId: string | null | undefined): string {
  const key = normalizePlantId(plantId);
  return PLANT_EMOJI[key] ?? "🌱";
}

export function animalEmoji(animalId: string | null | undefined): string {
  if (!animalId) return "🐾";
  return ANIMAL_EMOJI[animalId] ?? "🐾";
}

export function productEmoji(productId: string): string {
  return PRODUCT_EMOJI[productId] ?? "📦";
}

export interface TileVisual {
  emoji: string;
  accent: string;
  subtitle: string;
}

export function tileVisual(tile: TileState, own: boolean): TileVisual {
  const empty = !tile.occupant_type || tile.occupant_type === "EMPTY";
  const animal = tile.zone_type === "ANIMAL";

  if (empty) {
    if (animal) {
      return {
        emoji: "🪵",
        accent: own ? "#b8a888" : "#907868",
        subtitle: "загон",
      };
    }
    return {
      emoji: "🟫",
      accent: own ? "#d4bc8a" : "#907868",
      subtitle: "пусто",
    };
  }

  if (animal) {
    const aid = tile.occupant_id ?? "cow";
    return {
      emoji: animalEmoji(aid),
      accent: own ? "#9a8b6e" : "#a08070",
      subtitle: aid,
    };
  }

  const plantKey = normalizePlantId(tile.occupant_id);
  return {
    emoji: plantEmoji(plantKey),
    accent: PRODUCT_COLORS[plantKey] ?? (own ? "#8fbc6a" : "#a08070"),
    subtitle: plantKey,
  };
}

export function growthRatio(tile: TileState): number {
  const needed = tile.growth_time_sec ?? 0;
  if (needed <= 0) return 0;
  return Math.min(1, (tile.growth_elapsed_sec ?? 0) / needed);
}

export function productionRatio(tile: TileState): number {
  const hunger = tile.hunger_ticks ?? 0;
  if (hunger >= ANIMAL_PRODUCTION_HUNGER_TICKS) return 0;
  const needed = tile.production_interval_sec ?? 0;
  if (needed <= 0) return 0;
  return Math.min(1, (tile.production_elapsed_sec ?? 0) / needed);
}

export function isRipeTile(tile: TileState): boolean {
  const needed = tile.growth_time_sec ?? 0;
  return needed > 0 && (tile.growth_elapsed_sec ?? 0) >= needed;
}

/** 0–100 for plant tiles. */
export function growthPercent(tile: TileState): number {
  if (!plantHasCrop(tile)) return 0;
  return Math.min(100, Math.floor(growthRatio(tile) * 100));
}

export type PlantMaturity = "none" | "growing" | "almost" | "ripe";

const ALMOST_RIPE_RATIO = 0.72;

export function plantMaturity(tile: TileState): PlantMaturity {
  if (!plantHasCrop(tile)) return "none";
  if (isRipeTile(tile)) return "ripe";
  if (growthRatio(tile) >= ALMOST_RIPE_RATIO) return "almost";
  return "growing";
}

export function plantMaturityLabel(tile: TileState): string {
  const pct = growthPercent(tile);
  switch (plantMaturity(tile)) {
    case "ripe":
      return "Созрело — собери (H)";
    case "almost":
      return `Почти созрело (${pct}%)`;
    case "growing":
      return `Рост ${pct}%`;
    default:
      return "";
  }
}

/** Harvest allowed when ripe and water is sufficient (server gate). */
export function canHarvestPlant(tile: TileState): boolean {
  if (!isRipeTile(tile)) return false;
  const w = tile.water_level;
  if (w == null) return true;
  return w >= WATER_LOW_THRESHOLD;
}

export function plantHasCrop(tile: TileState): boolean {
  return (
    tile.zone_type !== "ANIMAL" &&
    !!tile.occupant_type &&
    tile.occupant_type !== "EMPTY"
  );
}

export function animalHasOccupant(tile: TileState): boolean {
  return (
    tile.zone_type === "ANIMAL" &&
    !!tile.occupant_type &&
    tile.occupant_type !== "EMPTY"
  );
}

export function waterLevelRatio(tile: TileState): number {
  const w = tile.water_level;
  if (w == null) return 1;
  return Math.max(0, Math.min(1, w / 100));
}

export function plantWaterUrgency(tile: TileState): CareUrgency | null {
  if (!plantHasCrop(tile)) return null;
  const w = tile.water_level;
  if (w == null) return null;
  if (w < WATER_CRITICAL_THRESHOLD) return "critical";
  if (w < WATER_LOW_THRESHOLD) return "low";
  return "ok";
}

export function animalFeedUrgency(tile: TileState): CareUrgency | null {
  if (!animalHasOccupant(tile)) return null;
  const hunger = tile.hunger_ticks ?? 0;
  if (hunger >= ANIMAL_PRODUCTION_HUNGER_TICKS) return "critical";
  if (hunger >= ANIMAL_HUNGER_WARN_TICKS) return "low";
  return "ok";
}

/** 0 = только покормлено, 1 = голод (порог производства). */
export function animalHungerRatio(tile: TileState): number {
  const hunger = tile.hunger_ticks ?? 0;
  return Math.min(1, hunger / ANIMAL_PRODUCTION_HUNGER_TICKS);
}
