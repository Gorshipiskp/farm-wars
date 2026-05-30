import { writable } from "svelte/store";

/** Guest waits for host start; host waits on roster until «Начать». */
export const awaitingMatchStart = writable(false);
