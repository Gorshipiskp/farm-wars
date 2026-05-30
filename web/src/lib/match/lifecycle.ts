import { get } from "svelte/store";
import { api } from "$lib/api/client";
import type { SyncResponse } from "$lib/api/types";
import { resetEventFeed } from "$lib/game/events";
import { plantIds } from "$lib/game/catalogData";
import { applySync, discardLiveState } from "$lib/sync/applySync";
import { startSyncPoller, stopSyncPoller } from "$lib/sync/poller";
import { selectedTileId, syncEnabled } from "$lib/stores/game";
import { awaitingMatchStart } from "$lib/stores/lobby";
import { selectedPlantId, viewOpponentId } from "$lib/stores/matchUi";
import { catalog, screen, statusMessage } from "$lib/stores/session";
import { pushToast } from "$lib/stores/toasts";

async function refreshCatalogFromServer(): Promise<void> {
  try {
    const health = await api.health();
    if (health.catalog) catalog.set(health.catalog);
  } catch {
    /* keep lobby catalog */
  }
}

export async function enterMatch(initial?: SyncResponse): Promise<void> {
  await refreshCatalogFromServer();
  awaitingMatchStart.set(false);
  resetEventFeed();
  syncEnabled.set(true);
  if (initial) applySync(initial);
  screen.set("match");
  startSyncPoller();
  selectedTileId.set(null);
  viewOpponentId.set(null);
  const plants = plantIds(get(catalog));
  if (plants.length) selectedPlantId.set(plants[0]);
  statusMessage.set("Удачной фермы!");
  pushToast("Матч начался — удачи!", "ok");
}

export function leaveMatch(): void {
  stopSyncPoller();
  discardLiveState();
  awaitingMatchStart.set(false);
  selectedTileId.set(null);
  viewOpponentId.set(null);
  screen.set("lobby");
  statusMessage.set("Вышел в меню");
  pushToast("Вышел в меню", "info");
}

export async function hostStartMatch(matchIdVal: string): Promise<void> {
  await api.startMatch(matchIdVal);
  const sync = await api.pollSync(matchIdVal, 0);
  await enterMatch(sync);
}
