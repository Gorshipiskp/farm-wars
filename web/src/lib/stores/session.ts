import { writable } from "svelte/store";
import type { GameCatalog } from "$lib/api/types";

export type AppScreen = "lobby" | "match";

export const screen = writable<AppScreen>("lobby");

export const serverHost = writable("127.0.0.1");
export const serverPort = writable("8765");
export const serverConnected = writable(false);

export const playerName = writable("Фермер");
export const joinCode = writable("");

export const matchId = writable("");
export const playerId = writable("");
export const isHost = writable(false);
export const myJoinCode = writable("");

export const catalog = writable<GameCatalog | null>(null);
export const statusMessage = writable("Подключись к серверу");
