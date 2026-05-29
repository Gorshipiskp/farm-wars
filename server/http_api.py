"""JSON HTTP API for match create/join/action/sync (stdlib only)."""

import json
import logging
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlparse

if TYPE_CHECKING:
    from server.game_server import GameServer

log = logging.getLogger("farm_wars.server.http")

MATCH_ID_RE = re.compile(r"^/api/matches/([a-zA-Z0-9-]+)(/.*)?$")


class FarmWarsHandler(BaseHTTPRequestHandler):
    game_server: "GameServer"

    def log_message(self, format, *args):
        log.debug("%s - %s", self.address_string(), format % args)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._json_error(400, "INVALID_JSON", "Request body must be JSON")
            return

        path = urlparse(self.path).path

        try:
            if path == "/api/matches/create":
                host_name = data.get("player_name") or data.get("host_name")
                result = self.game_server.create_match(host_name)
                self._json_response(200, result)
                return

            if path == "/api/matches/join":
                join_code = data.get("join_code", "")
                player_name = data.get("player_name", "")
                if not join_code or not player_name:
                    self._json_error(400, "MISSING_FIELD", "join_code and player_name required")
                    return
                result = self.game_server.join_match(join_code, player_name)
                self._json_response(200, result)
                return

            if path == "/api/matches/start":
                match_id = data.get("match_id")
                if not match_id:
                    self._json_error(400, "MISSING_FIELD", "match_id required")
                    return
                result = self.game_server.start_match(match_id)
                self._json_response(200, result)
                return

            if path == "/api/matches/action":
                for key in ("match_id", "player_id", "action"):
                    if key not in data:
                        self._json_error(400, "MISSING_FIELD", f"{key} required")
                        return
                action = data.get("action", {})
                log.info(
                    "POST /action match=%s player=%s type=%s",
                    data.get("match_id"),
                    data.get("player_id"),
                    action.get("action_type"),
                )
                result = self.game_server.submit_action(data)
                self._json_response(200, result)
                return

            self._json_error(404, "NOT_FOUND", f"Unknown path: {path}")
        except KeyError as exc:
            code = str(exc.args[0]) if exc.args else "NOT_FOUND"
            status = 404 if code in ("INVALID_JOIN_CODE", "UNKNOWN_MATCH") else 400
            self._json_error(status, code, code.replace("_", " ").lower())
        except ValueError as exc:
            self._json_error(400, "INVALID_REQUEST", str(exc))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        m = MATCH_ID_RE.match(path)
        if m and m.group(2) == "/roster":
            match_id = m.group(1)
            try:
                self._json_response(200, self.game_server.get_roster(match_id))
            except KeyError:
                self._json_error(404, "UNKNOWN_MATCH", "Match not found")
            return

        if m and (m.group(2) in ("/sync", "/state", None)):
            match_id = m.group(1)
            since_tick = int(query.get("since_tick", ["0"])[0])
            try:
                sync = self.game_server.get_sync(match_id, since_tick)
                if sync is None:
                    self._json_error(404, "NO_SYNC", "No state available yet")
                    return
                self._json_response(200, sync)
            except KeyError:
                self._json_error(404, "UNKNOWN_MATCH", "Match not found")
            return

        if path == "/api/health":
            from server.catalog_api import catalog_for_client
            from server.match import SHOP_HANDLER_VERSION

            self._json_response(200, {
                "contract_version": "v1",
                "status": "ok",
                "engine": self.game_server.engine_name,
                "shop_handler": SHOP_HANDLER_VERSION,
                "catalog": catalog_for_client(self.game_server.catalog),
            })
            return

        self._json_error(404, "NOT_FOUND", f"Unknown path: {path}")

    def _json_response(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json_error(self, status: int, error_code: str, message: str) -> None:
        self._json_response(status, {
            "contract_version": "v1",
            "error_code": error_code,
            "message": message,
            "field_path": None,
        })


def serve(game_server: "GameServer", host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    handler = FarmWarsHandler
    handler.game_server = game_server
    httpd = ThreadingHTTPServer((host, port), handler)
    log.info("HTTP API listening on http://%s:%s", host, port)
    return httpd
