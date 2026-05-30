/** Must match server default `FARM_WARS_TICKS_PER_SEC` (see shared/game_pacing.py). */
export const TICKS_PER_SECOND = 2;

/** Must match `shared.game_pacing.ANIMAL_PRODUCTION_HUNGER_TICKS`. */
export const ANIMAL_PRODUCTION_HUNGER_TICKS = 40;

/** UI warning before production stops (~15 s at 2 t/s). */
export const ANIMAL_HUNGER_WARN_TICKS = 30;

/** Plant tiles below this show a dry-soil warning. */
export const WATER_LOW_THRESHOLD = 50;

export const WATER_CRITICAL_THRESHOLD = 25;

/** Simulation ticks → approximate wall-clock seconds for UI. */
export function realSecondsForTicks(ticks: number): number {
  return ticks / TICKS_PER_SECOND;
}

/** Wall-clock seconds from catalog `production_time_sec` (same as server enricher input). */
export function ticksForRealSeconds(seconds: number): number {
  return Math.max(1, Math.floor(seconds * TICKS_PER_SECOND));
}

/** Human-readable duration for recipe/factory UI (Russian). */
export function formatDurationRu(seconds: number): string {
  const s = Math.max(1, Math.ceil(seconds));
  if (s < 60) return `${s} с`;
  const m = Math.floor(s / 60);
  const rest = s % 60;
  if (rest === 0) return `${m} мин`;
  return `${m} мин ${rest} с`;
}
