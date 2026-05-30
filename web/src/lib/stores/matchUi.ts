import { writable } from "svelte/store";

/** plant_id для посадки (как в pygame). */
export const selectedPlantId = writable("wheat");
export const selectedSellProductId = writable<string | null>(null);
export const selectedRecipeId = writable("bread");
export const selectedAnimalId = writable("cow");
export const viewOpponentId = writable<string | null>(null);
