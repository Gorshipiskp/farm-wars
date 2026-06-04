const STORAGE_KEY = "farm_wars.server";

const DEFAULT_HOST = "127.0.0.1";
const DEFAULT_PORT = "8765";

export type SavedServerConnection = {
  host: string;
  port: string;
};

export function loadServerConnection(): SavedServerConnection {
  if (typeof localStorage === "undefined") {
    return { host: DEFAULT_HOST, port: DEFAULT_PORT };
  }
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return { host: DEFAULT_HOST, port: DEFAULT_PORT };
    }
    const data = JSON.parse(raw) as Partial<SavedServerConnection>;
    const host = String(data.host ?? "").trim() || DEFAULT_HOST;
    const port = String(data.port ?? "").trim() || DEFAULT_PORT;
    return { host, port };
  } catch {
    return { host: DEFAULT_HOST, port: DEFAULT_PORT };
  }
}

export function saveServerConnection(host: string, port: string): void {
  if (typeof localStorage === "undefined") {
    return;
  }
  const payload: SavedServerConnection = {
    host: host.trim() || DEFAULT_HOST,
    port: port.trim() || DEFAULT_PORT,
  };
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  } catch {
    /* private mode / quota */
  }
}
