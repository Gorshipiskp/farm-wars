import { get } from "svelte/store";
import { SYNC_POLL_MS } from "$lib/game/constants";
import { requestSync } from "$lib/sync/requestSync";
import { syncEnabled } from "$lib/stores/game";
import { matchId } from "$lib/stores/session";

let timer: ReturnType<typeof setInterval> | null = null;

export function startSyncPoller(): void {
  stopSyncPoller();
  syncEnabled.set(true);
  void tick();
  timer = setInterval(() => void tick(), SYNC_POLL_MS);
}

export function stopSyncPoller(): void {
  if (timer) {
    clearInterval(timer);
    timer = null;
  }
}

async function tick(): Promise<void> {
  if (!get(matchId) || !get(syncEnabled)) return;
  await requestSync();
}
