export const FARM_COLS = 4;
export const FARM_PEN_COLS = 4;
export const FARM_PLANT_SLOTS = 12;
export const FARM_ANIMAL_SLOTS = 8;
export const FARM_TILE_COUNT = FARM_PLANT_SLOTS + FARM_ANIMAL_SLOTS;

/** Chebyshev radius on the plant grid when dropping the watering can. */
export const WATERING_CAN_RADIUS = 1;

export const LOBBY_POLL_MS = 350;
/** Interval for /api/health while on the lobby screen. */
export const LOBBY_HEALTH_POLL_MS = 4000;
/** Background reconcile while in match (action responses carry sync too). */
export const SYNC_POLL_MS = 120;
