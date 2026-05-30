import { get } from "svelte/store";
import { api } from "$lib/api/client";
import { ApiError } from "$lib/api/errors";
import { applySync } from "$lib/sync/applySync";
import { lastTick, syncEnabled } from "$lib/stores/game";
import { matchId, statusMessage } from "$lib/stores/session";

/** Pull latest state from server (e.g. after action or on error). */
export async function requestSync(): Promise<boolean> {
  const mid = get(matchId);
  if (!mid || !get(syncEnabled)) return false;
  try {
    const sync = await api.pollSync(mid, get(lastTick));
    if (sync) applySync(sync);
    return true;
  } catch (e) {
    if (e instanceof ApiError) {
      statusMessage.set(`${e.code}: ${e.message}`);
    }
    return false;
  }
}
