"""
HTTP client for server API. Uses GAME_CONTRACTS_V1 message shapes only.

Does not modify server — talks to existing endpoints from server/http_api.py.
"""

import json
import os
import time
import urllib.error
import urllib.request

DEFAULT_HOST = os.environ.get("FARM_WARS_SERVER_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.environ.get("FARM_WARS_SERVER_PORT", "8765"))
DEFAULT_BASE = os.environ.get(
    "FARM_WARS_SERVER",
    f"http://{DEFAULT_HOST}:{DEFAULT_PORT}",
)


def parse_server_address(host_text: str, port_text: str = "8765") -> str:
    """
    Build server base URL from lobby fields.

    Accepts:
    - full URL: http://192.168.0.5:8765
    - host:port in host field: 192.168.0.5:8765
    - host + separate port field
    """
    host_text = (host_text or "").strip()
    port_text = (port_text or "").strip() or "8765"

    if not host_text:
        host_text = DEFAULT_HOST

    if host_text.startswith("http://") or host_text.startswith("https://"):
        return host_text.rstrip("/")

    if ":" in host_text:
        host_part, maybe_port = host_text.rsplit(":", 1)
        if maybe_port.isdigit():
            return f"http://{host_part}:{maybe_port}"

    port = int(port_text)
    return f"http://{host_text}:{port}"


class ServerError(Exception):
    def __init__(self, error_code: str, message: str, status: int = 0):
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.status = status


class ServerClient:
    def __init__(self, base_url: str | None = None, timeout_sec: float = 5.0):
        self.base_url = (base_url or DEFAULT_BASE).rstrip("/")
        self.timeout_sec = timeout_sec

    def health(self) -> dict:
        return self._get("/api/health")

    def create_match(self, player_name: str | None = None) -> dict:
        body = {}
        if player_name:
            body["player_name"] = player_name
        return self._post("/api/matches/create", body)

    def join_match(self, join_code: str, player_name: str) -> dict:
        return self._post("/api/matches/join", {
            "contract_version": "v1",
            "join_code": join_code,
            "player_name": player_name,
        })

    def start_match(self, match_id: str) -> dict:
        return self._post("/api/matches/start", {
            "contract_version": "v1",
            "match_id": match_id,
        })

    def submit_action(self, match_id: str, player_id: str, action: dict) -> dict:
        return self._post("/api/matches/action", {
            "contract_version": "v1",
            "match_id": match_id,
            "player_id": player_id,
            "action": action,
        })

    def poll_sync(self, match_id: str, since_tick: int = 0) -> dict:
        return self._get(f"/api/matches/{match_id}/sync", {"since_tick": str(since_tick)})

    def make_action(self, player_id: str, action_type: str, payload: dict) -> dict:
        return {
            "contract_version": "v1",
            "player_id": player_id,
            "action_type": action_type,
            "payload": payload,
            "client_ts": int(time.time() * 1000),
        }

    def _post(self, path: str, body: dict) -> dict:
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        return self._request(req)

    def _get(self, path: str, query: dict | None = None) -> dict:
        url = f"{self.base_url}{path}"
        if query:
            qs = "&".join(f"{k}={v}" for k, v in query.items())
            url = f"{url}?{qs}"
        req = urllib.request.Request(url, method="GET")
        return self._request(req)

    def _request(self, req: urllib.request.Request) -> dict:
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            payload = {}
            try:
                payload = json.loads(exc.read().decode("utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
            code = payload.get("error_code", "HTTP_ERROR")
            msg = payload.get("message", str(exc))
            raise ServerError(code, msg, exc.code) from exc
        except urllib.error.URLError as exc:
            raise ServerError("NETWORK_ERROR", str(exc.reason)) from exc
