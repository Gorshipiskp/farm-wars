import type { SyncResponse } from "$lib/api/types";
import { feedToasts, resetEventFeed } from "$lib/game/events";
import {
  lastEvents,
  lastTick,
  matchFinished,
  syncEnabled,
  worldState,
} from "$lib/stores/game";
import { get } from "svelte/store";
import { playerId } from "$lib/stores/session";
import { pushToast } from "$lib/stores/toasts";

export function applySync(sync: SyncResponse): void {
  if (!get(syncEnabled)) return;
  if (sync.world_state) {
    worldState.set(sync.world_state);
  }
  lastTick.set(sync.tick_id ?? sync.world_state?.tick_id ?? 0);
  const events = sync.events ?? [];
  lastEvents.set(events);
  for (const ev of events) {
    if (ev.event_type === "MATCH_FINISHED") {
      matchFinished.set(true);
    }
  }
  const pid = get(playerId);
  if (pid) {
    feedToasts(events, pid, pushToast);
  }
}

export function discardLiveState(): void {
  worldState.set(null);
  lastTick.set(0);
  lastEvents.set([]);
  matchFinished.set(false);
  syncEnabled.set(false);
  resetEventFeed();
}
