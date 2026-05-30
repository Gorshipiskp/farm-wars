import { ApiError } from "./errors";
import type {
  ActionEnvelope,
  ActionSubmitResponse,
  CreateMatchResponse,
  HealthResponse,
  JoinMatchResponse,
  PlayerAction,
  RosterResponse,
  SyncResponse,
} from "./types";

/** Empty = same origin; Vite dev proxies /api to :8765 */
function defaultBase(): string {
  const env = import.meta.env.VITE_API_BASE?.trim();
  if (env) return env.replace(/\/$/, "");
  return "";
}

export function parseServerBase(host: string, port: string): string {
  const h = (host || "127.0.0.1").trim();
  const p = (port || "8765").trim();
  if (h.startsWith("http://") || h.startsWith("https://")) {
    return h.replace(/\/$/, "");
  }
  if (h.includes(":")) {
    const [hostPart, maybePort] = h.split(":");
    if (/^\d+$/.test(maybePort)) {
      return `http://${hostPart}:${maybePort}`;
    }
  }
  return `http://${h}:${p}`;
}

export class GameApi {
  constructor(private baseUrl = defaultBase()) {}

  setBaseUrl(url: string) {
    this.baseUrl = url.replace(/\/$/, "");
  }

  async health(): Promise<HealthResponse> {
    return this.get<HealthResponse>("/api/health");
  }

  async createMatch(playerName?: string): Promise<CreateMatchResponse> {
    const body: Record<string, string> = {};
    if (playerName) body.player_name = playerName;
    return this.post("/api/matches/create", body);
  }

  async joinMatch(joinCode: string, playerName: string): Promise<JoinMatchResponse> {
    return this.post("/api/matches/join", {
      contract_version: "v1",
      join_code: joinCode,
      player_name: playerName,
    });
  }

  async startMatch(matchId: string): Promise<{ status: string }> {
    return this.post("/api/matches/start", {
      contract_version: "v1",
      match_id: matchId,
    });
  }

  async submitAction(
    matchId: string,
    playerId: string,
    action: PlayerAction,
  ): Promise<ActionSubmitResponse> {
    const envelope: ActionEnvelope = {
      contract_version: "v1",
      match_id: matchId,
      player_id: playerId,
      action,
    };
    return this.post<ActionSubmitResponse>("/api/matches/action", envelope);
  }

  async pollSync(matchId: string, sinceTick = 0): Promise<SyncResponse> {
    return this.get<SyncResponse>(
      `/api/matches/${encodeURIComponent(matchId)}/sync`,
      { since_tick: String(sinceTick) },
    );
  }

  async pollRoster(matchId: string): Promise<RosterResponse> {
    return this.get<RosterResponse>(
      `/api/matches/${encodeURIComponent(matchId)}/roster`,
    );
  }

  makeAction(
    playerId: string,
    actionType: string,
    payload: Record<string, unknown>,
  ): PlayerAction {
    return {
      contract_version: "v1",
      player_id: playerId,
      action_type: actionType,
      payload,
      client_ts: Date.now(),
    };
  }

  private url(path: string, query?: Record<string, string>): string {
    const base = this.baseUrl;
    const full = `${base}${path}`;
    if (!query) return full;
    const qs = new URLSearchParams(query).toString();
    return `${full}?${qs}`;
  }

  private async get<T>(path: string, query?: Record<string, string>): Promise<T> {
    const res = await fetch(this.url(path, query));
    return this.parse<T>(res);
  }

  private async post<T>(path: string, body: unknown): Promise<T> {
    const res = await fetch(this.url(path), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return this.parse<T>(res);
  }

  private async parse<T>(res: Response): Promise<T> {
    const data = (await res.json()) as Record<string, unknown>;
    if (!res.ok) {
      throw new ApiError(
        String(data.error_code ?? "HTTP_ERROR"),
        String(data.message ?? res.statusText),
        res.status,
      );
    }
    return data as T;
  }
}

export const api = new GameApi();
