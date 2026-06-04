"""
HTTP API multiplayer tests (stdlib, in-process server on ephemeral port).

Run from repo root:
    py tools/init_db.py --seed
    py tools/test_multiplayer_http.py
"""

from __future__ import annotations

import json
import os
import sys
import threading
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from server.game_server import GameServer
from server.http_api import serve


def _post(base: str, path: str, body: dict) -> tuple[int, dict]:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{base}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        payload = json.loads(exc.read().decode("utf-8"))
        return exc.code, payload


def _get(base: str, path: str) -> tuple[int, dict]:
    with urllib.request.urlopen(f"{base}{path}", timeout=5) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def test_http_three_player_flow():
    print("\n--- MP HTTP: create, 2 joins, start, sync, action ---")
    game = GameServer()
    httpd = serve(game, host="127.0.0.1", port=0)
    port = httpd.server_address[1]
    base = f"http://127.0.0.1:{port}"
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    try:
        status, created = _post(base, "/api/matches/create", {"player_name": "Host"})
        assert status == 200
        mid = created["match_id"]
        code = created["join_code"]

        for name in ("Alice", "Bob"):
            status, joined = _post(base, "/api/matches/join", {
                "join_code": code,
                "player_name": name,
            })
            assert status == 200
            assert joined["match_id"] == mid

        status, roster = _get(base, f"/api/matches/{mid}/roster")
        assert status == 200
        assert len(roster["players"]) == 3

        status, started = _post(base, "/api/matches/start", {"match_id": mid})
        assert status == 200
        assert started["status"] == "RUNNING"
        assert started["player_count"] == 3

        status, sync = _get(base, f"/api/matches/{mid}/sync?since_tick=0")
        assert status == 200
        assert len(sync["world_state"]["players"]) == 3

        status, action_result = _post(base, "/api/matches/action", {
            "match_id": mid,
            "player_id": "p2",
            "action": {
                "contract_version": "v1",
                "player_id": "p2",
                "action_type": "BUY_PRODUCT",
                "payload": {"product_id": "wheat_seed", "amount": 1},
                "client_ts": 0,
            },
        })
        assert status == 200
        assert action_result["accepted"] is True
        p2 = next(
            p for p in action_result["sync"]["world_state"]["players"]
            if p["player_id"] == "p2"
        )
        wheat = next(i for i in p2["inventory"] if i["product_id"] == "wheat_seed")
        assert wheat["amount"] >= 1

        status, err_body = _post(base, "/api/matches/join", {
            "join_code": code,
            "player_name": "Late",
        })
        assert status == 400
        assert err_body.get("error_code") == "INVALID_REQUEST"
        print("  [OK] full HTTP MP flow")
    finally:
        httpd.shutdown()
        thread.join(timeout=2.0)


def test_http_invalid_join_code():
    print("\n--- MP HTTP: bad join code -> 404 ---")
    game = GameServer()
    httpd = serve(game, host="127.0.0.1", port=0)
    port = httpd.server_address[1]
    base = f"http://127.0.0.1:{port}"
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        status, body = _post(base, "/api/matches/join", {
            "join_code": "ZZZZZZ",
            "player_name": "Ghost",
        })
        assert status == 404
        assert body.get("error_code") == "INVALID_JOIN_CODE"
        print("  [OK] INVALID_JOIN_CODE via HTTP")
    finally:
        httpd.shutdown()
        thread.join(timeout=2.0)


def main() -> int:
    print("=" * 60)
    print("MULTIPLAYER HTTP TESTS")
    print("=" * 60)
    if not os.path.isfile(os.path.join(ROOT, "db", "farm_wars.db")):
        print("Run: py tools/init_db.py --seed", file=sys.stderr)
        return 1

    test_http_three_player_flow()
    test_http_invalid_join_code()
    print("\n" + "=" * 60)
    print("ALL MULTIPLAYER HTTP CHECKS PASSED")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
