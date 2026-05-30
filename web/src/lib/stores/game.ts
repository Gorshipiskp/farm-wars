import { writable } from "svelte/store";
import type { GameEvent, WorldState } from "$lib/api/types";

export const worldState = writable<WorldState | null>(null);
export const lastTick = writable(0);
export const lastEvents = writable<GameEvent[]>([]);
export const matchFinished = writable(false);
export const syncEnabled = writable(false);

export const selectedTileId = writable<string | null>(null);
